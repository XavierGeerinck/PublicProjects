#!/bin/bash

# Put Jetson nano in 4W Power Mode
# https://forums.developer.nvidia.com/t/nvpmodel-and-jetson-clocks/58659/4
# it boosts the clock
sudo nvpmodel -m 0

# Remove need for sudo during Docker
sudo usermod -aG docker ${USER}

# Configure the Libraries
if [ -n "${BASH_VERSION-}" ]; then
    if [[ $PATH != */usr/local/cuda/bin* ]]; then
        export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
    fi
    if [[ $LD_LIBRARY_PATH != */usr/local/cuda/lib64* ]]; then
        export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
    fi
fi

# Configure Docker to use Nvidia
cat << EOF > /etc/docker/daemon.json
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
EOF