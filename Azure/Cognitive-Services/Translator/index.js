const fs = require('fs');
const Throttler = require('../Throttler');
const config = require('./config');
const CognitiveServiceTranslate = require('./api/CognitiveServiceTranslate');
const api = new CognitiveServiceTranslate(config.microsoft.cognitive.translate);

// Read in our lines
const inFile = fs.readFileSync('./in_sentences.txt').toString();
const inLines = inFile.split(/\r?\n/);

// Create our REST calls
let calls = [];
let results = [];

inLines.forEach((line) => {
  calls.push(async (isDone, idx) => {
    let translateResult = await api.translate(line, [ 'en' ]);
    results[idx] = translateResult[0].translations[0].text;
    isDone();
  });
});

const start = async () => {
  // Create our throttler
  const throttler = new Throttler(calls, 10, 1000);
  await throttler.execute();

  // Done write result
  fs.writeFileSync('./results.json', JSON.stringify(results));
  fs.writeFileSync('./out_sentences.txt', results.join("\n"));
  console.log("DONE");
}

start();

