# Consume data from Kafka and write to S3 in json format
from kafka import KafkaConsumer
import json
import boto3
from datetime import datetime
import uuid
from config import topic, bucket_name, region, secret_access_key, access_key

#S3 bucket name
bucket = bucket_name


#Initialize KafkaConsumer
consumer = KafkaConsumer(
    topic,
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    enable_auto_commit=True, # Automatically commit offsets
    value_deserializer = lambda x: json.loads(x.decode('utf-8'))
)

# SInitialize S3 client
s3 = boto3.client(
    's3',
    region_name=region,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_access_key
)

def upload_to_s3(data_batch, prefix='sales_data'):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{prefix}/{timestamp}_{uuid.uuid4()}.json"

    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=filename,  # <- REQUIRED
            Body=json.dumps(data_batch).encode('utf-8')  # <- JSON payload
        )
        print(f"✅ Uploaded {filename} to S3 bucket {bucket_name}")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")


try:
    for message in consumer:
        try:
            data_batch = message.value

            print(f"Received batch of size {len(data_batch)}")
            upload_to_s3(data_batch)   

        except Exception as e:
            print(f"Error processing message: {e}")
except KeyboardInterrupt:
    print("Process interrupted. Closing consumer.")
finally:
    # Close the consumer after finishing
    consumer.close()
    print("Consumer closed.")