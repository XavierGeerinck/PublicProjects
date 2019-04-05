const config = {
  eventHubUrl: "EVENTHUBURL", // <ehName>.servicebus.windows.net
  eventHubSharedAccessKeyName: "NAME",
  eventHubSharedAccessKey: "KEY",
  eventHubNamespace: "NAMESPACE", // <ehNamespace>
  eventHub: "EVENTHUBNAME",
};

module.exports = {
  ...config,
  getConnectionString: () => `Endpoint=sb://${config.eventHubUrl}/;SharedAccessKeyName=${config.eventHubSharedAccessKeyName};SharedAccessKey=${config.eventHubSharedAccessKey}`
}