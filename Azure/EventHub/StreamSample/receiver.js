const config = require('./config');
const Stream = require('./stream/stream');
const StreamEventHub = require('./stream/streamEventHub.ts');
const StreamSocket = require('./stream/streamSocket');

// Init Client
console.log('[Receiver] Initializing Stream');
const streamEventHub = new StreamEventHub(config.getConnectionString(), { eventHubName: config.eventHub });
const streamSocket = new StreamSocket("seppe.net", 7778);
const stream = new Stream(streamSocket);

// Create a sender that sends random temperature and humidity values
const start = async () => {
  await stream.open();

  console.log('[Receiver] Awaiting Message from Stream');
  try {
    const message = await stream.receiveOneMessageAndClose({ timeout: 10000 });
    console.log('[Receiver] Received Message');
    console.log(message.toString('utf8'));
  } catch (e) {
    console.log('triggered')
    console.error(e);
  }
};

console.log('[Receiver] Starting Receiver');
start();