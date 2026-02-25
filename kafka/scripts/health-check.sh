#!/bin/bash
# kafka/scripts/health-check.sh
#!/bin/bash

# Health check for Kafka
echo "Checking Kafka health..."

# Check if Kafka is responding
kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Kafka is healthy"
    exit 0
else
    echo "Kafka is not healthy"
    exit 1
fi