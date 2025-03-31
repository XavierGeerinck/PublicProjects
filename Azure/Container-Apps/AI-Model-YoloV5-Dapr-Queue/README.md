# Azure Container Apps - AI Model - YoloV5

## Usage

### Local

> Note: A service bus queue should exist in Azure and be configured in ./example/components/my-queue.yaml

```bash
# Send 5 Events to Service Bus Queue
dapr run --app-id=send-events --app-protocol http --components-path=./example/components python example/send.py 5

# Start Server to Process the Events
cd app/code/src
dapr run --app-id=yolox --app-protocol http --components-path=../../../example/components -- uvicorn main:app --host 0.0.0.0 --port 5000
```

### Cloud

```bash
pulumi up \                                                                                                      
    --stack demo-cae-yolox \
    -c glb-location=northeurope \
    -c glb-project-name=demo-cae-yolox \
    -c glb-project-env=prd \
    -c sb-topics="worker-items"
```