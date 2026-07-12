import urllib.request
import time

url = "http://pubsub-emulator:8085/v1/projects/local-dev-project/topics"
print("Waiting for Pub/Sub emulator...")
while True:
    try:
        urllib.request.urlopen(url, timeout=3)
        print("Emulator is ready.")
        time.sleep(3)  # brief pause for full readiness
        break          # exit the loop, let the script finish normally
    except Exception:
        print("  not ready yet, retrying in 2s...")
        time.sleep(2)