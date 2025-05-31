from kafka import KafkaProducer
from config import topic
import json
import time
import random

# Retrieve Kafka topic from config
topic = topic
print(f"Using Kafka topic: {topic}")

# Initialize KafkaProducer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Function to send data to the Kafka topic
def send_data_to_topic(data):
    try:
        producer.send(topic, data)
    except Exception as e:
        print(f"Error sending data to Kafka: {e}")

# Function to generate and send random sales data
def generate_data():
    try:
        while True:
            # Randomly decide the batch size (between 1 and 100)
            batch_size = random.randint(1, 2)
            batch = []

            # Generate a batch of random sales data
            for _ in range(batch_size):
                data = {
                    'customer_id': random.randint(1, 100),
                    'country': random.choice(['North America', 'Europe', 'Asia', 'South America', 'Africa']),
                    'product_id': random.randint(1, 10000),
                    'quantity': random.randint(1, 5),
                    'price': round(random.uniform(1.99, 249.99), 2),
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                batch.append(data)

            # Send the entire batch to Kafka
            send_data_to_topic(batch)
            print(f"Batch sent: {batch}")

            # Pause for 0.5 seconds before sending the next batch
            time.sleep(10)

    except KeyboardInterrupt:
        print("Process interrupted. Closing producer.")
    finally:
        # Close the producer after finishing
        producer.close()
        print("Producer closed.")

# Start generating data
if __name__ == "__main__":
    generate_data()

