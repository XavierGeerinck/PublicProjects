#!/bin/bash
# Set DNS first since else we can't apt update
echo "Setting DNS"
cat << EOF > /etc/resolv.conf
# Created on $(date)
nameserver 1.1.1.1
nameserver 1.0.0.1
EOF

# Jetson Nano Cleanup
sudo apt-get update

echo "Cleaning Up Jetson Nano image - Base Cleaning"
sudo apt autoremove -y
sudo apt clean
sudo apt remove thunderbird libreoffice-* -y

echo "Cleaning Up Jetson Nano image - Dev Cleaning"
sudo rm -rf /usr/local/cuda/samples \
    /usr/src/cudnn_samples_* \
    /usr/src/tensorrt/data \
    /usr/src/tensorrt/samples \
    /usr/share/visionworks* ~/VisionWorks-SFM*Samples \
    /opt/nvidia/deepstream/deepstream*/samples	

echo "Cleaning Up Jetson Nano image - Deep Cleaning"
sudo apt-mark manual cuda-command-line-tools-10-0 cuda-compiler-10-0 cuda-cufft-10-0 cuda-cufft-dev-10-0 cuda-cuobjdump-10-0 cuda-cupti-10-0 cuda-curand-10-0 cuda-curand-dev-10-0 cuda-cusolver-10-0 cuda-cusolver-dev-10-0 cuda-cusparse-10-0 cuda-cusparse-dev-10-0 cuda-gdb-10-0 cuda-gpu-library-advisor-10-0 cuda-libraries-dev-10-0 cuda-memcheck-10-0 cuda-misc-headers-10-0 cuda-nsight-compute-addon-l4t-10-0 cuda-nvcc-10-0 cuda-nvdisasm-10-0 cuda-nvgraph-10-0 cuda-nvgraph-dev-10-0 cuda-nvml-dev-10-0 cuda-nvprof-10-0 cuda-nvprune-10-0 cuda-nvrtc-10-0 cuda-nvrtc-dev-10-0 cuda-nvtx-10-0 cuda-tools-10-0 cuda-documentation-10-0 cuda-samples-10-0 cuda-toolkit-10-0
sudo apt remove -y x11-common x11proto-* mesa-* libgl1* libglapi-mesa libgles* libglu1-mesa libglvnd* libglx* libx11-* libwayland-*
sudo apt remove -y --purge ubuntu-desktop gdm3