const eventHubClient = require('azure-event-hubs').Client;
const config = require('./config.js');

// Init Client
console.log(config.getConnectionString());
const client = eventHubClient.fromConnectionString(config.getConnectionString(), config.eventHub);
const consumerGroup = '$Default';

// Create a receiver
client.open()
.then(client.getPartitionIds.bind(client))
.then((partitionIds) => {
  return partitionIds.map((partitionId) => {
    client.createReceiver(consumerGroup, partitionId, { 'startAfterTime': Date.now() })
    .then((receiver) => {
      console.log(`[Partition - ${partitionId}] Receiver Created`);
      receiver.on('errorReceived', (err) => console.log(`[Partition - ${partitionId}] Error: ${err.message}`));
      receiver.on('message', (message) => console.log(`[Partition - ${partitionId}] Message: ${JSON.stringify(message.body)}`));
    })
  })
})
.catch((err) => console.log(`Error: ${err}`));