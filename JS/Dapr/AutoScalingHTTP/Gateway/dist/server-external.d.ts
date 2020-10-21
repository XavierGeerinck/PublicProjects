import express from 'express';
import Dapr from './API/dapr';
declare class ServerExternal {
    port: number;
    app: express;
    daprService: Dapr;
    expressResponseStore: object;
    timeouts: Array<any>;
    constructor(port: number, expressResponseStore: object);
    start(): void;
    routeMain(req: any, res: any): Promise<any>;
    handleTimeout(id: any): Promise<void>;
}
export default ServerExternal;
