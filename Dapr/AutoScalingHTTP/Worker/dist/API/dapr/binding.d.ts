import express from 'express';
interface FunctionDaprInputCallback {
    (data: object): Promise<any>;
}
export default class DaprBinding {
    url: string;
    urlDapr: string;
    port: number;
    constructor(daprUrl: string, daprPort: any);
    receive(app: express, bindingName: string, cb: FunctionDaprInputCallback): void;
    send(bindingName: string, data: object): Promise<any>;
}
export {};
