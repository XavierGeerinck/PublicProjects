import * as pulumi from "@pulumi/pulumi/index.js";
import * as random from "@pulumi/random";
import * as resources from "@pulumi/azure-native/resources/index.js";
import * as sa from "@pulumi/azure-native/storage/index.js";
import * as containerregistry from "@pulumi/azure-native/containerregistry/index.js";
import * as authorization from "@pulumi/azure-native/authorization/index.js";
import * as insights from "@pulumi/azure-native/insights/index.js";
import * as web from "@pulumi/azure-native/web/index.js";
import * as communication from "@pulumi/azure-native/communication/index.js";
import * as la from "@pulumi/azure-native/operationalinsights/index.js";
import * as acr from "@pulumi/azure-native/containerregistry/index.js";
import {
  getStorageAccountConnectionString,
  signedBlobReadUrl,
} from "./helpers.js";

const config = new pulumi.Config();

export const glbLocation = config.get("glb-location") ?? "undefined";
export const glbProjectName = config.get("glb-project-name") ?? "undefined";
export const glbProjectEnv = config.get("glb-project-env") ?? "undefined"; // prd, stg, dev, tst, tmp, ...

const clientConfig = await authorization.getClientConfig();
const subscriptionId = clientConfig.subscriptionId;

// ======================================================================
// Create the main Resource Group
// ======================================================================
const resourceGroup = new resources.ResourceGroup(
  `rg-${glbProjectName}-${glbProjectEnv}-`,
  {
    location: glbLocation,
  }
);

export const rgName = pulumi.interpolate`${resourceGroup.name}`;

// ======================================================================
// Log Analytics
// ======================================================================
const law = new la.Workspace("law-", {
  location: glbLocation,
  resourceGroupName: resourceGroup.name,
  retentionInDays: 30,
  sku: {
    name: "PerGB2018",
  },
});

// ======================================================================
// Create the Main Storage Account
// - Image Uploads
// - ...
// ======================================================================
const saMain = new sa.StorageAccount("sa-main-", {
  resourceGroupName: resourceGroup.name,
  location: glbLocation,
  accountName: pulumi.interpolate`samain${glbProjectName.replace(/-/g, '')}${glbProjectEnv}`,
  sku: {
    name: sa.SkuName.Standard_LRS,
  },
  kind: sa.Kind.StorageV2,
});

export const saMainEndpoint = saMain.primaryEndpoints.blob;
export const saMainConnectionString = getStorageAccountConnectionString(
  resourceGroup.name,
  saMain.name
);

// ======================================================================
// Create the Table Storage
// - Landing Page Emails
// ======================================================================
const saMainTableLandingPageEmails = new sa.Table("table-landing-page-emails", {
  resourceGroupName: resourceGroup.name,
  accountName: saMain.name,
  tableName: "landingpageemails",
});

export const saMainTableLandingPageEmailsName = "landingpageemails";

// ======================================================================
// Email Communication Services
// https://learn.microsoft.com/en-us/azure/templates/microsoft.communication/communicationservices?pivots=deployment-language-bicep
// ======================================================================
const csEmail = new communication.EmailService(`cs-email-`, {
  resourceGroupName: rgName,
  location: "Global",
  dataLocation: "UnitedStates", // currently only available in united states for data at rest
});

// ======================================================================
// Container Registry Configuration
// ======================================================================
const acrRegistry = new containerregistry.Registry("acr", {
  resourceGroupName: resourceGroup.name,
  sku: {
    name: "Standard",
  },
  adminUserEnabled: true,
});

const acrCredentials = containerregistry.listRegistryCredentialsOutput({
  resourceGroupName: resourceGroup.name,
  registryName: acrRegistry.name,
});

export const acrName = pulumi.interpolate`${acrRegistry.name}`;
export const acrLoginServer = pulumi.interpolate`${acrRegistry.loginServer}`;
export const acrAdminUser = acrCredentials.apply(
  (credentials) => credentials.username!
);
export const acrAdminPass = acrCredentials.apply(
  (credentials) => credentials.passwords![0].value!
);

// ======================================================================
// Azure App Service Plan
// https://azure.microsoft.com/en-us/pricing/details/app-service/linux/
// https://www.pulumi.com/registry/packages/azure-native/api-docs/web/appserviceplan/
// ======================================================================
const appServicePlan = new web.AppServicePlan("asp-main-", {
  resourceGroupName: rgName,
  kind: "App",
  sku: {
    name: "P1V3", // 2 Core, 8GB RAM, 130 eur / mo
    tier: "Premium",
  },
  reserved: true,
});

export const appServicePlanId = pulumi.interpolate`${appServicePlan.id}`;

// ======================================================================
// Functions
// ======================================================================
const fncApp = new web.WebApp("app-functions-", {
  resourceGroupName: resourceGroup.name,
  serverFarmId: appServicePlan.id,
  kind: "functionapp",
  siteConfig: {
    appSettings: [
      // { name: "AzureWebJobsStorage", value: saMainConnectionString },
      { name: "FUNCTIONS_EXTENSION_VERSION", value: "~4" }, // https://learn.microsoft.com/en-us/azure/azure-functions/functions-app-settings#functions_extension_version
      { name: "FUNCTIONS_WORKER_RUNTIME", value: "node" }, // https://learn.microsoft.com/en-us/azure/azure-functions/functions-app-settings#functions_worker_runtime

      // Note: we use remote build by enabling the following flags
      // this is because code deployment should be done outside IaC as IaC is for component provisioning and not code deployment
      // e.g., for a function app we provide the function app and publish our functions with the function cli
      // this is required for requirements.txt and others!
      //
      // More info:
      // - https://docs.microsoft.com/en-us/azure/azure-functions/functions-deployment-technologies#remote-build
      // - https://github.com/Azure/bicep/discussions/5833
      // - https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level#package-management
      { name: "SCM_DO_BUILD_DURING_DEPLOYMENT", value: "false" },
      { name: "ENABLE_ORYX_BUILD", value: "true" },
      { name: "WEBSITE_RUN_FROM_PACKAGE", value: "0" },

      { name: "secret-landingpageemails-connectionstring", value: saMainConnectionString }
    ],
    // https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-node?tabs=v2-v3-v4-export%2Cv2-v3-v4-done%2Cv2%2Cv2-log-custom-telemetry%2Cv2-accessing-request-and-response%2Cwindows-setting-the-node-version#node-version
    linuxFxVersion: "node|18", // https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python#python-version
  },
});

// @todo: enable app logs
// https://github.com/Azure-Samples/webapi-nodejs/blob/89fb1dc24449377819680e7921ceaa35f77f945e/deploy/infra/webapi/webapp.bicep#L66
const fncAppInsights = new insights.Component("ai-fnc-app-", {
  resourceGroupName: resourceGroup.name,
  location: glbLocation,
  kind: "web",
  applicationType: "web",
});

export const fncAppHelp = pulumi.interpolate`Deploy code with: "func azure functionapp publish ${fncApp.name}"`;
export const endpoint = pulumi.interpolate`https://${fncApp.defaultHostName}/api/`;

// ======================================================================
// Frontend - Application
// ======================================================================
const appFrontendName = "frontend";
const appFrontendDnsName = new random.RandomString(`rnd-${appFrontendName}`,
  {
    length: 6,
    special: false,
    upper: false,
    lower: true,
    number: true,
  }
);

export const appcontainerFrontendDnsName = pulumi.interpolate`app-${appFrontendName}-${appFrontendDnsName.result}`;

const appFrontend = pulumi
  .all([acrLoginServer, acrAdminUser, acrAdminPass])
  .apply(async ([acrLoginServer, acrAdminUser, acrAdminPass]) => {
    return new web.WebApp(
      `app-${appFrontendName}`,
      {
        resourceGroupName: rgName,
        serverFarmId: appServicePlan.id,
        siteConfig: {
          appSettings: [
            {
              name: "WEBSITES_ENABLE_APP_SERVICE_STORAGE",
              value: "false",
            },
            {
              name: "DOCKER_REGISTRY_SERVER_URL",
              value: acrLoginServer,
            },
            {
              name: "DOCKER_REGISTRY_SERVER_USERNAME",
              value: acrAdminUser,
            },
            {
              name: "DOCKER_REGISTRY_SERVER_PASSWORD",
              value: acrAdminPass,
            },
            {
              name: "DOCKER_CUSTOM_IMAGE_NAME",
              value: appFrontendName,
            },
            {
              name: "DOCKER_ENABLE_CI", // Automatically update the app when the image changes
              value: "true"
            },
            {
              name: "WEBSITES_PORT",
              value: "3000",
            },
          ],
          alwaysOn: true,
        },
        httpsOnly: true,
      }
    );
  });

export const appFrontendDockerHelp = pulumi.interpolate`Upload an image to ACR with: "docker push ${acrLoginServer}/${appFrontendName}"`;

const appFrontendPubCreds = web.listWebAppPublishingCredentialsOutput({
  resourceGroupName: rgName,
  name: appFrontend.name
});

// Create a webhook for the container registry to trigger a deployment
// More info: https://github.com/Azure/bicep/discussions/3352#discussioncomment-978622
const appFrontendAcrWebhook = pulumi
  .all([glbLocation, glbProjectName, glbProjectEnv])
  .apply(([glbLocation, glbProjectName, glbProjectEnv]) => {
    return new acr.Webhook(`acr-wh-${appFrontendName}`.replace(/-/g, ''), {
      resourceGroupName: rgName,
      location: glbLocation,
      registryName: acrName,
      scope: appFrontend.name,
      actions: ["push"],
      // Format is: https://user:pass@app.azurewebsites.net/docker/hook
      serviceUri: pulumi.interpolate`https://${appFrontendPubCreds.scmUri}/docker/hook`,
    });
  });