"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const binding_1 = __importDefault(require("./binding"));
const pubsub_1 = __importDefault(require("./pubsub"));
const state_1 = __importDefault(require("./state"));
class Dapr {
    constructor(daprUrl, daprPort) {
        this.url = daprUrl || "127.0.0.1";
        this.port = daprPort || 3500;
        if (!this.url.startsWith('http://') && !this.url.startsWith('https://')) {
            this.url = `http://${this.url}`;
        }
        this.urlDapr = `${this.url}:${this.port}/v1.0`;
        this.pubsub = new pubsub_1.default(daprUrl, daprPort);
        this.state = new state_1.default(daprUrl, daprPort);
        this.binding = new binding_1.default(daprUrl, daprPort);
    }
}
exports.default = Dapr;
//# sourceMappingURL=index.js.map