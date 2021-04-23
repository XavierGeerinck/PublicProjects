"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fetch_1 = __importDefault(require("node-fetch"));
const express_1 = __importDefault(require("express"));
class DaprPubSub {
    constructor(daprUrl, daprPort) {
        this.url = daprUrl || "127.0.0.1";
        this.port = daprPort || 3500;
        if (!this.url.startsWith('http://') && !this.url.startsWith('https://')) {
            this.url = `http://${this.url}`;
        }
        this.urlDapr = `${this.url}:${this.port}/v1.0`;
    }
    async publish(pubSubName, topic, body = {}) {
        const r = await node_fetch_1.default(`${this.urlDapr}/publish/${pubSubName}/${topic}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
    }
    subscribe(app, pubSubName, topic, cb) {
        app.use(express_1.default.json({ type: 'application/*+json' }));
        app.get('/dapr/subscribe', (req, res) => {
            res.json([
                {
                    pubsubname: pubSubName,
                    topic,
                    route: `route-${topic}`
                }
            ]);
        });
        app.post(`/route-${topic}`, (req, res) => {
            cb(req, res);
        });
    }
}
exports.default = DaprPubSub;
//# sourceMappingURL=pubsub.js.map