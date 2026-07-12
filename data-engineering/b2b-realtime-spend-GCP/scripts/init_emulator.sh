#!/bin/bash
# init_emulator.sh
#
# Waits for the Pub/Sub emulator to be healthy, then creates the topic
# and subscription. Run automatically by docker-compose on startup.
# Safe to re-run — the Python script handles "already exists" gracefully.

set -e

echo "Waiting for Pub/Sub emulator to be ready..."

until curl -sf http://pubsub-emulator:8085/v1/projects/local-dev-project/topics > /dev/null 2>&1; do
  echo "  emulator not ready yet, retrying in 2s..."
  sleep 2
done

echo "Emulator is ready. Creating topic and subscription..."
python /repo/init_emulator.py
echo "Done."