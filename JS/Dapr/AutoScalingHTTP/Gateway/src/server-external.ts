import url from 'url';
import express from 'express';
import cors from 'cors';
import Config from './config';
import Dapr from './API/dapr';
import DaprBindingEnum from './enum/DaprBinding.enum';
import { v4 as uuidv4 } from 'uuid';

// @todo, ban following user agents:
// - facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)
// - Ghost(https://github.com/TryGhost/Ghost)
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
    // Express limits the body to 100kb, so we need to change it 
    // https://expressjs.com/en/api.html#express.json
    this.app.use(express.json({ limit: '10mb' })); // Set size limit

    // Middleware
    this.app.use(cors());

    // Routes
    this.app.get('/', this.routeMain.bind(this));

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

    // Gather the options
    const test = queryObject.test as string;

    // Generate id and add our response object to map
    const id = uuidv4();
    const timeoutMs = 60 * 1000;
    this.expressResponseStore[id] = {
      res,
      req,
      timeout: setTimeout(() => this.handleTimeout(id), timeoutMs)
    };

    // Send a custom Request ID
    console.log(`[${id}] Processing request`)
    await this.daprService.binding.send(DaprBindingEnum.RABBIT_MQ_INPUT, {
      requestId: id,
      test
    })
  }

  async handleTimeout(id) {
    console.log(`[${id}] Timeout occurred, checking if we need to clean up`);

    if (!id) {
      return;
    }

    if (!this.expressResponseStore[id]) {
      console.log(`[${id}] Already cleaned up`);
      return;
    }

    const userReq = this.expressResponseStore[id];

    console.log(`[${id}] We need to clean, cleaning it up`);

    console.log(`[${id}] - Removing timeout itself`);
    clearTimeout(userReq.timeout);

    console.log(`[${id}] - Sending response to user with error`);
    userReq.res.json({
      error: "TIMEOUT",
      error_description: "Could not load within the allocated time of 60 seconds."
    })

    console.log(`[${id}] - Removing from response store`);
    delete this.expressResponseStore[id];

    console.log(`[${id}] - DONE`);
  }
}

export default ServerExternal;