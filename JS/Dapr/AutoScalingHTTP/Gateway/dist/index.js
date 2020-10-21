"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
console.log("Creating Response Store");
const expressResponseStore = {};
const app = express_1.default();
app.use(express_1.default.json());
app.use(cors_1.default());
app.get('/', async (req, res) => {
    console.log('Processing');
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('DONE');
    res.json({ res: "DONE" });
});
app.listen(5000, () => console.log(`Listening on port 5000`));
//# sourceMappingURL=index.js.map