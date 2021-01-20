Machine Learning on Streams with Kafka
======================================

This repository documents on way of operating with streaming data on Kafka using Python. 

It requires a seperate server to the Kafka box for interacting with streams. There are many tools to do this; in this particular setting, we are choosing to use the `river` machine learning library, and `streamz` for this implementation over other approaches such as `spark`. The rationale is the maintenance of a `spark` cluster may be prohibitive in certain scenarios where it is desireable for a data science team to deploy "small" or "self-contained" models in a microservices approach. 

Another view is to integrate things like `streamz` and the machine learning libraries so that they are treated more like an RPC with a generic interface rather than a whole encompassing platform solution (which would be the case for Spark). 

The goal is not to have the "lowest latency" or "fastest" solution, but rather to demonstrate ideas around having the "minimal viable model" which can be measured and deployed. Infact, we are expecting the solution be to a near-realtime solution, and not a real-time solution; with the ability to deploy and manage models with ~10 minute latency (which is far quicker than any existing framework). 

There are several reasons for loosening these assumptions; though the simpliest one is that any faster is simply impractical. We point out that the requirement to deploy is different to the requirement to serve models at low latency. 

Instructions
------------

### Setting up Kafka

We will use the quickstart guide here: https://kafka.apache.org/quickstart

```sh
cd kafka
# on separate terminals, you can use screen with `ctrl+a |` or `ctrl+a s` or `ctrl+a TAB` to navigate in a single screen, `ctrl+a c` to start the session
bin/zookeeper-server-start.sh config/zookeeper.properties
bin/kafka-server-start.sh config/server.properties
```


### Setting up Python

We'll assume that `conda` is already installed, and we'll create a new environment and install some dependencies.

*  `river` - our key ml library
*  `streamz` - our interface to Kafka, through its streaming dataframes interface

You may need to run `apt-get install -y librdkafka-dev` to install `librdkafka` initially.


```sh
conda create -n kafka python=3
conda activate kafka
pip install git+https://github.com/online-ml/river "streamz[kafka]" black scikit-learn confluent-kafka --upgrade
```

### Kafka Topics

To start off with, lets use Python to publish a topic onto Kafka. We will use the confluent example to demonstrate this. The combined example from [confluent-kafka-python](https://github.com/confluentinc/confluent-kafka-python) is copied below


```py
"""
This is to ensure the hello world examples for kafka are working correctly
"""

from confluent_kafka import Producer, Consumer
import time

p = Producer({"bootstrap.servers": "localhost:9092"})
c = Consumer(
    {
        "bootstrap.servers": "localhost:9092",
        "group.id": "mygroup",
        "auto.offset.reset": "earliest",
    }
)

topic = "mytopic"


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print("Message delivery failed: {}".format(err))
    else:
        print("Message delivered to {} - {}".format(msg.topic(), msg.value()))


for data in [f"msg {i}" for i in range(100)]:
    # Trigger any available delivery report callbacks from previous produce() calls
    p.poll(0)

    # Asynchronously produce a message, the delivery report callback
    # will be triggered from poll() above, or flush() below, when the message has
    # been successfully delivered or failed permanently.
    p.produce(topic, data.encode("utf-8"), callback=delivery_report)

# Wait for any outstanding messages to be delivered and delivery report
# callbacks to be triggered.
p.flush()

c.subscribe([topic])

time_start = time.time()
max_seconds_wait = 10
while time.time() - time_start < max_seconds_wait:
    msg = c.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue

    print("Received message: {}".format(msg.value().decode("utf-8")))

c.close()
```

Setting up with River
---------------------

To test out how this implementation would work with `river`, we'll need to create a kafka producer which creates the data, and a consumer which trains a model, and puts the predictions back on the stream (where appropriate). 

