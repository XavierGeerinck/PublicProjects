import * as pulumi from "@pulumi/pulumi";
import * as random from "@pulumi/random";
import * as docker from "@pulumi/docker";

import * as containerregistry from "@pulumi/azure-native/containerregistry";
import * as operationalinsights from "@pulumi/azure-native/operationalinsights";
import * as resources from "@pulumi/azure-native/resources";
import * as web from "@pulumi/azure-native/web/v20210301";
import * as sb from "@pulumi/azure-native/servicebus";
import { ActiveRevisionsMode } from "@pulumi/azure-native/web/v20210301";

const config = new pulumi.Config();

// az account list-locations --output table
const glbLocation = config.get("glb-location") || "northeurope";
const glbProjectName = config.get("glb-project-name") || "demo"
const glbProjectEnvironment = config.get("glb-project-env") || "tmp"; // prd, stg, dev, tst, tmp, ...

const cfgSbTopicNames = config.require("sb-topics");
const GLB_APP_ID = "ai-yolox";
const GLB_APP_PORT = 5000;

// ======================================================================
// Create the main Resource Group
// ======================================================================
const resourceGroup = new resources.ResourceGroup(`rg-${glbProjectName}-${glbProjectEnvironment}-`, {
  location: glbLocation
});

export const outRgName = pulumi.interpolate`${resourceGroup.name}`;

// ======================================================================
// Create the Queue System
// ======================================================================
const serviceBusNamespace = new sb.Namespace("sbn", {
  resourceGroupName: resourceGroup.name,
  location: glbLocation,
  sku: {
    name: "Standard"
  }
});

const serviceBusNamespaceAuthorizationRule = new sb.NamespaceAuthorizationRule("main-key", {
  resourceGroupName: resourceGroup.name,
  namespaceName: serviceBusNamespace.name,
  rights: [
    "Listen",
    "Manage",
    "Send"
  ]
});

const serviceBusNamespaceKeys = sb.listNamespaceKeysOutput({
  resourceGroupName: resourceGroup.name,
  namespaceName: serviceBusNamespace.name,
  authorizationRuleName: serviceBusNamespaceAuthorizationRule.name
});

// Create the topics for our models
// https://docs.microsoft.com/en-us/azure/templates/microsoft.servicebus/namespaces/topics?tabs=bicep
const sbTopics = cfgSbTopicNames.split(";").map(topicName => new sb.Topic(topicName, {
  resourceGroupName: resourceGroup.name,
  namespaceName: serviceBusNamespace.name,

  maxSizeInMegabytes: 1024,
  requiresDuplicateDetection: false,
  defaultMessageTimeToLive: 'P1D',
  duplicateDetectionHistoryTimeWindow: 'PT10M',
  autoDeleteOnIdle: 'P14D',
  enablePartitioning: false,
  enableExpress: false
}));

export const outSbNamespaceName = pulumi.interpolate`${serviceBusNamespace.name}`;
export const outSbNamespaceConnectionString = pulumi.interpolate`${serviceBusNamespaceKeys.primaryConnectionString}`;
export const outSbTopics = pulumi.interpolate`${cfgSbTopicNames}`;

// ======================================================================
// Container Registry Configuration
// ======================================================================
const acr = new containerregistry.Registry("acr", {
  resourceGroupName: resourceGroup.name,
  sku: {
    name: "Basic",
  },
  adminUserEnabled: true,
});

const acrCredentials = containerregistry.listRegistryCredentialsOutput({
  resourceGroupName: resourceGroup.name,
  registryName: acr.name,
});

export const outAcrName = pulumi.interpolate`${acr.name}`;
export const outAcrLoginServer = pulumi.interpolate`${acr.loginServer}`;
export const outAcrAdminUsername = acrCredentials.apply(credentials => credentials.username!);
export const outAcrAdminPassword = acrCredentials.apply(credentials => credentials.passwords![0].value!);

// ======================================================================
// App Container Configuration
// ======================================================================
const imageName = `${glbProjectName}-${glbProjectEnvironment}-${GLB_APP_ID}`;
const image = new docker.Image(imageName, {
  imageName: pulumi.interpolate`${acr.loginServer}/${imageName}:latest`,
  build: { context: `./app` },
  registry: {
    server: acr.loginServer,
    username: outAcrAdminUsername,
    password: outAcrAdminPassword
  },
});

export const outImageName = pulumi.interpolate`${image.imageName}`;

// ======================================================================
// Container App Configuration
// ======================================================================
const workspace = new operationalinsights.Workspace("law", {
  resourceGroupName: resourceGroup.name,
  sku: {
    name: "PerGB2018",
  },
  retentionInDays: 30,
});

const workspaceSharedKeys = operationalinsights.getSharedKeysOutput({
  resourceGroupName: resourceGroup.name,
  workspaceName: workspace.name,
});

const kubeEnv = new web.KubeEnvironment("env", {
  resourceGroupName: resourceGroup.name,
  location: glbLocation,
  type: "Managed",
  appLogsConfiguration: {
    destination: "log-analytics",
    logAnalyticsConfiguration: {
      customerId: workspace.customerId,
      sharedKey: workspaceSharedKeys.apply(r => r.primarySharedKey!),
    },
  },
});

const containerApp = new web.ContainerApp("app", {
  resourceGroupName: resourceGroup.name,
  location: glbLocation,
  kubeEnvironmentId: kubeEnv.id,
  configuration: {
    ingress: {
      external: true,
      targetPort: GLB_APP_PORT,
      transport: "http2"
    },
    registries: [{
      server: acr.loginServer,
      username: outAcrAdminUsername,
      passwordSecretRef: "acr-pwd",
    }],
    activeRevisionsMode: ActiveRevisionsMode.Single,
    secrets: [
      {
        name: "acr-pwd",
        value: outAcrAdminPassword,
      },
      {
        name: "sb-connection-string",
        value: serviceBusNamespaceKeys.primaryConnectionString,
      }
    ],
  },
  template: {
    revisionSuffix: `${(new Date()).getTime()}`,
    containers: [{
      name: `container-${GLB_APP_ID}`,
      image: image.imageName,
      env: [
        {
          name: "APP_ID",
          value: GLB_APP_ID
        },
        {
          name: "APP_PORT",
          value: `${GLB_APP_PORT}`
        },
        {
          name: "DAPR_PUBSUB_MODEL_NAME",
          value: "my-pubsub"
        },
        {
          name: "DAPR_PUBSUB_MODEL_TOPIC",
          value: "worker-items"
        }
      ]
    }],
    dapr: {
      enabled: true,
      appId: GLB_APP_ID,
      appPort: GLB_APP_PORT,
      // appProtocol: 'http', // Disabled for now since unsupported by ARM CLI
      components: [
        {
          name: 'my-pubsub',
          type: 'pubsub.azure.servicebus',
          version: 'v1',
          metadata: [
            {
              name: 'connectionString',
              secretRef: "sb-connection-string"
            },
            {
              name: 'ttlInSeconds',
              value: '60'
            },
            // We want the pubsub to act as a queue so we can outscale easily
            // https://docs.dapr.io/reference/components-reference/supported-pubsub/setup-azure-servicebus/
            {
              name: 'maxActiveMessages',
              value: '1'
            }
          ]
        }
      ]
    }
  }
});

export const outCaUrl = pulumi.interpolate`https://${containerApp.configuration.ingress.fqdn}`;
export const outCaRevisionSuffix = pulumi.interpolate`${containerApp.template.revisionSuffix}`;
export const outCaProvisioningState = pulumi.interpolate`${containerApp.provisioningState}`;
export const outCaLatestRevisionFqdn = pulumi.interpolate`https://${containerApp.latestRevisionFqdn}`;
export const outCaLatestRevisionName = pulumi.interpolate`${containerApp.latestRevisionName}`;