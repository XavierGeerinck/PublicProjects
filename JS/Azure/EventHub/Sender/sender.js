const uuidv4 = require('uuid/v4');
const eventHubClient = require('azure-event-hubs').Client;
const fs = require('fs');
const readline = require('readline');
const config = require('./config.js');

// Init Client
const client = eventHubClient.fromConnectionString(config.getConnectionString(), config.eventHub);

// Create a sender that sends random temperature and humidity values
const start = async () => {
  const sender = await client.createSender();

  const file = `data/${process.argv[2]}`;
  const sendFullFile = (process.argv[3] == "false") ? false : true || true;

  console.log(`[Sender] Sending content of file ${file}`);
  await streamFileToEH(sender, file, sendFullFile);
  console.log('[Sender] Done');
};

const streamFileToEH = async (sender, fileName, sendFullFile) => {
  console.log(`[Sender] Streaming complete file? ${sendFullFile}`);

  if (sendFullFile) {
    return await streamFileToEHFull(sender, fileName);
  }

  return await streamFileToEHLineByLine(sender, fileName);
};

const streamFileToEHFull = async (sender, fileName) => new Promise(async (resolve) => {
  let content = fs.readFileSync(fileName);
  sender.send(content);
  return resolve();
});

const streamFileToEHLineByLine = async (sender, fileName) => new Promise(async (resolve) => {
  // Read from data
  // Note: Node >= 11.4 required
  //       https://github.com/nodejs/node/pull/23916
  let fileStream = fs.createReadStream(fileName);
  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity // crlfDelay to recognize all instances of CR LF (\r\n) as a single line break
  });

  // Process lines
  let lineIdx = 0;
  for await (const line of rl) {
    lineIdx++;
    // Each line in input.txt will be successively available here as `line`.
    console.log(`Sending line #${lineIdx}: ${line}`);
    sender.send(line);
    await sleep(1000); // Send line every 1000 ms => 1 messages / sec 
  }

  return resolve();
});

const sleep = async (ms) => new Promise(resolve => setTimeout(resolve, ms));

console.log('[Sender] Starting sender');
start();