
const Resource = require('./Resource');
const HttpStatusCodes = require('../HttpStatusCodes');

class Collection extends Resource {
  constructor(cosmosDB) {
    super(cosmosDB);

    // ResourceType, see: https://docs.microsoft.com/en-us/rest/api/documentdb/access-control-on-documentdb-resources#constructkeytoken
    this.resourceType = 'docs';
  }

  async get(databaseName, collectionName, documentId) {
    return super.executeMethod({
      method: 'GET',
      resourceLink: `/dbs/${databaseName}/colls/${collectionName}/docs/${documentId}`, // Link the to resource (ex: /dbs/<db_name>)
    });
  }

  async create(databaseName, collectionName, document) {
    if (!document.id) {
      throw new Error("The key id is required in a document");
    }

    return super.executeMethod({
      method: 'POST',
      resourceLink: `/dbs/${databaseName}/colls/${collectionName}/docs`, // Link the to resource (ex: /dbs/<db_name>)
      body: document,
      isResourceLinkRelative: true
    });
  }

  async delete(databaseName, collectionName, documentId) {
    return super.executeMethod({
      method: 'DELETE',
      resourceLink: `/dbs/${databaseName}/colls/${collectionName}/docs/${documentId}`, // Link the to resource (ex: /dbs/<db_name>)
    });
  }

  async list(databaseName, collectionName) {
    return super.executeMethod({
      method: 'GET',
      resourceLink: `/dbs/${databaseName}/colls/${collectionName}/docs`, // Link the to resource (ex: /dbs/<db_name>)
      isResourceLinkRelative: true
    });
  }

  async query(databaseName, collectionName, query) {
    return super.executeMethod({
      method: 'POST',
      resourceLink: `/dbs/${databaseName}/colls/${collectionName}/docs`, // Link the to resource (ex: /dbs/<db_name>)
      body: query,
      headers: {
        'x-ms-documentdb-isquery': true,
        'x-ms-documentdb-query-enablecrosspartition': true,
        'Content-Type': 'application/query+json'
      }
    });
  }

  async createIfNotExists(databaseName, collectionName, document) {
    let database;

    try {
      database = await this.get(databaseName, collectionName, document.id);
    } catch (e) {
      if (e.status === HttpStatusCodes.NOT_FOUND) {
        database = await this.create(databaseName, collectionName, document);
      } else {
        throw e;
      }
    }

    return database;
  }
}

module.exports = Collection;
