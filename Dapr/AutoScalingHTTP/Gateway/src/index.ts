import ServerExternal from './server-external';
import ServerDapr from './server-dapr';

// Global response store
console.log("[Gateway] Creating Response Store");
const expressResponseStore = {};

console.log("[Gateway] Starting External Server - Port 5000");
const serverExternal = new ServerExternal(5000, expressResponseStore);
serverExternal.start();

console.log("[Gateway] Starting Dapr Server - Port 5001");
const serverDapr = new ServerDapr(5001, expressResponseStore);
serverDapr.start();