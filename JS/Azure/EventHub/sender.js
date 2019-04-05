const uuidv4 = require('uuid/v4');
const eventHubClient = require('azure-event-hubs').Client;
const config = require('./config.js');

// Init Client
const client = eventHubClient.fromConnectionString(config.getConnectionString(), config.eventHub);

// Create a sender that sends random temperature and humidity values
const start = async () => {
  const sender = await client.createSender();

  const sensorCount = 2;
  const sensors = generateSensors(sensorCount);


  sensors.forEach((sensorId) => {
    let intervalTime = Math.random() * 1000 + 500; // Between 500ms and 1s
    let interval = setInterval(() => {
      console.log(`Sending values for sensor_${sensorId}`);

      sender.send({
        sensor: sensorId,
        temperatureValue: createValueTemperature(),
        humidityValue: createValueHumidity(),
        createdAt: new Date()
      });
    }, intervalTime)
  });
};

const generateSensors = (count) => {
  let sensors = [];

  for (let i = 0; i < count; i++) {
    sensors.push(uuidv4());
  }

  return sensors;
}

const createValueHumidity = () => ((Math.random() * 100) + 30).toFixed(2);

const createValueTemperature = () => ((Math.random() * 41) - 10).toFixed(2);

console.log('Starting sender');
start();