const azureStorage = require('azure-storage');

class AzureBlobQueueStorage {
    constructor(storageAccountName, storageAccessKey) {
        this.queueService = azureStorage.createQueueService(storageAccountName, storageAccessKey);
    }

    async sendMessage(queueName, message) {
        await this.createQueueIfNotExists(queueName);

        return new Promise((resolve, reject) => {
            queueService.createMessage(queueName, JSON.stringify(message), (err, result, res) => {
                if (err) {
                    console.error(`[Azure - BlobQueueStorage] An error occurred: ${JSON.stringify(err)}`);
                    return reject(err);
                }
            
                console.log(`[Azure - BlobQueueStorage] Sent: ${JSON.stringify(message)}`);
                return resolve(result);
            });
        })
    }

    async createQueueIfNotExists(queueName) {
        return new Promise((resolve, reject) => {
            queueService.createQueueIfNotExists(queueName, (err, result, res) => {
                if (err) {
                    console.error(err);
                    return reject(err);
                }
              
                if (result.created) {
                    console.log(`[Azure - BlobQueueStorage] Queue ${queueName} did not exist, created it`);
                }

                return resolve();
            });
        })
    }
}

module.exports = AzureBlobQueueStorage;