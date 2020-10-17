interface IKeyValuePair {
    key: string;
    value: string;
}
export default class DaprState {
    url: string;
    urlDapr: string;
    port: number;
    constructor(daprUrl: any, daprPort: any);
    save(storeName: string, stateObjects: IKeyValuePair[]): Promise<number>;
    get(storeName: string, key: string): Promise<object>;
    delete(storeName: string, key: string): Promise<number>;
}
export {};
