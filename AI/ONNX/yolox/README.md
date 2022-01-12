# 

## Prerequisites

### Ensure Nvidia CUDA and cuDNN are installed 

```bash
nvidia-smi
nvcc --version
```

#### Installing CUDA on WSL 2

```bash
# View all: https://developer.nvidia.com/cuda-toolkit-archive
# View ONNX Supported: https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#requirements
CUDA_VERSION_MAJOR=11
CUDA_VERSION_MINOR=4
CUDA_VERSION_PATCH=0

# Install CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.5.1/local_installers/cuda-repo-wsl-ubuntu-${CUDA_VERSION_MAJOR}-${CUDA_VERSION_MINOR}-local_${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}.${CUDA_VERSION_PATCH}-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-${CUDA_VERSION_MAJOR}-${CUDA_VERSION_MINOR}-local_${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}.${CUDA_VERSION_PATCH}-1_amd64.deb
sudo apt-key add /var/cuda-repo-wsl-ubuntu-${CUDA_VERSION_MAJOR}-${CUDA_VERSION_MINOR}-local/7fa2af80.pub
sudo apt-get update
sudo apt-get -y install cuda

# Add CUDA to Path
# https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#post-installation-actions
# Note: add those to ~/.bashrc at the bottom
export PATH=/usr/local/cuda-11.5/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda-11.5/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

```

> [Previous CUDA Versions](https://developer.nvidia.com/cuda-toolkit-archive)

## Installing TensorRT

> Note: we prefer TensorRT since it's easier to install than cuDNN (requires login)

```bash
# https://developer.nvidia.com/nvidia-tensorrt-download
```

## Installing cuDNN

> Both TensorRT and cuDNN require a login

```bash
# https://docs.nvidia.com/deeplearning/cudnn/install-guide/index.html#install-zlib-linux
sudo apt-get install zlib1g

# 1. Login at: https://developer.nvidia.com/cudnn
# 2. Go to: https://developer.nvidia.com/rdp/cudnn-archive
# 3. Download cuDNN that fits ONNX (https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html) for Linux x86_64
# 4. Extract through `tar -xvf cudnn-11.4-linux-x64-v8.2.4.15.tgz`
# 5. Run the below
export LINK_CUDNN="https://developer.nvidia.com/compute/machine-learning/cudnn/secure/8.2.4/11.4_20210831/cudnn-11.4-linux-x64-v8.2.4.15.tgz"
wget $LINK_CUDNN
mkdir cudnn; tar -xvf cudnn-11.4-linux-x64-v8.2.4.15.tgz -C ./cudnn

cd cudnn/cuda
sudo cp include/cudnn*.h /usr/local/cuda/include 
sudo cp -P lib64/libcudnn* /usr/local/cuda/lib64 
sudo chmod a+r /usr/local/cuda/include/cudnn*.h /usr/local/cuda/lib64/libcudnn*
```


```bash
OS="wsl-ubuntu"
CUDA_VERSION_MAJOR=11
CUDA_VERSION_MINOR=4
CUDA_VERSION_PATCH=0
CUDNN_VERSION_MAJOR=8
CUDNN_VERSION_MINOR=2
CUDNN_VERSION_PATCH=4

wget https://developer.download.nvidia.com/compute/cuda/repos/${OS}/x86_64/cuda-${OS}.pin 

sudo mv cuda-${OS}.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/${OS}/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/${OS}/x86_64/ /"
sudo apt-get update
sudo apt-get install libcudnn8=${CUDNN_VERSION_MAJOR}.${CUDNN_VERSION_MINOR}.${CUDNN_VERSION_PATCH}-1+cuda${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}
sudo apt-get install libcudnn8-dev=${CUDNN_VERSION_MAJOR}.${CUDNN_VERSION_MINOR}.${CUDNN_VERSION_PATCH}-1+cuda${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}
```

## Running

```bash
# Create directories
mkdir model; mkdir images; mkdir output

# Download Model
wget -O ./model/yolox_l.onnx https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_l.onnx 

# Download Example
wget -O ./images/example.jpg https://www.ikea.com/ext/ingkadam/m/7f8f282fb240f466/original/PH179208-crop001.jpg?f=m

# Run
python src/main.py -m ./model/yolox_l.onnx -i ./images/example.jpg -o ./output -s 0.3 --input_shape 640,640
```