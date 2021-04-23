import IStream from "../stream/IStream";

const config = require('../config');
const Stream = require('../stream/stream');
const StreamEventHub = require('../stream/streamEventHub');
const StreamSocket = require('../stream/streamSocket');

exports.sampleStreamEventHub = async (req, h) => {
    // @TODO: Make it dynamic through a post body param
    const streamEventHub = new StreamEventHub(config.getConnectionString(), { eventHubName: config.eventHub });
    return exports.sampleStream(streamEventHub, req, h);
}

exports.sampleStreamSocket = async (req, h) => {
    const host = req.query.host;
    const port = req.query.port;

    if (!host) {
        return { error: "MISSING_PARAMETER", parameter: 'host' }
    }

    if (!port) {
        return { error: "MISSING_PARAMETER", parameter: 'port' }
    }

    const streamSocket = new StreamSocket(host, port);
    return exports.sampleStream(streamSocket, req, h);
}

exports.sampleStream = async (streamSocket: IStream, req, h) => {
    const stream = new Stream(streamSocket);

    await stream.open();

    console.log('[Receiver] Awaiting Message from Stream');
    try {
        const message = await stream.receiveOneMessageAndClose({ timeout: 10000 });
        console.log('[Receiver] Received Message');
        console.log(message.toString('utf8'));

        return {
            event: {
                raw: message.toString()
            }
        }
    } catch (e) {
        console.log('triggered')
        console.error(e);
    }
}