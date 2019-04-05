// ======================================================
// CONFIG START
// ======================================================
// /[eventHubPath]/ConsumerGroups/[consumerGroup]/Partitions/[partitionId]
// wss://<eventhubNamespace>.servicebus.windows.net:443/$servicebus/websocket -->
var eventhubNamespace = "FILL_IN"; // ehNamespace
var eventhubName = "FILL_IN"; // ehName
var eventHubConsumerGroup = "$Default";

var sharedAccessKeyName = "FILL_IN";
var sharedAccessKey = "FILL_IN";
// ======================================================
// CONFIG END
// ======================================================

var hostName = eventhubNamespace + ".servicebus.windows.net";
var wsServer = "wss://" + hostName + ":443/$servicebus/websocket";
var connectionSettings = {
  "hostname": hostName,
  "container_id": "conn" + new Date().getTime(),
  "max_frame_size": 4294967295,
  "channel_max": 65535,
  "idle_timeout": 120000,
  "outgoing_locales": 'en-US',
  "incoming_locales": 'en-US',
  "offered_capabilities": null,
  "desired_capabilities": null,
  "properties": {},
  "connection_details": null, // Will be set below!
  "reconnect": false,
  "username": sharedAccessKeyName,
  "password": sharedAccessKey,
  "onSuccess": null,
  "onFailure": null,
}

// Connect to the EventHub over AMQP
var sender;
var client = require("rhea");
var ws = client.websocket_connect(WebSocket);
connectionSettings.connection_details = ws(wsServer, [ "AMQPWSB10" ]);
client.on('connection_open', function (ctx) {
  console.log('Connection Opened');

  // Connect to a topic, $management contains our partitions
  // More: https://github.com/Azure/azure-event-hubs-node/blob/91ba72d47f0fbc0e07318c221102bbcb01df271a/send_receive/lib/client.js#L169
  connection.open_receiver('$management');
  sender = connection.open_sender('$management');
});

client.on('connection_error', function (ctx) {
  console.log('Connection Error: ' + ctx);
});

client.on('connection_close', function (ctx) {
  console.log('Connection Closed');
});

client.on('receiver_open', function (ctx) {
  console.log('Receiver open');
  console.log(ctx);
});

client.on('sendable', function (context) {
  // Our sender to the $management topic has been opened
  // Send a message to our $management topic to fetch our partitions
  sender.send({
    body: client.message.data_section(str2ab('[]')),
    application_properties: {
      operation: 'READ',
      name: eventhubName,
      type: 'com.microsoft:eventhub'
    }
  });
});

client.on("message", function (context) {
  if (context.receiver.source.address === '$management') {
    var p = context.message.body;
    var partitionCount = p.partition_count;

    // Open receivers for all my partitions
    for (var i = 0; i < partitionCount; i++) {
      console.log('Opening receiver for ' + '/' + eventhubName + '/ConsumerGroups/' + eventHubConsumerGroup + '/Partitions/' + i)
      connection.open_receiver({
        source: {
          address: '/' + eventhubName + '/ConsumerGroups/' + eventHubConsumerGroup + '/Partitions/' + i,
          filter: client.filter.selector("amqp.annotation.x-opt-enqueuedtimeutc > " + (new Date().getTime()))
        }
      });
    }
  }

  // Process message
  if (!context.message.body.content) {
    return;
  }

  var decodedMessage = Utf8ArrayToStr(context.message.body.content);
  var decodedMessages = decodedMessage.split('\n'); // Apparently multiple json messages per payload
  var decodedMessage = JSON.parse(decodedMessages[0]);

  console.log("Got Message: ");
  console.log(decodedMessage);

  document.querySelector("#content").innerHTML = "<img id=\"minecraft\" />";
  document.querySelector("#minecraft").src = "/images/dolls/" + decodedMessage.name + ".png";
});


client.on("error", function (ctx) {
  console.log(ctx);
})

var connection = client.connect(connectionSettings);