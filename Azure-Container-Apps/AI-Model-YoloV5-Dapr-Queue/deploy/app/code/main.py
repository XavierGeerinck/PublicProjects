import argparse
import io
from PIL import Image
import requests
import torch
import json
import os

from dapr.ext.grpc import App, BindingRequest

# We need a HTTP Server for Dapr for now
import flask

app_dapr = App()
app_http = flask.Flask(__name__)

@app_dapr.binding('queue')
def handler(request: BindingRequest) -> None:
    data = json.loads(request.text())
    image_url = data["image_url"]

    print(f'Received: id="{data["id"]}" image_url="{data["image_url"]}"', flush=True)

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
    # https://docs.dapr.io/reference/environment/
    dapr_sidecar_port_grpc = os.getenv('DAPR_GRPC_PORT', '50051')
    dapr_sidecar_http_grpc = os.getenv('DAPR_HTTP_PORT', '50051')
    app_port = os.getenv('APP_PORT', '5000')
    app_id = os.getenv('APP_ID', 'my-app-id')

    parser = argparse.ArgumentParser(description="AI Model with Dapr Queue")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()

    print("Loading Model", flush=True)
    model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
    model.eval()
    
    print("App is running", flush=True)

    app_dapr.run(args.port)
    app_http.run(host="0.0.0.0", port=args.port) 