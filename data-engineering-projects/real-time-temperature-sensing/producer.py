from confluent_kafka import Producer
import time
import json
import random
import configparser

def read_config():
  # reads the client configuration from client.properties
  # and returns it as a key-value map
  config = {}
  with open(r"C:\Users\brian\Desktop\portfolio\portfolio\data-engineering-projects\real-time-temperature-sensing\client.properties") as fh:
    for line in fh:
      line = line.strip()
      if len(line) != 0 and line[0] != "#":
        parameter, value = line.strip().split('=', 1)
        config[parameter] = value.strip()
  return config

config = read_config()
topic = 'temperatures'
producer = Producer(config)


def delivery_report(err,msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()}')

def produce_temperature_data():
   sensor = {"sensor_id": "sensor1", "location":"room1"}
   data = {
        "sensor_id": sensor["sensor_id"],
        "location": sensor["location"],
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "temperature": round(random.uniform(18, 30), 2)  
   }
   producer.produce(topic,json.dumps(data).encode('utf-8'),callback=delivery_report)
   producer.flush()


if __name__ == '__main__':
    while True:
        produce_temperature_data()
        time.sleep(0.1)