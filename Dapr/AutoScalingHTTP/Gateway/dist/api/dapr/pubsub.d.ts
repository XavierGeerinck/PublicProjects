export default class DaprPubSub {
    url: string;
    urlDapr: string;
    port: number;
    constructor(daprUrl: any, daprPort: any);
    publish(pubSubName: string, topic: string, body?: object): Promise<void>;
    subscribe(app: any, pubSubName: string, topic: string, cb: any): void;
}
