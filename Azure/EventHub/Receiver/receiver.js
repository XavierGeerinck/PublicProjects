const config = require('./config.js');
const Stream = require('./stream.js');

// Init Client
console.log('[Receiver] Initializing Stream');
const stream = new Stream(config.getConnectionString(), { eventHubName: config.eventHub });

// Create a sender that sends random temperature and humidity values
const start = async () => {
  await stream.open();

  console.log('[Receiver] Awaiting Message from Stream');
  try {
    const message = await stream.receiveOneMessageAndClose({ timeout: 100000 });
    console.log(`[Receiver] Received Message : ${JSON.stringify(message)}`);
  } catch (e) {
    console.log('triggered')
    console.error(e);
  }
};

console.log('[Receiver] Starting Receiver');
start();