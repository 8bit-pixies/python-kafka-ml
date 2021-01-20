"""
This is to ensure the hello world examples for kafka are working correctly
"""

from confluent_kafka import Producer, Consumer
import json
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


for json_data in [{'msg': f"msg {i}", 'key': f'{i}!'} for i in range(100)]:
    # Trigger any available delivery report callbacks from previous produce() calls
    p.poll(0)

    data = json.dumps(json_data)

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

    data = json.loads(msg.value().decode("utf-8"))
    data = ' '.join([f"{k}-{v}" for k, v in data.items()])
    print("Received message: {}".format(data))

c.close()
