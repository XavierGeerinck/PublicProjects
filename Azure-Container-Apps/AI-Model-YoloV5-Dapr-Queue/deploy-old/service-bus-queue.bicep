// scope
targetScope = 'resourceGroup'

// parameters
param name string
param serviceBusNamespace string

resource sbq 'Microsoft.ServiceBus/namespaces/queues@2021-06-01-preview' = {
  name: '${serviceBusNamespace}/${name}'
  properties: {
    lockDuration: 'PT5M'
    maxSizeInMegabytes: 1024
    requiresDuplicateDetection: false
    requiresSession: false
    defaultMessageTimeToLive: 'P1DT0H0M0.0S'
    deadLetteringOnMessageExpiration: false
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    maxDeliveryCount: 4
    autoDeleteOnIdle: 'P1DT0H0M0.0S'
    enablePartitioning: false
    enableExpress: false
  }
}

resource sbqa 'Microsoft.ServiceBus/namespaces/queues/authorizationRules@2021-06-01-preview' = {
  parent: sbq
  name: 'main-key'
  properties: {
    rights: [
      'Listen'
      'Manage'
      'Send'
    ]
  }
}

// https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/bicep-functions-resource#list
output connectionString string = sbqa.listKeys().primaryConnectionString
output primaryKey string = sbqa.listKeys().primaryKey
