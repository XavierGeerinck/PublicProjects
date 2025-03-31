import { EventEmitter } from "events";
import IStream from './IStream';

const net = require('net');

class StreamSocket implements IStream {
    host: string;
    port: number;
    connection: any;
    eventEmitter: EventEmitter;

    constructor(host, port) {
        if (!host) {
            throw new Error('Required parameter Host is not set');
        }

        if (!port) {
            throw new Error('Required parameter Port is not set');
        }

        this.host = host;
        this.port = port;

        this.connection = null;
        this.eventEmitter = null;
    }

    async open(eventEmitter) {
        this.eventEmitter = eventEmitter;

        return new Promise((resolve, reject) => {
            this.connection = net.connect(this.port, this.host, () => {
                return resolve();
            });

            this.connection.on('data', this.onData.bind(this));
            console.log('[StreamSocket] Stream Opened');
        });
    }

    onData(msg) {
        this.eventEmitter.emit('stream_message_received', msg);
    }

    close() {
        this.connection = null;
    }
}

module.exports = StreamSocket;