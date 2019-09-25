const fetch = require('node-fetch');
const fs = require('fs');
const util = require('util');

const readFile = util.promisify(fs.readFile);

// Based on https://github.com/Microsoft/BotFramework-Samples/blob/master/StackOverflow-Bot/StackBot/lib/bingsearchclient.js
class CognitiveServiceAnalyzeImage {
  constructor(apiKey, opts) {
    if (!apiKey) throw new Error('apiKey is required');

    this.apiKey = apiKey;
    this.baseUrl = "https://westeurope.api.cognitive.microsoft.com/vision/v2.0/";
  }

  /**
   * An util to help you get the binary data of an image
   * @param {string} imagePath 
   */
  async readImageByPath(imagePath) {
    const imageBinary = await readFile(imagePath);
    const fileData = imageBinary.toString('hex');
    const result = [];
    for (let i = 0; i < fileData.length; i += 2) {
      result.push(parseInt(`${fileData[i]}${fileData[i + 1]}`, 16))
    }
    return new Buffer(result);
  }

  async analyzeImage(imageBinary, opts) {
    const url = this.baseUrl + "analyze/" + "?"
      + "returnFaceId=true"
      + "&visualFeatures=Tags,Description,Faces,Color"
      + "&returnFaceLandmarks=false"
      + "&returnFaceAttributes=age,gender,headPose,smile,facialHair,glasses,emotion,hair,makeup,occlusion,accessories,blur,exposure,noise";

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          "Content-Type": "application/octet-stream",
          "Ocp-Apim-Subscription-Key": this.apiKey
        },
        body: imageBinary
      });

      const json = await response.json();
      return Promise.resolve(json);
    } catch (e) {
      return Promise.reject(e);
    }
  }
}

module.exports = CognitiveServiceAnalyzeImage;
