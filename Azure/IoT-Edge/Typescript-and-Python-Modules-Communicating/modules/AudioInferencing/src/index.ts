import { Mqtt } from "azure-iot-device-mqtt";
import { ModuleClient, Message } from "azure-iot-device";

async function main() {
  await init();
}

async function init() {
  console.log("Initializing module client");
  // Relies on ENV variable "EdgeHubConnectionString" or "IotHubConnectionString"
  const client = await ModuleClient.fromEnvironment(Mqtt);

  console.log("Opening module client");
  // Connect to the Edge Instance
  await client.open();

  console.log("Listening on messages");
  // Listen to incoming messages
  client.on("inputMessage", (inputName, msg) => {
    console.log("Incoming Message");
    console.log(inputName);
    console.log(msg);
  });
}

init().catch((e) => console.error(e));