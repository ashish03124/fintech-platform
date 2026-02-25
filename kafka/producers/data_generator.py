import time
import random
import json
import logging
from datetime import datetime
from kafka import KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = ["kafka:29092"]
TOPIC_NAME = "transactions"

def get_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Connected to Kafka")
            return producer
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def generate_transaction():
    merchants = ["Amazon", "Starbucks", "Uber", "Apple", "Netflix", "Walmart"]
    categories = ["Shopping", "Food", "Transport", "Electronics", "Entertainment", "Groceries"]
    
    return {
        "amount": round(random.uniform(5.0, 500.0), 2),
        "currency": "USD",
        "description": f"Transaction at {random.choice(merchants)}",
        "merchant": random.choice(merchants),
        "category": random.choice(categories),
        "timestamp": datetime.now().isoformat()
    }

def main():
    producer = get_producer()
    logger.info("Starting data generation...")
    
    while True:
        tx = generate_transaction()
        producer.send(TOPIC_NAME, tx)
        logger.info(f"Produced transaction: {tx['merchant']} - ${tx['amount']}")
        time.sleep(random.uniform(1, 5))

if __name__ == "__main__":
    main()
