import express from 'express';
import Config from './config';
import Dapr from './API/dapr';
import DaprBindingEnum from './enum/DaprBinding.enum';

interface IQueryObject {
  timeout?: number;
  name?: string;
}

class Server {
  port: number;
  app: express;
  daprService: Dapr;

  constructor(port: number) {
    this.port = port || 3000;
    this.app = express();
    this.daprService = new Dapr(Config.third_party.dapr.url, Config.third_party.dapr.port);
    this.daprService.binding.receive(this.app, DaprBindingEnum.RABBIT_MQ_INPUT, this.bindingRabbitMQInput.bind(this))
  }

  start() {
    this.app.listen(this.port, () => console.log(`[Worker] Listening on port ${this.port}`));
  }

  async bindingRabbitMQInput(data) {
    console.log(`[Worker] Received request`);

    if (!data?.requestId) {
      console.log(`[Worker] RequestID not set`);
      return;
    }

    const requestId = data.requestId;
    let queryParsed = {} as IQueryObject;

    try {
      queryParsed = JSON.parse(data.query);
    } catch (e) {
      queryParsed = {};
    }

    console.log(`[Worker][${requestId}] Processing request`);
    console.log(`[Worker][${requestId}] - Got Data from Gateway: ${data}`);
    
    if (queryParsed.timeout) {
      console.log(`[${requestId}] - Handling timeout`);
      await this.timeout(queryParsed.timeout); // timeout was passed in the query parameters
    }

    console.log(`[Worker][${requestId}] Done processing, publishing result`);
    await this.daprService.binding.send(DaprBindingEnum.RABBIT_MQ_OUTPUT, {
      requestId,
      result_worker: `Welcome Back, ${queryParsed.name || "John Doe"}<br /><br />-- Page Timeout: ${queryParsed.timeout || 0}ms`
    });
  }

  async timeout(ms = 1000) {
    return new Promise((resolve, reject) => setTimeout(resolve, ms));
  }
}

export default Server;