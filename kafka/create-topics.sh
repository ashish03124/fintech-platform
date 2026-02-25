#!/bin/bash

# Wait for Kafka to be ready
echo "Waiting for Kafka..."
until cub kafka-ready -b kafka:29092 1 30; do
  sleep 2
done

echo "Creating Kafka topics..."

kafka-topics --create --if-not-exists --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --topic transactions
kafka-topics --create --if-not-exists --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --topic api-logs
kafka-topics --create --if-not-exists --bootstrap-server kafka:29092 --partitions 1 --replication-factor 1 --topic advice-requests

echo "Topics created successfully!"
