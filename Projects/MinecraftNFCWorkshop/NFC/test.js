"use strict";
const mfrc522 = require("mfrc522-rpi");
//# Init WiringPi with SPI Channel 0
mfrc522.initWiringPi(0);

//# This loop keeps checking for chips. If one is near it will get the UID and authenticate
console.log("scanning...");
console.log("Please put chip or keycard in the antenna inductive zone!");
console.log("Press Ctrl-C to stop.");

setInterval(function(){

    //# reset card
    mfrc522.reset();

    //# Scan for cards
    let response = mfrc522.findCard();
    if (!response.status) {
        return;
    }
    console.log("Card detected, CardType: " + response.bitSize);

    //# Get the UID of the card
    response = mfrc522.getUid();
    if (!response.status) {
        console.log("UID Scan Error");
        return;
    }
    //# If we have the UID, continue
    const uid = response.data;
    console.log("Card read UID: %s %s %s %s", uid[0].toString(16), uid[1].toString(16), uid[2].toString(16), uid[3].toString(16));

    //# Select the scanned card
    const memoryCapacity = mfrc522.selectCard(uid);
    console.log("Card Memory Capacity: " + memoryCapacity);

    // Dump block i = 7
    let blockNo = 7;
    let blockClosingByte = 254;

    let blockRaw = mfrc522.getDataForBlock(blockNo).toString().split(",");
    console.log(blockRaw);
    let result = "";
    let i = 0;

    while (blockRaw[i] && blockRaw[i] != "0" && blockRaw[i] != blockClosingByte.toString() && i < 20) {
        i++;
        if (i == 0 || i == 1 || blockRaw[i] == blockClosingByte.toString()) {
            // Do nothing
        } else {
            result += String.fromCharCode(blockRaw[i]);
        }
    }

    console.log("Raw: " + blockRaw.join(","));
    console.log("Text: " + result);
}, 500);