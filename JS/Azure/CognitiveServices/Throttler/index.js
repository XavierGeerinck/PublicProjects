const delay = require('delay');

/**
 * Example usage:
 * 
 * const start = async () => {
 *     // Create our throttler
 *     const throttler = new Throttler(calls, 10, 1000);
 *     await throttler.execute();
 * }
 *
 * start();
 *
 */
class Throttler {
    /**
     * 
     * @param {array} calls array of functions to be executed in batches of rateLimitCount every rateLimitCount
     * 
     * Example of how to create this array:
     * 
     * calls.push((isDone) => {
     *    isDone(); // Is our call done executing and did we process the result?
     * });
     *
     * @param {integer} rateLimitCount how many calls do we perform each time?
     * @param {integer} rateLimitDelay What is the delay to wait between each batch of calls?
     */
    constructor(calls = [], rateLimitCount = 10, rateLimitDelay = 1000) {
        this.calls = calls;
        this.callsCount = calls.length;
        this.rateLimitDelay = rateLimitDelay;
        this.rateLimitCount = rateLimitCount;
        this.currentCallIndex = 0;
    }

    async execute() {
        // Go over them in a throttled way
        while (this.calls.length > 0) {
            console.log(`[${Math.abs(this.calls.length - this.callsCount)}/${this.callsCount}] Performing`);
            let callsToExecute = this.calls.slice(0, this.rateLimitCount);
            this.calls = this.calls.slice(this.rateLimitCount, this.calls.length);

            // Wrap our call in a promise and wait till cb is called
            // Note: We can also implement the promise earlier, but easier here for compatibility with older code
            let promises = [];
            callsToExecute.forEach((callIsDoneCallback) => {
                promises.push(new Promise((resolve, reject) => callIsDoneCallback(resolve, this.currentCallIndex)));
                this.currentCallIndex++;
            });

            // Wait for all our alls to be done
            await Promise.all(promises);

            // Throttle time @todo: this is not the exact time but an artificial time, we actually need the time between latest call and finish.
            await delay(this.rateLimitDelay);
        }
    }
}

module.exports = Throttler;