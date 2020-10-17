import express from 'express';
import Config from './config';
import Dapr from './API/dapr';
import DaprBindingEnum from './enum/DaprBinding.enum';

class Server {
    port: number;
    app: express;
    daprService: Dapr;

    constructor(port: number) {
        this.port = port || 3000;
        this.app = express();
        this.daprService = new Dapr(Config.third_party.dapr.url, Config.third_party.dapr.port);
        this.daprService.binding.receive(this.app, DaprBindingEnum.RABBIT_MQ_INPUT, this.bindingRabbitMQInput.bind(this))
    }

    start() {
        this.app.listen(this.port, () => console.log(`Listening on port ${this.port}`));
    }

    async bindingRabbitMQInput(data) {
        console.log(`Received request`);

        if (!data?.requestId) {
            console.log(`RequestID not set`);
            return;
        }

        const requestId = data.requestId;

        console.log(`[${requestId}] Done, publishing result`);

        const r = await this.daprService.binding.send(DaprBindingEnum.RABBIT_MQ_OUTPUT, {
            requestId,
            result: "HELLO WORLD"
        })
    }
}

export default Server;