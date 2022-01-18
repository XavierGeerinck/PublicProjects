import io
from PIL import Image
import requests
import torch
import os
import json

# Pydantic
from typing import Optional
from pydantic import BaseModel
from starlette.requests import Request

# App Server
from fastapi import FastAPI
from dapr.ext.fastapi import DaprApp

app = FastAPI(title="ModelService")
dapr_app = DaprApp(app)

GLB_APP_ID = os.getenv("APP_ID", "")
GLB_APP_PORT = os.getenv("APP_PORT", "")
GLB_DAPR_PUBSUB_MODEL_NAME = os.getenv("DAPR_PUBSUB_MODEL_NAME", "")
GLB_DAPR_PUBSUB_MODEL_TOPIC = os.getenv("DAPR_PUBSUB_MODEL_TOPIC", "")

print(f"Options", flush=True)
print(f"- APP_ID: {GLB_APP_ID}", flush=True)
print(f"- APP_PORT: {GLB_APP_PORT}", flush=True)
print(f"- DAPR_PUBSUB_MODEL_NAME: {GLB_DAPR_PUBSUB_MODEL_NAME}", flush=True)
print(f"- DAPR_PUBSUB_MODEL_TOPIC: {GLB_DAPR_PUBSUB_MODEL_TOPIC}", flush=True)

"""
Our Subscription Request DTO which follows a cloud envelope

https://github.com/cloudevents/spec/blob/v1.0.1/json-format.md
https://github.com/cloudevents/spec/blob/v1.0.1/spec.json
"""
class ItemDto(BaseModel):
    image_url: str

# @todo: why is this needed here? shouldn't the __name__ == "main" be called first?
model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
model.eval()

@app.post("/")
async def handler_route(item: ItemDto):
    print(item, flush=True)
    return handler_image_url(item.image_url)


@dapr_app.subscribe(pubsub=GLB_DAPR_PUBSUB_MODEL_NAME, topic=GLB_DAPR_PUBSUB_MODEL_TOPIC)
async def handler_subscribe(req: Request) -> None:
    # CloudEventEventDto normally but we cannot submit dict to the publish
    # {'topic': 'worker-items', 'pubsubname': 'my-pubsub', 'data': '{"image_url": "https://www.ikea.com/images/een-3-zitsbank-met-chaise-longue-een-stellingkast-met-deuren-04d392ffcd855db85a5373f188230c66.jpg"}', 'id': 'aa050335-4a1b-46ac-9e19-c46acfc04a21', 'specversion': '1.0', 'type': 'com.dapr.event.sent', 'traceid': '00-e14fba7ba827d2da2d30ca7eb9da3957-f45807057c1c5029-01', 'datacontenttype': 'text/plain', 'source': 'send-events'}	
    req_json = await req.json()
    data = json.loads(req_json["data"])
    image_url = data["image_url"]
    return handler_image_url(image_url)


def handler_image_url(image_url):
    print(f'Received: image_url="{image_url}"', flush=True)

    if not image_url:
        return

    # Download the image
    response = requests.get(image_url)
    img = Image.open(io.BytesIO(response.content))

    # Infer result
    results = model(img, size=640)
    data = results.pandas().xyxy[0].to_json(orient="records")

    print(f'Result: {data}', flush=True)

    return data


if __name__ == "__main__":
    print("Loading Model", flush=True)
    model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
    model.eval()

    print("App is running", flush=True)
    # uvicorn.run(app, host="0.0.0.0", port=GLB_APP_PORT)
