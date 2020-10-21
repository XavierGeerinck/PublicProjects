import url from 'url';
import express from 'express';
import cors from 'cors';
import Config from './config';
import Dapr from './API/dapr';
import DaprBindingEnum from './enum/DaprBinding.enum';
import { v4 as uuidv4 } from 'uuid';

class ServerExternal {
  port: number;
  app: express;
  daprService: Dapr;
  expressResponseStore: object;
  timeouts: Array<any>;

  constructor(port: number, expressResponseStore: object) {
    this.port = port || 3000;
    this.app = express();
    this.daprService = new Dapr(Config.third_party.dapr.url, Config.third_party.dapr.port);
    this.expressResponseStore = expressResponseStore;
    this.timeouts = [];
  }

  start() {
    this.app.use(express.json()); // Set size limit

    // Middleware
    this.app.use(cors());

    // Routes
    this.app.get('/', async (req, res) => this.routeMain(req, res)); // routeMain is async, so we are not awaiting it and throwing it in the event loop!!!

    // Start Server
    this.app.listen(this.port, () => console.log(`Listening on port ${this.port}`));
  }

  async routeMain(req, res) {
    // Start processing
    let queryObject;

    try {
      queryObject = url.parse(req.url, true).query;
    } catch (e) {
      return res.json({
        error: "PARAM_URL_INCORRECT",
        error_description: e.message
      });
    }

    // Generate id and add our response object to map
    const id = uuidv4();
    const timeoutMs = 60 * 1000;
    this.expressResponseStore[id] = {
      res,
      req,
      timeout: setTimeout(() => this.handleTimeout(id), timeoutMs)
    };

    // Send a custom Request ID
    console.log(`[Gateway][${id}] Processing request`)
    await this.daprService.binding.send(DaprBindingEnum.RABBIT_MQ_INPUT, {
      requestId: id,
      query: JSON.stringify(queryObject)
    })
    console.log(`[Gateway][${id}] Finished Processing request`);
  }

  async handleTimeout(id) {
    console.log(`[Gateway][${id}] Timeout occurred, checking if we need to clean up`);

    if (!id) {
      return;
    }

    if (!this.expressResponseStore[id]) {
      console.log(`[Gateway][${id}] Already cleaned up`);
      return;
    }

    const userReq = this.expressResponseStore[id];

    console.log(`[Gateway][${id}] We need to clean, cleaning it up`);

    console.log(`[Gateway][${id}] - Removing timeout itself`);
    clearTimeout(userReq.timeout);

    console.log(`[Gateway][${id}] - Sending response to user with error`);
    userReq.res.json({
      error: "TIMEOUT",
      error_description: "Could not load within the allocated time of 60 seconds."
    })

    console.log(`[Gateway][${id}] - Removing from response store`);
    delete this.expressResponseStore[id];

    console.log(`[Gateway][${id}] - DONE`);
  }
}

export default ServerExternal;