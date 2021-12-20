// general Azure Container App settings
param location string
param name string
param containerAppEnvironmentId string

// Container Image ref
param containerImage string

// Networking
param useExternalIngress bool = false
param containerPort int
param daprAppId string
param daprComponents array = []

param registry string = 'docker.io'
param registryUsername string
@secure()
param registryPassword string

param serviceBusNameQueue string
@secure()
param serviceBusConnectionString string

param envVars array = []

resource containerApp 'Microsoft.Web/containerApps@2021-03-01' = {
  name: name
  kind: 'containerapp'
  location: location
  properties: {
    kubeEnvironmentId: containerAppEnvironmentId
    configuration: {
      secrets: [
        {
          name: 'container-registry-password'
          value: registryPassword
        }
        {
          name: 'service-bus-connection-string'
          value: serviceBusConnectionString
        }
      ]
      registries: [
        {
          server: registry
          username: registryUsername
          passwordSecretRef: 'container-registry-password'
        }
      ]
      ingress: {
        external: useExternalIngress
        targetPort: containerPort
      }
    }
    template: {
      containers: [
        {
          image: containerImage
          name: name
          env: envVars
        }
      ]
      dapr: {
        enabled: true
        appPort: containerPort
        appId: daprAppId
        appProtocol: 'grpc'
        components: daprComponents
      }
      scale: {
        minReplicas: 0
        maxReplicas: 10
        rules: [
          {
            name: 'queue-based-autoscaling'
            custom: {
              type: 'azure-servicebus'
              metadata: {
                queueName: serviceBusNameQueue
                messageCount: '20'
              }
              auth: [
                {
                  secretRef: 'service-bus-connection-string'
                  triggerParameter: 'connection'
                }
              ]
            }
          }
        ]
      }
    }
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
