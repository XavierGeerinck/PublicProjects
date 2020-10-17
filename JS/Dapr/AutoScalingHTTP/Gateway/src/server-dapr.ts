import express from 'express';
import Config from './config';
import Dapr from './API/dapr';
import DaprBindingEnum from './enum/DaprBinding.enum';

class ServerDapr {
  port: number;
  app: express;
  daprService: Dapr;
  expressResponseStore: object

  constructor(port: number, expressResponseStore: object) {
    this.port = port || 3000;
    this.app = express();
    this.daprService = new Dapr(Config.third_party.dapr.url, Config.third_party.dapr.port);
    this.expressResponseStore = expressResponseStore;
  }

  start() {
    // Express limits the body to 100kb, so we need to change it 
    // https://expressjs.com/en/api.html#express.json
    this.app.use(express.json({ limit: '10mb' })); // Set size limit

    // Bindings
    this.daprService.binding.receive(this.app, DaprBindingEnum.RABBIT_MQ_OUTPUT, this.bindingWorkerResult.bind(this))

    // Start Server
    this.app.listen(this.port, () => console.log(`Listening on port ${this.port}`));
  }

  async bindingWorkerResult(data) {
    if (!data?.requestId) {
      return;
    }

    const requestId = data.requestId; // Request ID
    const client = this.expressResponseStore[requestId];

    if (!client || !client.res || !client.req) {
      return;
    }

    // Send response to the client
    client.res.writeHead(200, { 'Content-Type': 'text/html' });
    client.res.write(data.html);
    client.res.end();

    // Clean up
    console.log(`[${requestId}] Cleaning up`);
    clearTimeout(this.expressResponseStore[requestId].timeout);
    delete this.expressResponseStore[requestId];
  }
}

export default ServerDapr;