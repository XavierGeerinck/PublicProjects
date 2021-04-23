export default {
  third_party: {
    dapr: {
      url: process.env.DAPR_HOST || "127.0.0.1",
      port: process.env.DAPR_PORT || "3500"
    }
  },
};
