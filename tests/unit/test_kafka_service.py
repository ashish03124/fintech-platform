# tests/unit/test_kafka_service.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from api_service.services.kafka_service import KafkaService

@pytest.fixture
def kafka_service():
    service = KafkaService(bootstrap_servers="localhost:9092")
    return service

@pytest.mark.asyncio
async def test_kafka_initialization(kafka_service):
    """Test Kafka service initialization"""
    with patch('confluent_kafka.Producer') as mock_producer:
        with patch('confluent_kafka.admin.AdminClient') as mock_admin:
            await kafka_service.initialize()
            
            mock_producer.assert_called_once()
            mock_admin.assert_called_once()

@pytest.mark.asyncio
async def test_produce_message(kafka_service):
    """Test producing message to Kafka"""
    with patch.object(kafka_service, 'producer') as mock_producer:
        mock_producer.produce = Mock()
        mock_producer.poll = Mock()
        
        result = await kafka_service.produce(
            topic="test-topic",
            key="test-key",
            value={"message": "test"}
        )
        
        assert result is True
        mock_producer.produce.assert_called_once()
        mock_producer.poll.assert_called_once()

@pytest.mark.asyncio
async def test_create_topic(kafka_service):
    """Test creating Kafka topic"""
    with patch.object(kafka_service, 'admin_client') as mock_admin:
        mock_future = AsyncMock()
        mock_future.result = Mock()
        mock_admin.create_topics.return_value = {"test-topic": mock_future}
        
        await kafka_service.create_topic("test-topic")
        
        mock_admin.create_topics.assert_called_once()

@pytest.mark.asyncio
async def test_health_check(kafka_service):
    """Test health check"""
    with patch.object(kafka_service, 'admin_client') as mock_admin:
        mock_admin.list_topics.return_value = Mock(
            brokers={"1": Mock()},
            topics={"test-topic": Mock()}
        )
        
        health = await kafka_service.check_health()
        
        assert health["status"] == "healthy"
        assert health["brokers"] == 1
        assert health["topics"] == 1