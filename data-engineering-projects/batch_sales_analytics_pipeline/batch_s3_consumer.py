from kafka import KafkaConsumer
import json
from json import loads
from s3fs import S3FileSystem

with open("keys.json","r") as file:
    config = json.load(file)

topic = config['kafka_topic']

print(topic)

consumer = KafkaConsumer(
    topic,
    bootstrap_servers = 'localhost:9092',
    value_deserializer = lambda v: loads(v.decode('utf-8')))