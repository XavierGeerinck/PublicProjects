import argparse
import io
from PIL import Image

import torch
from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello():
    return {
        "hello": "world"
    }

@app.route("/v1/object-detection/yolov5s", methods=["POST"])
def predict():
    if not request.method == "POST":
        return

    if request.files.get("image"):
        image_file = request.files["image"]
        image_bytes = image_file.read()

        img = Image.open(io.BytesIO(image_bytes))

        results = model(img, size=640)
        data = results.pandas().xyxy[0].to_json(orient="records")
        return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask api exposing yolov5 model")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()

    # model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, force_reload=True).autoshape()
    model = torch.hub.load("ultralytics/yolov5", "yolov5s")
    model.eval()
    
    app.run(host="0.0.0.0", port=args.port) 