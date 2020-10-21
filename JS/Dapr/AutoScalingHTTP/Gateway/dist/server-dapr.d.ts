import express from 'express';
import Dapr from './API/dapr';
declare class ServerDapr {
    port: number;
    app: express;
    daprService: Dapr;
    expressResponseStore: object;
    constructor(port: number, expressResponseStore: object);
    start(): void;
    bindingWorkerResult(data: any): Promise<void>;
}
export default ServerDapr;
