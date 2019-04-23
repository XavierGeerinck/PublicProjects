const config = {
  eventHubUrl: "", // <ehName>.servicebus.windows.net
  eventHubSharedAccessKeyName: "RootManageSharedAccessKey",
  eventHubSharedAccessKey: "",
  eventHubNamespace: "", // <ehNamespace>
  eventHub: "",
};

module.exports = {
  ...config,
  getConnectionString: () => `Endpoint=sb://${config.eventHubUrl}/;SharedAccessKeyName=${config.eventHubSharedAccessKeyName};SharedAccessKey=${config.eventHubSharedAccessKey}`
}