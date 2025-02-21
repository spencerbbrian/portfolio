from kafka import KafkaProducer
import json
import time
import random

'''
Every batch should have between 1 and 100 sales and must include
- Customer id
- Country
- Product id
- Quantity
- Price
- Timestamp
'''

topic = 'sales'

producer = KafkaProducer(
    bootstrap_servers = 'localhost:9092',
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
)

def send_data_to_topic(data):
    producer.send(topic, data)


def generate_data():
    for line in range(1,100):
        data = {
            'customer_id': random.randint(1,100),
            'country': random.choice(['North America', 'Europe', 'Asia', 'South America', 'Africa']),
            'product_id': random.randint(1,10000),
            'quantity': random.randint(1,5),
            'price': round(random.uniform(1.99, 249.99), 2),
            'timestamp': time.strftime("%Y-$m-%d %H:%M:%S")
        }
        send_data_to_topic(data)
        print(f"Data sent: {data}")
        time.sleep(0.5)
