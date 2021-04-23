const redis = require('redis'); // Note: Should become a permanent storage later, now in memory

class Redis {
  constructor() {
    this.client = redis.createClient();
  }

  async get(key) {
    return new Promise((resolve, reject) => {
      this.client.get(key, (err, reply) => {
        if (err) {
          throw err;
        }

        return resolve(reply);
      });
    })
  }
}

module.exports = Redis;