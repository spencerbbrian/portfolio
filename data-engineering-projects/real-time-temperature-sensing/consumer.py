from confluent_kafka import Consumer, KafkaError
import json


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
config["group.id"] = "python-group-1"
config["auto.offset.reset"] = "earliest"
consumer = Consumer(config)
consumer.subscribe([topic])

# sets the consumer group ID and offset  


try:
  while True:
    msg = consumer.poll(timeout=1.0)
    if msg is None:
      continue
    if msg.error():
      if msg.error().code == KafkaError._PARTITION_EOF:
        continue
      else:
        print(msg.error())
        break
    
    data = json.loads(msg.value())
    temperature = data.get('temperature')
    if temperature is not None:
      print(f"Temperature: {temperature}")

except KeyboardInterrupt:
  pass

finally:
  consumer.close()