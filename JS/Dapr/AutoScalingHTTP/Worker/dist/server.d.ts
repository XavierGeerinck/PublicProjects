import express from 'express';
import Dapr from './API/dapr';
declare class Server {
    port: number;
    app: express;
    daprService: Dapr;
    constructor(port: number);
    start(): void;
    bindingRabbitMQInput(data: any): Promise<void>;
}
export default Server;
