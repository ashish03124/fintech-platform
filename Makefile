# Makefile
.PHONY: help start stop build test deploy clean

help:
	@echo "FinTech Platform Management Commands:"
	@echo "  make start        - Start all services with docker-compose"
	@echo "  make stop         - Stop all services"
	@echo "  make build        - Build all Docker images"
	@echo "  make test         - Run all tests"
	@echo "  make deploy       - Deploy to Kubernetes"
	@echo "  make clean        - Remove all containers and volumes"
	@echo "  make logs         - View service logs"
	@echo "  make kafka-topics - Create Kafka topics"

start:
	docker-compose up -d
	@echo "Platform started. Access:"
	@echo "  API: http://localhost:8000"
	@echo "  Kafka UI: http://localhost:8080"
	@echo "  Grafana: http://localhost:3000 (admin/admin)"

stop:
	docker-compose down

build:
	docker-compose build

test:
	docker-compose run --rm api-service pytest /app/tests/ -v

deploy:
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/

clean:
	docker-compose down -v
	docker system prune -f

logs:
	docker-compose logs -f

kafka-topics:
	docker-compose exec kafka kafka-topics --create \
		--topic transactions \
		--partitions 3 \
		--replication-factor 1 \
		--bootstrap-server localhost:9092
	
	docker-compose exec kafka kafka-topics --create \
		--topic alerts \
		--partitions 3 \
		--replication-factor 1 \
		--bootstrap-server localhost:9092
	
	docker-compose exec kafka kafka-topics --create \
		--topic recommendations \
		--partitions 3 \
		--replication-factor 1 \
		--bootstrap-server localhost:9092

init-db:
	docker-compose exec postgres psql -U admin -d fintech -f /docker-entrypoint-initdb.d/init.sql

data-generate:
	docker-compose run --rm data-generator python /app/producers/transaction_producer.py

spark-submit:
	docker-compose exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
		/opt/spark-jobs/transaction_processor.py