# Azure Container Apps - AI Model - YoloV5

## Building

Build the container by running

```bash
docker build -t api-yolov5 .
```

## Usage

curl -X POST -F image=@demo.jpg 'http://localhost:5000/v1/object-detection/yolov5s'

WHen running the above you will get something such as:

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