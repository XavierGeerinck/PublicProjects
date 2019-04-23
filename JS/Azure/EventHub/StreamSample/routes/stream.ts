const controller = require('../controllers/stream');

module.exports = (server) => {
    server.route({ method: 'GET', path: '/stream/eh', handler: controller.sampleStreamEventHub });
    server.route({ method: 'GET', path: '/stream/socket', handler: controller.sampleStreamSocket });
}