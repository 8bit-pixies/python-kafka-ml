"""
This is an example of integrating kafka with river. 

We'll have Kafa produce data which is used for training in Kafka so that we can then use this to train and build.

This is just to test out integration with Kafka, obviously in production, they would reside in seperate scripts and
processes.
"""


from confluent_kafka import Producer, Consumer
from river import datasets
from river import linear_model
from itertools import cycle
import json
import time
from river import metrics

p = Producer({"bootstrap.servers": "localhost:9092"})
c = Consumer(
    {
        "bootstrap.servers": "localhost:9092",
        "group.id": "mygroup",
        "auto.offset.reset": "earliest",
    }
)

topic = "mytopic"
dataset = cycle(datasets.Phishing())
model = linear_model.LogisticRegression()
training_has_started = False
metric = metrics.Accuracy()
c.subscribe([topic])


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print("Message delivery failed: {}".format(err))
    else:
        print("Message delivered to {} - {}".format(msg.topic(), msg.value()))


for x, y in dataset:
    x['label'] = y
    data = json.dumps(x)
    p.poll(0)
    p.produce(topic, data.encode("utf-8"), callback=delivery_report if not training_has_started else None)
    p.flush()
    # the run the consumer
    msg = c.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue

    training_has_started = True
    data = json.loads(msg.value().decode("utf-8"))
    X_dat = {k:v for k,v in data.items() if k != "label"}
    y_dat = data['label']

    y_pred = model.predict_one(X_dat)
    metric = metric.update(y_dat, y_pred)
    model = model.learn_one(X_dat, y_dat)

    print("Performance (Accuracy) ", metric, end="\r", )

c.close()
