"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fetch_1 = __importDefault(require("node-fetch"));
class DaprState {
    constructor(daprUrl, daprPort) {
        this.url = daprUrl || "127.0.0.1";
        this.port = daprPort || 3500;
        if (!this.url.startsWith('http://') && !this.url.startsWith('https://')) {
            this.url = `http://${this.url}`;
        }
        this.urlDapr = `${this.url}:${this.port}/v1.0`;
    }
    async save(storeName, stateObjects) {
        const req = await node_fetch_1.default(`${this.urlDapr}/state/${storeName}`, {
            method: 'POST',
            body: JSON.stringify(stateObjects)
        });
        let json;
        switch (req.status) {
            case 200:
                json = await req.json();
                return json;
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
    async get(storeName, key) {
        const req = await node_fetch_1.default(`${this.urlDapr}/state/${storeName}/${key}`);
        let json;
        switch (req.status) {
            case 200:
                json = await req.json();
                return json;
                break;
            case 204:
                console.log(req.status);
                console.log(req.statusText);
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
    async delete(storeName, key) {
        const req = await node_fetch_1.default(`${this.urlDapr}/state/${storeName}/${key}`, {
            method: 'DELETE'
        });
        return req.status;
    }
}
exports.default = DaprState;
//# sourceMappingURL=state.js.map