const redis = require('redis'); // Note: Should become a permanent storage later, now in memory
const redisClient = redis.createClient();

class HashSet {
  async get(key) {
    return new Promise((resolve, reject) => {
      redisClient.get(key, (err, reply) => {
        if (err) {
          throw err;
        }

        return resolve(JSON.parse(reply));
      });
    })
  }

  async set(key, val) {
    return new Promise((resolve, reject) => {
      // @TODO: CHECK IF TYPEOF OBJECT
      redisClient.set(key, JSON.stringify(val));
      return resolve();
    });
  }
}

module.exports = HashSet;