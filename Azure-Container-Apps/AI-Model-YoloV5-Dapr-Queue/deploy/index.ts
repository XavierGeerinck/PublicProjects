import * as pulumi from "@pulumi/pulumi";
import * as docker from "@pulumi/docker";

import * as containerregistry from "@pulumi/azure-native/containerregistry";
import * as operationalinsights from "@pulumi/azure-native/operationalinsights";
import * as resources from "@pulumi/azure-native/resources";
import * as web from "@pulumi/azure-native/web/v20210301";
import * as sb from "@pulumi/azure-native/servicebus";

// az account list-locations --output table
const glbLocation = "northeurope";
const glbProjectName = "demo"
const glbProjectEnvironment = "tmp"; // prd, stg, dev, tst, tmp, ...

const resourceGroup = new resources.ResourceGroup(`rg-${glbProjectName}-${glbProjectEnvironment}-`, {
  location: glbLocation
});

const serviceBusNamespace = new sb.Namespace("sbn", {
  resourceGroupName: resourceGroup.name,
  location: glbLocation,
  sku: {
    name: "Standard"
  }
});

const serviceBusQueue = new sb.Queue("sbq-items", {
  resourceGroupName: resourceGroup.name,
  namespaceName: serviceBusNamespace.name,

  lockDuration: 'PT5M',
  maxSizeInMegabytes: 1024,
  requiresDuplicateDetection: false,
  requiresSession: false,
  defaultMessageTimeToLive: 'P1DT0H0M0.0S',
  deadLetteringOnMessageExpiration: false,
  duplicateDetectionHistoryTimeWindow: 'PT10M',
  maxDeliveryCount: 4,
  autoDeleteOnIdle: 'P1DT0H0M0.0S',
  enablePartitioning: false,
  enableExpress: false
});

const serviceBusQueueAuthorizationRule = new sb.QueueAuthorizationRule("main-key", {
  resourceGroupName: resourceGroup.name,
  namespaceName: serviceBusNamespace.name,
  queueName: serviceBusQueue.name,
  rights: [
    "Listen",
    "Manage",
    "Send"
  ]
});

const serviceBusQueueKeys = sb.listQueueKeysOutput({
  resourceGroupName: resourceGroup.name,
  namespaceName: serviceBusNamespace.name,
  queueName: serviceBusQueue.name,
  authorizationRuleName: serviceBusQueueAuthorizationRule.name
})

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

const kubeEnv = new web.KubeEnvironment("cae", {
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

const registry = new containerregistry.Registry("acr", {
  resourceGroupName: resourceGroup.name,
  sku: {
    name: "Basic",
  },
  adminUserEnabled: true,
});

const credentials = containerregistry.listRegistryCredentialsOutput({
  resourceGroupName: resourceGroup.name,
  registryName: registry.name,
});
const adminUsername = credentials.apply(credentials => credentials.username!);
const adminPassword = credentials.apply(credentials => credentials.passwords![0].value!);

const customImage = "app";
const myImage = new docker.Image(customImage, {
  imageName: pulumi.interpolate`${registry.loginServer}/${customImage}:v1.0.0`,
  build: { context: `./${customImage}` },
  registry: {
    server: registry.loginServer,
    username: adminUsername,
    password: adminPassword,
  },
});


const containerApp = new web.ContainerApp("app", {
  resourceGroupName: resourceGroup.name,
  location: glbLocation,
  kubeEnvironmentId: kubeEnv.id,
  configuration: {
    ingress: {
      external: true,
      targetPort: 5000,
    },
    registries: [{
      server: registry.loginServer,
      username: adminUsername,
      passwordSecretRef: "pwd",
    }],
    secrets: [{
      name: "pwd",
      value: adminPassword,
    }],
  },
  template: {
    containers: [{
      name: "myapp",
      image: myImage.imageName,
    }],
    dapr: {
      enabled: true,
      appId: "ca-yolov5-demo",
      appPort: 5000,
      components: [
        {
          name: 'queue',
          type: 'bindings.azure.servicebusqueues',
          version: 'v1',
          metadata: [
            {
              name: 'connectionString',
              value: serviceBusQueueKeys.primaryConnectionString
            },
            {
              name: 'queueName',
              value: 'sbq-items'
            },
            {
              name: 'ttlInSeconds',
              value: '60'
            }
          ]
        }
      ]
    }
  }
});


export const rgName = pulumi.interpolate`${resourceGroup.name}`;
export const sbNamespace = pulumi.interpolate`${serviceBusNamespace.name}`;
export const sbQueue = pulumi.interpolate`${serviceBusQueue.name}`;
export const sbQueueAuthorizationRule = pulumi.interpolate`${serviceBusQueueAuthorizationRule.name}`;

export const url = pulumi.interpolate`https://${containerApp.configuration.apply(c => c?.ingress?.fqdn)}`;