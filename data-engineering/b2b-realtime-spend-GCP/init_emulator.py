import os
from google.cloud import pubsub_v1

os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"

project_id = "local-dev-project"
topic_id = "b2b-transactions"
sub_id = "b2b-transactions-sub"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, sub_id)

try:
    publisher.create_topic(request={"name": topic_path})
    print(f"Topic created: {topic_path}")
except Exception as e:
    print(f"Topic already exists: {e}")

try:
    subscriber.create_subscription(request={"name": subscription_path, "topic": topic_path})
    print(f"Subscription created: {subscription_path}")
except Exception as e:
    print(f"Subscription already exists: {e}")