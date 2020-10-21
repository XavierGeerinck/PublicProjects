"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const url_1 = __importDefault(require("url"));
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const config_1 = __importDefault(require("./config"));
const dapr_1 = __importDefault(require("./API/dapr"));
const uuid_1 = require("uuid");
class ServerExternal {
    constructor(port, expressResponseStore) {
        this.port = port || 3000;
        this.app = express_1.default();
        this.daprService = new dapr_1.default(config_1.default.third_party.dapr.url, config_1.default.third_party.dapr.port);
        this.expressResponseStore = expressResponseStore;
        this.timeouts = [];
    }
    start() {
        this.app.use(express_1.default.json());
        this.app.use(cors_1.default());
        this.app.get('/', async (req, res) => await this.routeMain(req, res));
        this.app.listen(this.port, () => console.log(`Listening on port ${this.port}`));
    }
    async routeMain(req, res) {
        let queryObject;
        try {
            queryObject = url_1.default.parse(req.url, true).query;
        }
        catch (e) {
            return res.json({
                error: "PARAM_URL_INCORRECT",
                error_description: e.message
            });
        }
        const id = uuid_1.v4();
        const timeoutMs = 60 * 1000;
        console.log(`[${id}] Processing request`);
        await new Promise(resolve => setTimeout(resolve, 1000));
        console.log(`[${id}] Finished Processing request`);
        res.json({ res: "HELLO WORLD" });
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
        });
        console.log(`[${id}] - Removing from response store`);
        delete this.expressResponseStore[id];
        console.log(`[${id}] - DONE`);
    }
}
exports.default = ServerExternal;
//# sourceMappingURL=server-external.js.map