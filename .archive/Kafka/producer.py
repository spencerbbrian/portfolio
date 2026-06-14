from kafka import KafkaProducer
import json
import random
import time

topic= 'test-topic'

producer = KafkaProducer(
    bootstrap_servers = 'localhost:9092',
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
)

def send_data():
    for data in range(100):
        data = {"sensor_id": random.randint(1,5), "temperature": round(random.uniform(20.0, 30.0), 2)}
        producer.send(topic, data)
        print(f"Data sent: {data}")
        time.sleep(0.5)

send_data()
