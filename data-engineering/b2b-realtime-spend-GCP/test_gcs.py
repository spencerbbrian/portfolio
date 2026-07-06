import os
from google.cloud import storage

# Route to OrbStack container
os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:4443"

client = storage.Client(
    client_options={"api_endpoint": "http://localhost:4443"},
    project="local-dev-project"
)

bucket_name = "b2b-spend-models"
blob_name = "test_artifact.txt"
dummy_content = "isolation_forest_v1_mock_data"

try:
    # 1. Get or create the bucket
    try:
        bucket = client.get_bucket(bucket_name)
        print(f"📁 Bucket '{bucket_name}' already exists.")
    except Exception:
        bucket = client.create_bucket(bucket_name)
        print(f"✅ Created bucket '{bucket_name}'.")

    # 2. Upload a dummy object (Simulating saving an ML model artifact)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(dummy_content)
    print(f"🚀 Successfully uploaded '{blob_name}' to fake GCS.")

    # 3. Download and verify the round-trip
    downloaded_content = blob.download_as_text()
    print(f"📥 Round-trip check read content: '{downloaded_content}'")
    
    if downloaded_content == dummy_content:
        print("\n💯 SUCCESS: Local GCS emulator is fully verified end-to-end!")

except Exception as e:
    print(f"❌ Round-trip failed: {e}")