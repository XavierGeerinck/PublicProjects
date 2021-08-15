const crypto = require('crypto');

function createSharedAccessToken(uri, saName, saKey) { 
    if (!uri || !saKey) { 
        console.error(`Example for IoT Hub Device Message:`)
        console.error(`node ./generate-sas-token.js URI saKey`);
        console.error(`node ./generate-sas-token.js poc-kortrijk-peoplecounting.azure-devices.net/devices/poc-knokke-sorama-2_v2 saKey`);
        throw "Missing required parameter"; 
    } 
    
    var encoded = encodeURIComponent(uri); 
    var now = new Date(); 
    var week = 60 * 60 * 24 * 7;
    var ttl = Math.round(now.getTime() / 1000) + week;
    var signature = encoded + '\n' + ttl; 
    var signatureUTF8 = signature.toString('utf8');
    var hash = crypto.createHmac('sha256', saKey).update(signatureUTF8).digest('base64'); 
    
    if (saName) {
        return `SharedAccessSignature sr=${encoded}&sig=${encodeURIComponent(hash)}&se=${ttl}&skn=${saName}`;
    } else {
        return `SharedAccessSignature sr=${encoded}&sig=${encodeURIComponent(hash)}&se=${ttl}`;
    } 
}

const uri = process.argv[2];
const saKey = process.argv[3];
const saName = process.argv[4];

console.log(`URI: ${uri}`);
console.log(`saName: ${saName}`);
console.log(`saKey: ${saKey}`);

console.log(`SAS Token: ${createSharedAccessToken(uri, saName, saKey)}`);