import DaprBinding from "./binding";
import DaprPubSub from "./pubsub";
import DaprState from "./state";
export default class Dapr {
    url: string;
    urlDapr: string;
    port: number;
    pubsub: DaprPubSub;
    state: DaprState;
    binding: DaprBinding;
    constructor(daprUrl: any, daprPort: any);
}
