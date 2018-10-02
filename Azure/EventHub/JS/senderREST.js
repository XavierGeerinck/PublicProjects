const config = require('./config');
const fetch = require('node-fetch');
const utf8 = require('utf8');
const crypto = require('crypto');
const uuidv4 = require('uuid/v4');
const hrstart = process.hrtime();

const createSharedAccessToken = (uri, saName, saKey) => { 
    if (!uri || !saName || !saKey) { 
        throw "Missing required parameter"; 
    }

    var encoded = encodeURIComponent(uri); 
    var now = new Date(); 
    var week = 60*60*24*7;
    var ttl = Math.round(now.getTime() / 1000) + week;
    var signature = encoded + '\n' + ttl; 
    var signatureUTF8 = utf8.encode(signature); 
    var hash = crypto.createHmac('sha256', saKey).update(signatureUTF8).digest('base64'); 
    return 'SharedAccessSignature sr=' + encoded + '&sig=' + encodeURIComponent(hash) + '&se=' + ttl + '&skn=' + saName; 
}

const performCall = (body, cb) => {
    fetch(`https://${config.eventHubUrl}/myeventhub/messages?timeout=60&api-version=2014-01`, {
        method: 'POST',
        headers: {
            "Authorization": createSharedAccessToken(config.eventHubUrl, config.eventHubSharedAccessKeyName, config.eventHubSharedAccessKey)
        },
        body: JSON.stringify(body)
    })
    .then((res) => res.text())
    .then((body) => {
        if (!cb) {
            return;
        }
        
        cb(body);
    })
    .catch((e) => console.log(e));
}

let counter = 0;

for (var i = 0; i < 100; i++) {
    performCall({ 
        "clientId": uuidv4(), 
        "a": "test1", 
        "b": "test2", 
        "c": "test3" 
    }, () => {
        counter++;
        console.log(`Did ${counter} calls`);

        if (counter == 2000) {
            const hrend = process.hrtime(hrstart);
            console.info("Execution time: %dms", end);
            console.info("Execution time (hr): %ds %dms", hrend[0], hrend[1]/1000000);
        }
    });
}


