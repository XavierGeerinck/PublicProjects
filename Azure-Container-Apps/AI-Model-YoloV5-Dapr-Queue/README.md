# Azure Container Apps - AI Model - YoloV5

## Note

Important to this demo is to test the use case of a Queue. Meaning that 1 item is processed once and not distributed over all the subscribers. Therefore we spin up 2 separate applications to demonstrate this.

## Creating Azure Infrastructure

To build this application we will be using [Pulumi](https://www.pulumi.com/). A tool that focuses on Developers and let's us use Javascript to create our application in cloud. To get started, let's configure it for use with Azure:

### Configuring Pulumi Azure

The below will set the subscription in Azure that we will use

```bash
# Login to Azure
az login

# Set the Azure Account Subscription to deploy to
az account set --subscription YOUR_SUBSCRIPTION_ID

export PULUMI_CONFIG_PASSPHRASE=""
```

### Running Pulumi

Pulumi will take care of:
* Creating the Azure Components
* Building our application Docker container
* Pushing it to a build Azure Container Registry
* Starting the application in a [Container App](https://docs.microsoft.com/en-us/azure/container-apps/overview)

So let's run the command below that will create a stack named `demo-cae-yolox` that deploys it to the `northeurope` region and listen on items in the topic `worker-items` of a Service Bus topic that will be created by Pulumi.

```bash
pulumi up \
    --stack demo-cae-yolox \
    -c glb-location=northeurope \
    -c glb-project-name=demo-cae-yolox \
    -c glb-project-env=prd \
    -c sb-topics="worker-items"
```

ALl of the above take around 15 minutes to complete.

## Usage

Once the Azure components have been created, configure the service bus connection in `examples/components/my-pubsub.yaml` and run it with:

```bash
dapr run --app-id=send-events --app-protocol http --components-path=./example/components python example/send.py
```

## Remarks

When using Container Apps, it seems that when you deploy a new container, the version revision is not automatically updated.


Start the application in with the Dapr Sidecar

```bash
# Run subscriber #1
dapr run --app-id=ai-yolo-v5 --app-port 5000 --app-protocol grpc --components-path=./components python "main.py --port 5000"

# Run subscriber #2
dapr run --app-id=ai-yolo-v5 --app-port 5001 --app-protocol grpc --components-path=./components python "main.py --port 5001"
```

Publish an item on the queue

```bash
dapr run --app-protocol grpc --components-path=./components python send.py
```

When running the above you will see that the message gets picked up and that we see:

```bash
[
    {"xmin":103.2421798706,"ymin":292.3749694824,"xmax":437.8124694824,"ymax":615.8124389648,"confidence":0.8725585938,"class":56,"name":"chair"},
    {"xmin":774.8436889648,"ymin":246.4374847412,"xmax":1126.8748779297,"ymax":567.5311889648,"confidence":0.841796875,"class":56,"name":"chair"},
    {"xmin":0.3515624702,"ymin":244.3281097412,"xmax":150.3515472412,"ymax":483.6249389648,"confidence":0.8344726562,"class":56,"name":"chair"},
    {"xmin":752.3436889648,"ymin":97.0234298706,"xmax":821.7186889648,"ymax":220.5390472412,"confidence":0.8227539062,"class":0,"name":"person"},
    {"xmin":536.2499389648,"ymin":107.1015548706,"xmax":659.0624389648,"ymax":210.4609222412,"confidence":0.7124023438,"class":0,"name":"person"},
    {"xmin":356.0155944824,"ymin":218.4296722412,"xmax":984.3749389648,"ymax":491.1249389648,"confidence":0.6181640625,"class":57,"name":"couch"},
    {"xmin":85.8984298706,"ymin":154.0937347412,"xmax":185.5077972412,"ymax":284.8749694824,"confidence":0.5854492188,"class":58,"name":"potted plant"},
    {"xmin":674.5311889648,"ymin":121.9843673706,"xmax":729.8436889648,"ymax":205.1874847412,"confidence":0.384765625,"class":58,"name":"potted plant"},
    {"xmin":233.5546722412,"ymin":220.0702972412,"xmax":367.0312194824,"ymax":321.9062194824,"confidence":0.2978515625,"class":56,"name":"chair"},
    {"xmin":440.3905944824,"ymin":0.0,"xmax":626.7186889648,"ymax":173.1952972412,"confidence":0.2956542969,"class":58,"name":"potted plant"},
    {"xmin":0.9082030654,"ymin":146.59375,"xmax":44.5898399353,"ymax":170.0312347412,"confidence":0.2568359375,"class":58,"name":"potted plant"}
]
```

Showing that it detected:

* 4 Chairs
* 2 Persons
* 4 Potted Plants
* 1 Couch

## Debug

### View latest logs of a Container App

```bash
ContainerAppConsoleLogs_CL 
    | where ContainerAppName_s == 'ca-api-yolov5' 
    | project ContainerAppName_s, Log_s, TimeGenerated 
    | order by TimeGenerated desc 
    | take 30
```

## Deploying

# Pulumi Deploy

## Getting Started

### Install Pulumi

Install Pulumi through the code below:

```bash
# Mac
brew install pulumi

# Windows
choco install pulumi

# Linux
curl -fsSL https://get.pulumi.com | sh
```

### Access Microsoft

```bash
az login
az account set --subscription YOUR_SUB_ID

# Get the locations we can deploy in
az account list-locations --output table
```

### Configure Pulumi

#### State File

Pulumi utilizes a state file. This file can be stored in the cloud or locally.

```bash
# Use Current Directory
pulumi login file://$(pwd)

# Use Home Directory
pulumi login --local

# Use Azure Blob
AZURE_STORAGE_ACCOUNT="NAME_OF_STORAGE_ACCOUNT"
AZURE_STORAGE_KEY="ACCESS_KEY_OF_STORAGE_ACCOUNT"
pulumi login azblob://AZURE_STORAGE_ACCOUNT_CONTAINER_PATH

# Logout
pulumi logout

# Migrating between backends
# https://www.pulumi.com/docs/intro/concepts/state/#migrating-between-backends

# Update State File
# find resources in stack: pulumi stack -s YOUR_STACK_NAME
# delete them: pulumi state -s YOUR_STACK_NAME delete 'URN'
```

## Running Pulumi

```bash
# Set Pulumi Location
pulumi config set azure-native:location northeurope

# Set Pulumi Password
export PULUMI_CONFIG_PASSPHRASE="YOUR_PASSWORD"

# [Node,.js] Install Dependencies
npm i

# Run Pulumi
pulumi up --stack demo-container-apps-pulumi
```