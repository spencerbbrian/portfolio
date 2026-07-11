import os
import time
import urllib.request
from google.cloud import pubsub_v1

EMULATOR_HOST = os.environ.get("PUBSUB_EMULATOR_HOST", "localhost:8085")
os.environ["PUBSUB_EMULATOR_HOST"] = EMULATOR_HOST
PROJECT_ID = "local-dev-project"
TOPIC_ID = "b2b-transactions"
SUB_ID = "b2b-transactions-sub"

# Wait for emulator
print("Waiting for Pub/Sub emulator...")
url = f"http://{EMULATOR_HOST}/v1/projects/{PROJECT_ID}/topics"
while True:
    try:
        urllib.request.urlopen(url, timeout=3)
        print("Emulator ready.")
        time.sleep(2)
        break
    except Exception:
        print("  not ready, retrying...")
        time.sleep(2)

# Create topic
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
try:
    publisher.create_topic(request={"name": topic_path})
    print(f"Topic created: {topic_path}")
except Exception as e:
    print(f"Topic already exists: {e}")

# Create subscription
subscriber = pubsub_v1.SubscriberClient()
sub_path = subscriber.subscription_path(PROJECT_ID, SUB_ID)
try:
    subscriber.create_subscription(request={"name": sub_path, "topic": topic_path})
    print(f"Subscription created: {sub_path}")
except Exception as e:
    print(f"Subscription already exists: {e}")