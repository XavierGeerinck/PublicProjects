# https://hub.docker.com/r/nvidia/cuda/tags?page=1&name=20.04
FROM nvidia/cuda:11.7.1-base-ubuntu20.04

RUN apt update \
    && apt install -y wget curl software-properties-common apt-utils

# ================================================================================================================
# Provide BlobFuse v2 (https://docs.microsoft.com/en-us/azure/storage/blobs/blobfuse2-how-to-deploy)
# this will translate calls from Linux Filesystem to Azure Blob Storage 
# beside installing it, we need to perform 3 base actions
# - Configure a temporary path for caching or streaming
# - Create an empty directory for mounting the blob container
# - Authorize access to your storage account
# ================================================================================================================
# https://github.com/Azure/azure-storage-fuse/releases/download/blobfuse2-2.0.0-preview2/blobfuse2-2.0.0-preview.2-ubuntu-18.04-x86-64.deb
RUN apt install -y libfuse3-dev fuse3 \
    && wget https://github.com/Azure/azure-storage-fuse/releases/download/blobfuse2-2.0.0-preview2/blobfuse2-2.0.0-preview.2-ubuntu-20.04-x86-64.deb \
    && apt install ./blobfuse2-2.0.0-preview.2-ubuntu-20.04-x86-64.deb

# Authorize access to your storage account
# https://github.com/Azure/azure-storage-fuse/blob/main/sampleFileCacheConfig.yaml
ADD docker/azure-blobfuse-config.yaml docker/azure-blobfuse-config.yaml

# ================================================================================================================
# Other
# ================================================================================================================
# ...

# ================================================================================================================
# Configure Scripts
# ================================================================================================================
COPY docker/ /docker
RUN chmod 755 /docker/*.sh

# ================================================================================================================
# Configure Other
# ================================================================================================================
ADD ./ ./

ENTRYPOINT ["/docker/azure-blobfuse-mount.sh"]
