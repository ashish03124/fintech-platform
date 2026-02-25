# api-service/services/kafka_service.py
import json
import asyncio
from typing import Dict, Any, Optional
from confluent_kafka import Producer, Consumer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import logging

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers or "kafka:29092"
        self.producer = None
        self.admin_client = None
        
    async def initialize(self):
        """Initialize Kafka connections"""
        try:
            # Initialize producer
            producer_conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'client.id': 'fintech-api-producer',
                'acks': 'all',
                'retries': 3,
                'compression.type': 'snappy',
                'linger.ms': 5,
                'batch.size': 32768,
                'enable.idempotence': True,
                'message.timeout.ms': 30000
            }
            self.producer = Producer(producer_conf)
            
            # Initialize admin client
            self.admin_client = AdminClient({'bootstrap.servers': self.bootstrap_servers})
            
            logger.info(f"Kafka service initialized with brokers: {self.bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka service: {e}")
            raise
    
    async def produce(self, topic: str, key: str, value: Dict[str, Any]) -> bool:
        """Produce message to Kafka topic"""
        try:
            def delivery_report(err, msg):
                if err is not None:
                    logger.error(f"Message delivery failed: {err}")
                else:
                    logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
            
            # Serialize value
            value_str = json.dumps(value)
            
            # Produce message
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8'),
                value=value_str.encode('utf-8'),
                callback=delivery_report
            )
            
            # Poll for delivery reports
            self.producer.poll(0)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to produce message to {topic}: {e}")
            return False
    
    async def create_topic(self, topic_name: str, num_partitions: int = 3, replication_factor: int = 1):
        """Create Kafka topic"""
        try:
            topic = NewTopic(
                topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor
            )
            
            futures = self.admin_client.create_topics([topic])
            
            for topic_name, future in futures.items():
                try:
                    future.result()
                    logger.info(f"Topic {topic_name} created")
                except Exception as e:
                    logger.error(f"Failed to create topic {topic_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to create topic: {e}")
            raise
    
    async def check_health(self) -> Dict[str, Any]:
        """Check Kafka health"""
        try:
            # Try to list topics
            topics = self.admin_client.list_topics(timeout=5)
            return {
                "status": "healthy",
                "brokers": len(topics.brokers),
                "topics": len(topics.topics)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self):
        """Close Kafka connections"""
        if self.producer:
            self.producer.flush()
            logger.info("Kafka producer closed")
        
    def __del__(self):
        # Synchronous cleanup — safe without a running event loop
        if self.producer:
            try:
                self.producer.flush(timeout=5)
            except Exception:
                pass