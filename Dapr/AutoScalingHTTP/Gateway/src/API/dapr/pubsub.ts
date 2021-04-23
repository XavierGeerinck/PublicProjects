// https://github.com/dapr/docs/blob/master/reference/api/state_api.md

import fetch from 'node-fetch';
import express from 'express';

export default class DaprPubSub {
  url: string;
  urlDapr: string;
  port: number;

  constructor(daprUrl, daprPort) {
    this.url = daprUrl || "127.0.0.1";
    this.port = daprPort || 3500;

    if (!this.url.startsWith('http://') && !this.url.startsWith('https://')) {
      this.url = `http://${this.url}`;
    }

    this.urlDapr = `${this.url}:${this.port}/v1.0`;
  }

  async publish(pubSubName: string, topic: string, body: object = {}): Promise<void> {
    const r = await fetch(`${this.urlDapr}/publish/${pubSubName}/${topic}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })
  }

  subscribe(app, pubSubName: string, topic: string, cb) {
    app.use(express.json({ type: 'application/*+json' }))

    app.get('/dapr/subscribe', (req, res) => {
      res.json([
        {
          pubsubname: pubSubName,
          topic,
          route: `route-${topic}`
        }
      ]);
    });

    app.post(`/route-${topic}`, (req, res) => {
      cb(req, res);
    });
  }
}