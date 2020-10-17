import ServerExternal from './server-external';
import ServerDapr from './server-dapr';

// Global response store
console.log("Creating Response Store");
const expressResponseStore = {};

console.log("Starting External Server - Port 5000");
const serverExternal = new ServerExternal(5000, expressResponseStore);
serverExternal.start();

console.log("Starting Dapr Server - Port 5001");
const serverDapr = new ServerDapr(5001, expressResponseStore);
serverDapr.start();