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
  
    constructor(daprUrl, daprPort) {
      this.url = daprUrl || "127.0.0.1";
      this.port = daprPort || 3500;
  
      if (!this.url.startsWith('http://') && !this.url.startsWith('https://')) {
        this.url = `http://${this.url}`;
      }
  
      this.urlDapr = `${this.url}:${this.port}/v1.0`;

      this.pubsub = new DaprPubSub(daprUrl, daprPort);
      this.state = new DaprState(daprUrl, daprPort);
      this.binding = new DaprBinding(daprUrl, daprPort);
    }
}