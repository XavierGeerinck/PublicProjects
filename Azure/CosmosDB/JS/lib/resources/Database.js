
const Resource = require('./Resource');
const HttpStatusCodes = require('../HttpStatusCodes');

class Database extends Resource {
    constructor(cosmosDB) {
        super(cosmosDB);

        // ResourceType, see: https://docs.microsoft.com/en-us/rest/api/documentdb/access-control-on-documentdb-resources#constructkeytoken
        this.resourceType = 'dbs';
    }

    async get(databaseName) {
        return super.executeMethod({
            method: 'GET',
            resourceLink: `/dbs/${databaseName}`, // Link the to resource (ex: /dbs/<db_name>)
        });
    }

    async create(databaseName) {
        return super.executeMethod({
            method: 'POST',
            resourceLink: '/dbs', // Link the to resource (ex: /dbs/<db_name>)
            body: {
                id: databaseName
            }
        });
    }

    async delete(databaseName) {
        return super.executeMethod({
            method: 'DELETE',
            resourceLink: `/dbs/${databaseName}`, // Link the to resource (ex: /dbs/<db_name>)
        });
    }

    async list() {
        return super.executeMethod({
            method: 'GET',
            resourceLink: '/dbs', // Link the to resource (ex: /dbs/<db_name>)
            isResourceLinkRelative: true
        });
    }

    async createIfNotExists(databaseName) {
        let database;
        
        try {
            database = await this.get(databaseName);
        } catch (e) {
            if (e.status === HttpStatusCodes.NOT_FOUND) {
                database = await this.create(databaseName);
            } else {
                throw e;
            }
        }

        return database;
    }
 }

module.exports = Database;
