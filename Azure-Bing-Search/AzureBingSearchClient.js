const fetch = require('node-fetch');

// Based on https://github.com/Microsoft/BotFramework-Samples/blob/master/StackOverflow-Bot/StackBot/lib/bingsearchclient.js
class BingSearchClient {
    constructor(key) {
        if (!key) throw new Error('bingSearchKey is required');
    
        this.bingSearchKey = key;
        this.bingSearchCount = 50;
        this.bingSearchMkt = "en-us";
        this.bingSearchBaseUrl = "https://api.cognitive.microsoft.com/bing/v7.0/search";
        this.bingSearchMaxSearchStringSize = 150;
    }

    get(search, offset = 0, cb) {
        return new Promise((resolve, reject) => { 
            if (!search) throw new Error('Search text is required');
            cb = cb || (() => {});
        
            const searchText = search.substring(0, this.bingSearchMaxSearchStringSize).trim();
        
            const url = this.bingSearchBaseUrl + "?"
                + `q=${encodeURIComponent(searchText)}`
                + `&count=${this.bingSearchCount}`
                //+ `&mkt=${this.bingSearchMkt}`
                + `&offset=${offset}&responseFilter=Webpages&safesearch=Strict`;

            try {
                fetch(url, {
                    method: 'GET',
                    headers: {
                        "Ocp-Apim-Subscription-Key": this.bingSearchKey
                    }
                })
                .then((response) => response.json())
                .then((json) => resolve(json));
            } catch (e) {
                return reject(e);
            }
        })
    }   
}

module.exports = BingSearchClient;