# kafka/consumers/transaction_consumer.py
"""
Kafka Consumer — reads transactions from the 'transactions' topic
and persists them to PostgreSQL + logs them to ClickHouse.
"""
import os
import json
import logging
import time
from datetime import datetime
from kafka import KafkaConsumer
import psycopg2
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092").split(",")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://admin:admin123@postgres:5432/fintech")
TOPIC_NAME = "transactions"
GROUP_ID = "transaction-persister"


def get_db_connection(retries: int = 10, delay: int = 5):
    """Get PostgreSQL connection with retry logic."""
    import psycopg2
    from urllib.parse import urlparse

    parsed = urlparse(DATABASE_URL)
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                dbname=parsed.path.lstrip("/"),
                user=parsed.username,
                password=parsed.password,
            )
            logger.info("Connected to PostgreSQL")
            return conn
        except Exception as e:
            logger.error(f"DB connection attempt {attempt + 1}/{retries} failed: {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to PostgreSQL after retries")


def get_kafka_consumer(retries: int = 10, delay: int = 5) -> KafkaConsumer:
    """Get Kafka consumer with retry logic."""
    for attempt in range(retries):
        try:
            consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )
            logger.info(f"Connected to Kafka topic: {TOPIC_NAME}")
            return consumer
        except Exception as e:
            logger.error(f"Kafka connection attempt {attempt + 1}/{retries} failed: {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after retries")


def persist_transaction(conn, tx: dict):
    """Insert a transaction into PostgreSQL."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO transactions
                (id, amount, currency, description, merchant, category, status, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                tx.get("id", str(uuid.uuid4())),
                float(tx.get("amount", 0)),
                tx.get("currency", "USD"),
                tx.get("description", ""),
                tx.get("merchant", ""),
                tx.get("category", "OTHER"),
                tx.get("status", "COMPLETED"),
                tx.get("timestamp", datetime.utcnow().isoformat()),
            ),
        )
    conn.commit()


def main():
    logger.info("Starting Kafka transaction consumer...")
    conn = get_db_connection()
    consumer = get_kafka_consumer()

    processed = 0
    for message in consumer:
        try:
            tx = message.value
            persist_transaction(conn, tx)
            processed += 1
            if processed % 10 == 0:
                logger.info(f"Persisted {processed} transactions to PostgreSQL")
        except psycopg2.OperationalError:
            logger.warning("DB connection lost — reconnecting...")
            conn = get_db_connection()
        except Exception as e:
            logger.error(f"Error processing message: {e}")


if __name__ == "__main__":
    main()
