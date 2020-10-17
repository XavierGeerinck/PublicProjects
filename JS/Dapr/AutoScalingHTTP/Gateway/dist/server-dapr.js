"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const config_1 = __importDefault(require("./config"));
const dapr_1 = __importDefault(require("./api/dapr"));
const DaprBinding_enum_1 = __importDefault(require("./enum/DaprBinding.enum"));
class ServerDapr {
    constructor(port, expressResponseStore) {
        this.port = port || 3000;
        this.app = express_1.default();
        this.daprService = new dapr_1.default(config_1.default.third_party.dapr.url, config_1.default.third_party.dapr.port);
        this.expressResponseStore = expressResponseStore;
    }
    start() {
        this.app.use(express_1.default.json({ limit: '10mb' }));
        this.daprService.binding.receive(this.app, DaprBinding_enum_1.default.RABBIT_MQ_OUTPUT, this.bindingWorkerResult.bind(this));
        this.app.listen(this.port, () => console.log(`Listening on port ${this.port}`));
    }
    async bindingWorkerResult(data) {
        if (!(data === null || data === void 0 ? void 0 : data.requestId)) {
            return;
        }
        const requestId = data.requestId;
        const client = this.expressResponseStore[requestId];
        if (!client || !client.res || !client.req) {
            return;
        }
        client.res.writeHead(200, { 'Content-Type': 'text/html' });
        client.res.write(data.html);
        client.res.end();
        console.log(`[${requestId}] Cleaning up`);
        clearTimeout(this.expressResponseStore[requestId].timeout);
        delete this.expressResponseStore[requestId];
    }
}
exports.default = ServerDapr;
//# sourceMappingURL=server-dapr.js.map