#!/bin/bash
DAPR_GRPC_PORT="10001"
DAPR_HTTP_PORT="10002"
DAPR_PROTOCOL="http"
APP_ID="my-demo-application"
APP_PORT="10000"
DAPR_PUBSUB_NAME="my-pubsub"
DAPR_PUBSUB_TOPIC="worker-items"

dapr run \
    --app-port $APP_PORT \
    --app-id $APP_ID \
    --app-protocol $DAPR_PROTOCOL \
    --dapr-grpc-port $DAPR_GRPC_PORT \
    --dapr-http-port $DAPR_HTTP_PORT \
    --dapr-http-max-request-size 16 \
    --components-path ./deploy/development/components \
    ./start.sh \
        $APP_ID \
        $APP_PORT \
        $DAPR_PUBSUB_NAME \
        $DAPR_PUBSUB_TOPIC