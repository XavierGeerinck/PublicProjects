import io
from PIL import Image
import requests
import torch
import os
import json
import time

# Pydantic
from pydantic import BaseModel

# App Server
from fastapi import FastAPI
from dapr.ext.fastapi import DaprApp

# First load the model as we will always need this
print("Loading Model", flush=True)
model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
model.eval()

# Then we can initialize the App Service
app = FastAPI(title="ModelService")
dapr_app = DaprApp(app)

print("Initializing App", flush=True)
GLB_APP_ID = os.getenv("APP_ID", "")
GLB_APP_PORT = os.getenv("APP_PORT", "")
GLB_DAPR_PUBSUB_MODEL_NAME = os.getenv("DAPR_PUBSUB_MODEL_NAME", "")
GLB_DAPR_PUBSUB_MODEL_TOPIC = os.getenv("DAPR_PUBSUB_MODEL_TOPIC", "")

print(f"Options", flush=True)
print(f"- APP_ID: {GLB_APP_ID}", flush=True)
print(f"- APP_PORT: {GLB_APP_PORT}", flush=True)
print(f"- DAPR_PUBSUB_MODEL_NAME: {GLB_DAPR_PUBSUB_MODEL_NAME}", flush=True)
print(f"- DAPR_PUBSUB_MODEL_TOPIC: {GLB_DAPR_PUBSUB_MODEL_TOPIC}", flush=True)

class WorkerItemRequestDto(BaseModel):
    id: str
    image_url: str

# And add our Routes
@app.options("/my-queue")
async def processor_worker_item_options():
    return

@app.post("/my-queue")
async def processor_worker_item(item: WorkerItemRequestDto):
    print(f"Got Item: {item.id}", flush=True)

    # We add a delay so we don't work too quickly
    print("Sleeping for 5s before working", flush=True)
    time.sleep(5)
    
    # Then we run our code
    return handler_image_url(item.image_url)

def handler_image_url(image_url):
    print(f'Received: image_url="{image_url}"', flush=True)

    if not image_url:
        return

    # Download the image
    response = requests.get(image_url)
    img = Image.open(io.BytesIO(response.content))

    # Infer result
    results = model(img, size=640)
    bboxes = results.pandas().xyxy[0].to_json(orient="records")
    bboxes = json.loads(bboxes)

    # Print the Result
    items = {}
    for bbox in bboxes:
        items[bbox["name"]] = 1 if bbox["name"] not in items else items[bbox["name"]] + 1
    
    print(f'Results:', flush=True)
    for key, value in items.items():
        print(f'- {key}: {value}', flush=True)
        
    return