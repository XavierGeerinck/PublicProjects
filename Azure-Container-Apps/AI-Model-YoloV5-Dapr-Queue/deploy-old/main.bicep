param location string = resourceGroup().location
param containerAppEnvName string
param containerAppName string

param containerImage string
param containerPort int
param registry string
param registryUsername string

@secure()
param registryPassword string

param serviceBusNameNamespace string
param serviceBusNameQueue string

module serviceBus 'service-bus.bicep' = {
  name: 'service-bus'
  params: {
    name: serviceBusNameNamespace
    location: location
    sku: 'Standard'
  }
}

module serviceBusQueue 'service-bus-queue.bicep' = {
  name: 'service-bus-queue'
  params: {
    name: serviceBusNameQueue
    serviceBusNamespace: serviceBusNameNamespace
  }
  dependsOn: [
    serviceBus
  ]
}

module law 'log-analytics.bicep' = {
  name: 'log-analytics-workspace'
  params: {
    location: location
    name: 'law-${containerAppEnvName}'
  }
}

module containerAppEnvironment 'container-app-environment.bicep' = {
  name: 'container-app-environment'
  params: {
    name: containerAppEnvName
    location: location
    lawClientId: law.outputs.clientId
    lawClientSecret: law.outputs.clientSecret
  }
  dependsOn: [
    law
    serviceBusQueue
  ]
}

module containerApp 'container-app-servicebus.bicep' = {
  name: 'container-app-servicebus'
  params: {
    name: containerAppName
    location: location
    containerAppEnvironmentId: containerAppEnvironment.outputs.id
    containerImage: containerImage
    containerPort: containerPort
    daprAppId: 'yolo-v5-processor'
    daprComponents: [
      {
        name: 'queue'
        type: 'bindings.azure.servicebusqueues'
        version: 'v1'
        metadata: [
          {
            name: 'connectionString'
            value: serviceBus.outputs.connectionString
          }
          {
            name: 'queueName'
            value: 'items-ai-yolo-v5'
          }
          {
            name: 'ttlInSeconds'
            value: '60'
          }
        ]
      }
    ]
    useExternalIngress: true
    registry: registry
    registryUsername: registryUsername
    registryPassword: registryPassword
    serviceBusNameQueue: serviceBusNameQueue
    serviceBusConnectionString: serviceBus.outputs.connectionString
  }
  dependsOn: [
    containerAppEnvironment
  ]
}

output fqdn string = containerApp.outputs.fqdn
