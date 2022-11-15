#!/bin/bash
# https://learn.microsoft.com/en-gb/azure/iot-edge/how-to-vs-code-develop-module?view=iotedge-1.4&tabs=node&pivots=iotedge-dev-cli

PLATFORM=arm32v7
ACR_REPO=YOUR_ACR_REPO

# Initialize qemu
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Generate the config from the deployment template
# More info: https://learn.microsoft.com/en-us/azure/iot-edge/module-composition?view=iotedge-1.4
iotedgedev solution genconfig --file deployment.template.json \
    --platform $PLATFORM

# Build and push your modules for the target architecture
for d in modules/*; do
    MODULE_DIR=$d
    MODULE_NAME=$(echo $d | cut -d "/" -f 2)
    MODULE_NAME_LOWER=$(echo $MODULE_NAME | tr '[:upper:]' '[:lower:]')

    echo "building $ACR_REPO.azurecr.io/$MODULE_NAME_LOWER"
    docker buildx build --push --platform linux/$PLATFORM \
        -t $ACR_REPO.azurecr.io/$MODULE_NAME_LOWER:0.0.1-arm32v7 \
        -f $MODULE_DIR/Dockerfile.$PLATFORM \
        $MODULE_DIR
done

# Push to the device
# similar to: az iot edge set-modules --hub-name my-iot-hub --device-id my-device --content ./deployment.debug.template.json --login "HostName=my-iot-hub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=<SharedAccessKey>"
iotedgedev solution deploy --file config/deployment.arm32v7.json