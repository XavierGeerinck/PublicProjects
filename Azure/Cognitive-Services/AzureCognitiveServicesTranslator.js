const fetch = require('node-fetch');
const fs = require('fs');
const util = require('util');

// Based on https://docs.microsoft.com/en-us/azure/cognitive-services/translator/quickstart-nodejs-translate
class CognitiveServiceTranslator {
  constructor(apiKey, opts) {
    if (!apiKey) throw new Error('apiKey is required');

    this.apiKey = apiKey;
    this.baseUrl = "https://api.cognitive.microsofttranslator.com/translate";
  }

  async translate(text, translateToLocales = []) {
    const url = this.baseUrl + "?"
      + "api-version=3.0"
      + '&to=' + translateToLocales.join('&to=');

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
          "Ocp-Apim-Subscription-Key": this.apiKey
        },
        body: JSON.stringify([{
          'Text': text
        }])
      });

      const json = await response.json();
      return Promise.resolve(json);
    } catch (e) {
      return Promise.reject(e);
    }
  }
}

module.exports = CognitiveServiceTranslator;
