"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const config_1 = __importDefault(require("./config"));
const dapr_1 = __importDefault(require("./API/dapr"));
const DaprBinding_enum_1 = __importDefault(require("./enum/DaprBinding.enum"));
class Server {
    constructor(port) {
        this.port = port || 3000;
        this.app = express_1.default();
        this.daprService = new dapr_1.default(config_1.default.third_party.dapr.url, config_1.default.third_party.dapr.port);
        this.daprService.binding.receive(this.app, DaprBinding_enum_1.default.RABBIT_MQ_INPUT, this.bindingRabbitMQInput.bind(this));
    }
    start() {
        this.app.listen(this.port, () => console.log(`Listening on port ${this.port}`));
    }
    async bindingRabbitMQInput(data) {
        console.log(`Received request`);
        if (!(data === null || data === void 0 ? void 0 : data.requestId)) {
            console.log(`RequestID not set`);
            return;
        }
        const requestId = data.requestId;
        console.log(`[${requestId}] Done, publishing result`);
        const r = await this.daprService.binding.send(DaprBinding_enum_1.default.RABBIT_MQ_OUTPUT, {
            requestId,
            result: "HELLO WORLD"
        });
    }
}
exports.default = Server;
//# sourceMappingURL=server.js.map