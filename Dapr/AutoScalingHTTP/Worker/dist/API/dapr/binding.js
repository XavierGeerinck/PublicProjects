"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fetch_1 = __importDefault(require("node-fetch"));
const express_1 = __importDefault(require("express"));
class DaprBinding {
    constructor(daprUrl, daprPort) {
        this.url = daprUrl || "127.0.0.1";
        this.port = daprPort || 3500;
        if (!this.url.startsWith('http://') && !this.url.startsWith('https://')) {
            this.url = `http://${this.url}`;
        }
        this.urlDapr = `${this.url}:${this.port}/v1.0`;
    }
    receive(app, bindingName, cb) {
        app.use(express_1.default.json());
        app.post(`/${bindingName}`, async (req, res) => {
            await cb(req === null || req === void 0 ? void 0 : req.body);
            res.status(200).send();
        });
    }
    async send(bindingName, data) {
        const req = await node_fetch_1.default(`${this.urlDapr}/bindings/${bindingName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data,
                operation: "create"
            })
        });
        let json;
        switch (req.status) {
            case 200:
                return;
                break;
            case 204:
                return null;
                break;
            case 400:
                json = await req.json();
                throw new Error(JSON.stringify(json));
                break;
            case 500:
                json = await req.json();
                throw new Error(JSON.stringify(json));
                break;
            default:
                return null;
        }
    }
}
exports.default = DaprBinding;
//# sourceMappingURL=binding.js.map