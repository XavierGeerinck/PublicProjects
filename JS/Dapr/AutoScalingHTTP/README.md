# Dapr - Auto Scaling HTTP

## Installation

## Building and Pushing to Docker

docker build -t thebillkidy/dapr-autoscaling-http-gateway ./Gateway
docker build -t thebillkidy/dapr-autoscaling-http-worker ./Worker

docker push thebillkidy/dapr-autoscaling-http-gateway
docker push thebillkidy/dapr-autoscaling-http-worker

## Running

dapr run --app-id gateway --app-port 5000 --dapr-http-port 5001 --components-path ../components npm run start:dev
dapr run --app-id worker --app-port 3000 --dapr-http-port 3501 --components-path ../components npm run start:dev