
const Resource = require('./Resource');
const HttpStatusCodes = require('../HttpStatusCodes');

class Collection extends Resource {
    constructor(cosmosDB) {
        super(cosmosDB);

        // ResourceType, see: https://docs.microsoft.com/en-us/rest/api/documentdb/access-control-on-documentdb-resources#constructkeytoken
        this.resourceType = 'colls';
    }

    async get(databaseName, collectionName) {
        return super.executeMethod({
            method: 'GET',
            resourceLink: `/dbs/${databaseName}/colls/${collectionName}`, // Link the to resource (ex: /dbs/<db_name>)
        });
    }

    async create(databaseName, collectionName) {
        return super.executeMethod({
            method: 'POST',
            resourceLink: `/dbs/${databaseName}/colls`, // Link the to resource (ex: /dbs/<db_name>)
            body: {
                id: collectionName
            }
        });
    }

    async delete(databaseName, collectionName) {
        return super.executeMethod({
            method: 'DELETE',
            resourceLink: `/dbs/${databaseName}/colls/${collectionName}`, // Link the to resource (ex: /dbs/<db_name>)
        });
    }

    async list(databaseName) {
        return super.executeMethod({
            method: 'GET',
            resourceLink: `/dbs/${databaseName}/colls`, // Link the to resource (ex: /dbs/<db_name>)
            isResourceLinkRelative: true
        });
    }

    async createIfNotExists(databaseName, collectionName) {
        let database;
        
        try {
            database = await this.get(databaseName, collectionName);
        } catch (e) {
            if (e.status === HttpStatusCodes.NOT_FOUND) {
                database = await this.create(databaseName, collectionName);
            } else {
                throw e;
            }
        }

        return database;
    }

    async truncate(databaseName, collectionName) {
        await this.delete(databaseName, collectionName);
        await this.create(databaseName, collectionName);
        return {
            success: true
        }
    }
 }

module.exports = Collection;
