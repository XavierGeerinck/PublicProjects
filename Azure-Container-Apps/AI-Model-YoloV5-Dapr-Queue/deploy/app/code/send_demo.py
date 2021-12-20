from dapr.ext.grpc import App
from dapr.clients import DaprClient

import json

app = App()

if __name__ == "__main__":
    print("Publishing 2 messages")
    with DaprClient() as d:
        d.invoke_binding('bindings-ai-yolo-v5', 'create', json.dumps({
            "id": 1,
            "image_url": "https://www.ikea.com/images/een-3-zitsbank-met-chaise-longue-een-stellingkast-met-deuren-04d392ffcd855db85a5373f188230c66.jpg"
        }))

        d.invoke_binding('bindings-ai-yolo-v5', 'create', json.dumps({
            "id": 2,
            "image_url": "https://www.ikea.com/images/een-3-zitsbank-met-chaise-longue-een-stellingkast-met-deuren-04d392ffcd855db85a5373f188230c66.jpg"
        }))