const HttpStatusCodes = { NOTFOUND: 404 };

const resources = {
  Database: require('./resources/Database'),
  Collection: require('./resources/Collection'),
  Document: require('./resources/Document'),
}

class CosmosDB {
  constructor(accountName, primaryKey) {
    this.packageVersion = require('../package.json').version;
    this.baseUrl = `https://${accountName}.documents.azure.com`;
    this.masterKey = primaryKey;
    this.accountName = accountName;

    this.initResources();
  }

  initResources() {
    for (var name in resources) {
      this[name.toLowerCase()] = new resources[name](this);
    }
  }
}

module.exports = CosmosDB;
