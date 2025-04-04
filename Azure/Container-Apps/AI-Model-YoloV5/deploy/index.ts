import * as pulumi from "@pulumi/pulumi";
import * as docker from "@pulumi/docker";

import * as containerregistry from "@pulumi/azure-native/containerregistry";
import * as operationalinsights from "@pulumi/azure-native/operationalinsights";
import * as resources from "@pulumi/azure-native/resources";
import * as web from "@pulumi/azure-native/web/v20210301";

// az account list-locations --output table
const glbLocation = "northeurope";

const resourceGroup = new resources.ResourceGroup("rg");

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
  }
});

export const url = pulumi.interpolate`https://${containerApp.configuration.apply(c => c?.ingress?.fqdn)}`;