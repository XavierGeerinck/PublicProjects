FROM python:3.8-slim-buster

WORKDIR /code

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

# Install PyTorch
RUN pip install torch==1.9.0+cpu torchvision==0.10.0+cpu torchaudio==0.9.0 -f https://download.pytorch.org/whl/torch_stable.html

# Install Requirements
ADD code/requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt

# Install Source
ADD code/ /code

# Run Uvicorn on the src dir
WORKDIR /code/src
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000" ]