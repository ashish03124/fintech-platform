import logging

logger = logging.getLogger(__name__)

class TransactionProducer:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers
        logger.info(f"TransactionProducer initialized with {bootstrap_servers}")

    def send_transaction(self, transaction_data):
        # Placeholder for Kafka send logic
        logger.info(f"Transaction sent: {transaction_data}")
        return True
