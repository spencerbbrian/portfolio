import os
from google.cloud import storage

os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:4443"

client = storage.Client(
    client_options={"api_endpoint": "http://localhost:4443"},
    project="local-dev-project"
)

try:
    bucket = client.create_bucket("b2b-spend-models")
    print(f"✅ Success! Bucket created.")
except Exception as e:
    print(f"Failed: {e}")