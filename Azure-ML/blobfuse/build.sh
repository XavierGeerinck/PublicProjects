docker build -t azure-blobfuse -f Dockerfile .
docker run -it --rm --cap-add=SYS_ADMIN --device=/dev/fuse --security-opt apparmor:unconfined azure-blobfuse /bin/bash