"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const server_external_1 = __importDefault(require("./server-external"));
const server_dapr_1 = __importDefault(require("./server-dapr"));
console.log("Creating Response Store");
const expressResponseStore = {};
console.log("Starting External Server - Port 5000");
const serverExternal = new server_external_1.default(5000, expressResponseStore);
serverExternal.start();
console.log("Starting Dapr Server - Port 5001");
const serverDapr = new server_dapr_1.default(5001, expressResponseStore);
serverDapr.start();
//# sourceMappingURL=index.js.map