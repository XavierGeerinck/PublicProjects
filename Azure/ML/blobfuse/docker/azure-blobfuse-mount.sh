#!/bin/bash
set -euo pipefail
set -o errexit
set -o errtrace
IFS=$'\n\t'

# Configuring temporary path for caching or streaming
# finally we create an empty directory for mounting the blob container (/root/azure-storage)
mkdir /tmp/blobfuse \
    && chown root /tmp/blobfuse \
    && mkdir -p /root/azurestorage

# Authorize access to your storage account and mount our blobstore
# Example: https://github.com/Azure/azure-storage-fuse/blob/main/sampleFileCacheConfig.yaml
# Full Config: https://github.com/Azure/azure-storage-fuse/blob/main/setup/baseConfig.yaml
blobfuse2 mount /root/azurestorage --config-file=/docker/azure-blobfuse-config.yaml

# run the command passed to us
exec "$@"