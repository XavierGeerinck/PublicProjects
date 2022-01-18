from dapr.clients import DaprClient

import json
import uuid
import sys

message_count = int(sys.argv[1])

print(f"Publishing {message_count} messages")

with DaprClient() as d:
    for i in range(message_count):
        d.invoke_binding("my-queue", "create", data=json.dumps({
            "id": str(uuid.uuid4()),
            "image_url": "https://www.ikea.com/images/een-3-zitsbank-met-chaise-longue-een-stellingkast-met-deuren-04d392ffcd855db85a5373f188230c66.jpg"
        }))
