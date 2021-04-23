import { EventEmitter } from "events";

class Stream {
    stream: any;
    bus: EventEmitter;
    timeoutFunction: ReturnType<typeof setTimeout>;
    
    constructor(stream) {
        if (!stream) {
            throw new Error('Stream not set');
        }

        if (!(typeof stream === 'object')) {
            throw new Error('Stream should be an opject');
        }
        
        this.stream = stream;
        this.bus = new EventEmitter();
    }

    // Every stream implementation gets the EventEmitter passed
    // Here they should call the `stream_message_received` event to state that an event was received
    async open() {
        await this.stream.open(this.bus);
    }

    async receiveOneMessageAndClose(options) {
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
            this.close();
            throw e;
        }

        console.log('resolved');
        this.close();
        return message;
    }

    close() {
        console.log('[Stream] Closing stream');
        this.stream.close();
        this.bus.removeAllListeners(); // Close our EventEmitter listeners

        if (this.timeoutFunction) {
            clearTimeout(this.timeoutFunction); // Remove our timeout waiter!
        }
    }
}

module.exports = Stream;