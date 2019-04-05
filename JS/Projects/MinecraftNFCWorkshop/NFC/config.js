const config = {
  eventHubUrl: "FILL_IN.servicebus.windows.net", // <ehNamespace>.servicebus.windows.net
  eventHubSharedAccessKeyName: "RootManageSharedAccessKey",
  eventHubSharedAccessKey: "FILL_IN", // RootManagedSharedAccessKey
  eventHubNamespace: "FILL_IN", // ehNamespace
  eventHub: "FILL_IN", // ehName
};

module.exports = {
  ...config,
  getConnectionString: () => `Endpoint=sb://${config.eventHubUrl}/;SharedAccessKeyName=${config.eventHubSharedAccessKeyName};SharedAccessKey=${config.eventHubSharedAccessKey}`
}