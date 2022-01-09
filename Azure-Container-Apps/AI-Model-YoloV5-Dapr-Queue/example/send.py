from dapr.clients import DaprClient

import json
import uuid

if __name__ == "__main__":
    print("Publishing 2 messages", flush=True)

    with DaprClient() as d:
        # d.publish_event(pubsub_name="my-pubsub", topic_name="worker-items", data=json.dumps({
        #     "id": str(uuid.uuid4()),
        #     "source": "/demo",
        #     "specversion": "1.0.0",
        #     "type": "com.m18x.examples.ai.yolo-dapr-queue",
        #     "data": {
        #         "image_url": "https://www.ikea.com/images/een-3-zitsbank-met-chaise-longue-een-stellingkast-met-deuren-04d392ffcd855db85a5373f188230c66.jpg"
        #     }
        # }))

        # d.publish_event(pubsub_name="my-pubsub", topic_name="worker-items", data=json.dumps({
        #     "id": str(uuid.uuid4()),
        #     "source": "/demo",
        #     "specversion": "1.0.0",
        #     "type": "com.m18x.examples.ai.yolo-dapr-queue",
        #     "data": {
        #         "image_url": "https://www.ikea.com/images/een-3-zitsbank-met-chaise-longue-een-stellingkast-met-deuren-04d392ffcd855db85a5373f188230c66.jpg"
        #     }
        # }))

        d.publish_event(pubsub_name="my-pubsub", topic_name="worker-items", data=json.dumps({
            "image_url": "https://www.ikea.com/images/een-3-zitsbank-met-chaise-longue-een-stellingkast-met-deuren-04d392ffcd855db85a5373f188230c66.jpg"
        }))

    print("Done", flush=True)

# time="2022-01-08T11:34:55.519974221Z" level=warning msg="retriable error returned from app while processing pub/sub event beec19a5-62bd-4cbf-8abb-64382e961e13: {\"detail\":[{\"loc\":[\"body\",\"data\"],\"msg\":\"value is not a valid dict\",\"type\":\"type_error.dict\"}]}. status code returned: 422" app_id=ai-yolox instance=appab3c2742--1641635671433-574476f9f6-585x7 scope=dapr.runtime type=log ver=edge
