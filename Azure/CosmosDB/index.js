const CosmosDB = require('./lib/CosmosDB');

module.exports = function(accountName, key) {
  return new CosmosDB(accountName, key);
};
