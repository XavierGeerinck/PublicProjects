// const request = require('request');
// const crypto = require('crypto');
// const fetch = require('node-fetch');
// const HttpStatusCodes = { NOTFOUND: 404 };

// class CosmosDBWrapper {
//     constructor(client, accountName, primaryKey) {
//         this.client = client;
//         this.baseUrl = `https://${accountName}.documents.azure.com`;
//         this.primaryKey = primaryKey;
//     }

//     /**
//      * 
//      * @param {string} verb Example: GET/PUT/POST/DELETE/....
//      * @param {string} resourceType Example: dbs, colls, docs, ...
//      * @param {string} resourceLink ? Example: dbs/ToDoList/colls/Items/docs/cb2f81a4-b3cd-6cef-cbc5-c97678f1eef5
//      * @param {string} masterKey Your Primary/Secondary key
//      */
//     getAuthorizationHeader(verb, resourceType, resourceLink) {
//         const date = new Date().toUTCString();

//         return {
//             'Authorization': this.getAuthorizationTokenUsingMasterKey(verb, resourceType, resourceLink, date, this.primaryKey),
//             'x-ms-version': '2017-02-22',
//             'x-ms-date': date,
//         }
//     }

//     getAuthorizationTokenUsingMasterKey(verb, resourceType, resourceLink, date, masterKey) {
//         const key = new Buffer(masterKey, "base64");

//         const text = (verb || "").toLowerCase() + "\n" +   
//                      (resourceType || "").toLowerCase() + "\n" +   
//                      (resourceLink || "") + "\n" +   
//                      date.toLowerCase() + "\n" +   
//                      "" + "\n";  

//         const body = new Buffer(text, "utf8");  
//         const signature = crypto.createHmac("sha256", key).update(body).digest("base64");  
//         const MasterToken = "master";  
//         const TokenVersion = "1.0";  

//         return encodeURIComponent("type=" + MasterToken + "&ver=" + TokenVersion + "&sig=" + signature);  
//     }

//     handleResponse(response) {
//         if (response.code) {
//             throw response;
//         }

//         return response;
//     }

//     async getDatabase(databaseName) {
//         // Generate an authorization header so we can connect to it, this needs the Verb (GET, POST, ...) 
//         // and the type stating what we want (dbs, colls, docs, ...)
//         const authorizationHeader = this.getAuthorizationHeader('GET', "dbs", `dbs/${databaseName}`);

//         const response = await fetch(`${this.baseUrl}/dbs/${databaseName}`, {
//             method: 'GET',
//             headers: { ...authorizationHeader }
//         });

//         return this.handleResponse(await response.json());
//     }

//     async createDatabase(databaseName) {
//         // Generate an authorization header so we can connect to it, this needs the Verb (GET, POST, ...) 
//         // and the type stating what we want (dbs, colls, docs, ...)
//         const authorizationHeader = this.getAuthorizationHeader('POST', "dbs", '');

//         const response = await fetch(`${this.baseUrl}/dbs`, {
//             method: 'POST',
//             body: JSON.stringify({
//                 id: databaseName
//             }),
//             headers: { ...authorizationHeader }
//         });
//         console.log(response.status);
//         return this.handleResponse(await response.json());
//     }

//     async createDatabaseIfNotExists(databaseName) {
//         let database;
        
//         try {
//             database = this.getDatabase(databaseName);
//         } catch (e) {
//             console.log(e);
//             if (e.code === 'NotFound') {
//                 database = this.createDatabase(databaseName);
//             } else {
//                 throw e;
//             }
//         }

//         return database;
//     }
// }

// module.exports = CosmosDBWrapper;
