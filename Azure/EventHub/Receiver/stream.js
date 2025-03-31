const eventHubClient = require('azure-event-hubs').Client;
const EventEmitter = require('events'); 

class Stream {
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
        this.bus = new EventEmitter();
    }

    async open() {
        if (this.client) {
            return;
        }

        this.client = eventHubClient.fromConnectionString(this.endpoint, this.options.eventHubName);

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
    }

    receiverOnErrorReceiver(partitionId, err) {
        console.log(`[Stream][Partition - ${partitionId}] Error: ${err.message}`)
    }

    receiverOnMessage(partitionId, message) {
        // console.log(`[Stream][Partition - ${partitionId}] Message: ${JSON.stringify(message.body)}`);
        this.bus.emit('stream_message_received', message.body);
    }

    async receiveOneMessageAndClose(options) {
        if (!this.client) {
            throw new Error('Stream is not open yet, open it with open()');
        }

        // Set options
        let timeout = options.timeout || 1000; // auto timeout if we are waiting longer than X ms
        console.log(`[Stream] Awaiting one message or until timeout of ${timeout}ms is reached`);

        // Smart way of waiting until we receive a message on the bus
        let message;
        try {
            message = await new Promise(async (resolve, reject) => {
                // Resolve if message received
                this.bus.once('stream_message_received', (message) => resolve(message));
                this.bus.once('stream_message_timeout', () => reject('Timeout reached, closing stream automatically'));

                this.timeoutFunction = setTimeout(() => this.bus.emit('stream_message_timeout'), timeout);
            });
        } catch (e) {
            if (this.client) {
                this.close();
            }

            throw e;
        }

        console.log('resolved');
        this.close();
        return message;
    }

    close() {
        console.log('[Stream] Closing stream');
        this.client.close(); // Close the eventhub
        this.bus.removeAllListeners(); // Close our EventEmitter listeners

        if (this.timeoutFunction) {
            clearTimeout(this.timeoutFunction); // Remove our timeout waiter!
        }

        // Release variables for garbage collection
        this.receivers = null;
        this.client = null;
    }
}

module.exports = Stream;