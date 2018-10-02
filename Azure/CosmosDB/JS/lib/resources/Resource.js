const crypto = require('crypto');
const fetch = require('node-fetch');
const HttpStatusCodes = require('../HttpStatusCodes');

class Resource {
  constructor(cosmosDB) {
    this._cosmosDB = cosmosDB;
  }

  /**
   * 
   * @param {string} verb Example: GET/PUT/POST/DELETE/....
   * @param {string} resourceType Example: dbs, colls, docs, ...
   * @param {string} resourceLink ? Example: dbs/ToDoList/colls/Items/docs/cb2f81a4-b3cd-6cef-cbc5-c97678f1eef5
   * @param {string} masterKey Your Primary/Secondary key
   */
  getAuthorizationHeader(verb, resourceType, resourceLink) {
    const date = new Date().toUTCString();

    if (resourceLink.startsWith('/')) {
      resourceLink = resourceLink.substring(1, resourceLink.length);
    }

    if (resourceLink.endsWith(resourceType)) {
      resourceLink = resourceLink.substring(0, resourceLink.length - resourceType.length - 1); // The -1 is from the /
    }

    return {
      'Authorization': this.getAuthorizationTokenUsingMasterKey(verb, resourceType, resourceLink, date, this._cosmosDB.masterKey),
      'x-ms-version': '2017-02-22',
      'x-ms-date': date,
    }
  }

  getAuthorizationTokenUsingMasterKey(verb, resourceType, resourceLink, date, masterKey) {
    const key = new Buffer(masterKey, "base64");

    // console.log('Verb:' + verb);
    // console.log('ResourceType:' + resourceType);
    // console.log('ResourceLink:' + resourceLink);
    // console.log('Date:' + date);
    // console.log('MasterKey:' + masterKey);

    const text = (verb || "").toLowerCase() + "\n" +
      (resourceType || "").toLowerCase() + "\n" +
      (resourceLink || "") + "\n" +
      date.toLowerCase() + "\n" +
      "" + "\n";

    const body = new Buffer(text, "utf8");
    const signature = crypto.createHmac("sha256", key).update(body).digest("base64");
    const MasterToken = "master";
    const TokenVersion = "1.0";

    return encodeURIComponent("type=" + MasterToken + "&ver=" + TokenVersion + "&sig=" + signature);
  }

  /**
   * 
   * @param [spec.method=''] Request Method (POST, GET, DELETE, PUT)
   * @param [spec.resourceLink=''] The path excluding the resourceType (ex: when full path is dbs/{db_name} then just {db_name}) 
   * @param [spec.body={}] (optional) The body to use when using a POST request
   * @param [spec.headers={}] (optional) Extra headers to add
   */
  async executeMethod(spec) {
    let resourceLink = spec.resourceLink;

    if (spec.isResourceLinkRelative) {
      resourceLink = spec.resourceLink.replace();
    }

    const authorizationHeader = this.getAuthorizationHeader(spec.method, this.resourceType, spec.resourceLink);

    let fetchOptions = {
      method: spec.method,
      headers: { ...authorizationHeader, ...spec.headers },
    }

    if (spec.body) {
      fetchOptions.body = JSON.stringify(spec.body);
    }

    const response = await fetch(`${this._cosmosDB.baseUrl}${spec.resourceLink}`, fetchOptions);
    return this.handleResponse(response);
  }

  async handleResponse(response) {
    switch (response.status) {
      case HttpStatusCodes.NO_CONTENT:
        return;
      case HttpStatusCodes.SUCCESS:
      case HttpStatusCodes.CREATED:
        return await response.json();
      case HttpStatusCodes.NOT_FOUND:
      case HttpStatusCodes.CONFLICT:
      default:
        let result = await response.json();

        throw {
          url: response.url,
          status: response.status,
          statusText: response.statusText,
          message: result.message,
        };
    }
  }
}

module.exports = Resource;