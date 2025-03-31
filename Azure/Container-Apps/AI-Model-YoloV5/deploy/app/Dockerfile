FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

WORKDIR /app
ADD code/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

WORKDIR /app
ADD code/ /app

EXPOSE 5000

CMD ["python", "main.py", "--port=5000"]