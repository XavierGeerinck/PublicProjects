const eventHubClient = require('azure-event-hubs').Client;

import IStream from './IStream';
import { EventEmitter } from 'events';

class Stream implements IStream  {
    endpoint: string;
    options: {
        consumerGroup: string,
        eventHubName: string
    };
    receivers: Array<any>;
    eventEmitter: EventEmitter;
    client: any;

    constructor(endpoint, options) {
        if (!endpoint) {
            throw new Error('Endpoint not set');
        }

        if (!options) {
            throw new Error('Options not set');
        }

        if (!(typeof options === 'object')) {
            throw new Error('Options should be an opject');
        }

        this.endpoint = endpoint;

        this.options = options || {};
        this.options.consumerGroup = this.options.consumerGroup || '$Default';
        this.options.eventHubName = this.options.eventHubName || '';

        this.receivers = []; // Our receivers for the different partitions
    }

    async open(eventEmitter) {
        if (this.client) {
            return;
        }

        this.client = eventHubClient.fromConnectionString(this.endpoint, this.options.eventHubName);
        this.eventEmitter = eventEmitter;

        console.log('[Stream] Opening');
        await this.client.open();
        console.log('[Stream] Getting Partitions');
        const partitionIds = await this.client.getPartitionIds();
        console.log(`[Stream] Got Partitions: ${partitionIds}`);

        // For each partition, create a receiver and bind the handlers
        for (let partitionId in partitionIds) {
            let receiver = await this.client.createReceiver(this.options.consumerGroup, partitionId, { 'startAfterTime': Date.now() });
            receiver.on('errorReceived', (error) => this.receiverOnErrorReceiver(partitionId, error));
            receiver.on('message', (message) => this.receiverOnMessage(partitionId, message));

            this.receivers.push(receiver);
            console.log(`[Stream][Partition - ${partitionId}] Receiver Created`);
        }

        console.log('[StreamEventHub] Stream Opened');
    }

    receiverOnErrorReceiver(partitionId, err) {
        console.log(`[Stream][Partition - ${partitionId}] Error: ${err.message}`)
    }

    receiverOnMessage(partitionId, message) {
        // console.log(`[Stream][Partition - ${partitionId}] Message: ${JSON.stringify(message.body)}`);
        this.eventEmitter.emit('stream_message_received', JSON.stringify(message.body));
    }

    close() {
        // Close the eventhub
        this.client.close(); 

        // Release variables for garbage collection
        this.receivers = null;
        this.client = null;
    }
}

module.exports = Stream;