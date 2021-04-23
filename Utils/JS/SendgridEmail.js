const sendgrid = require('@sendgrid/mail');

class SendgridMail {
    constructor(apiKey) {
        this.sendgrid = sendgrid;
        this.sendgrid.setApiKey(apiKey)
    }

    // Returns promise, if fails error is thrown
    // More info: https://github.com/sendgrid/sendgrid-nodejs/blob/master/use-cases/success-failure-errors.md
    async sendMail(to, from, subject, html) {
        return this.sendgrid.send({
            to,
            from,
            subject,
            html
        });
    }
}

module.exports = SendgridMail;