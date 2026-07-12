#!/bin/bash
# Start Airflow standalone in background
airflow standalone &

# Wait for it to initialise
echo "Waiting for Airflow to start..."
sleep 20

# Create admin user (will skip if already exists)
airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com 2>/dev/null

# Always reset password to make sure it's what we expect
airflow users reset-password \
  --username admin \
  --password admin

echo "Airflow ready — login with admin/admin"

# Keep container alive
wait