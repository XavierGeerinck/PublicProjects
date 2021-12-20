// scope
targetScope = 'resourceGroup'

// parameters
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Standard'
param name string
param location string

resource sb 'Microsoft.ServiceBus/namespaces@2021-01-01-preview' = {
  name: name
  location: location
  sku: {
    name: sku
  }
  properties: {}
}

output name string = sb.name
output id string = sb.id

// https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/bicep-functions-resource#list
output connectionString string = listKeys('${sb.id}/AuthorizationRules/RootManageSharedAccessKey', sb.apiVersion).primaryConnectionString
output sharedAccessKey string = listKeys('${sb.id}/AuthorizationRules/RootManageSharedAccessKey', sb.apiVersion).primaryKey
