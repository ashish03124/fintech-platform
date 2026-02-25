# Fintech Platform

A modern fintech microservices platform featuring AI-driven financial advice, real-time transaction processing with Kafka, and comprehensive monitoring.

## Architecture

- **api-service**: FastAPI gateway for mobile/web clients.
- **ai-services**: LangChain based agentic financial advisors and RAG system.
- **spark**: (Optional) Real-time analytical processing.
- **kafka**: Event streaming for transactions and notifications.
- **databases**: PostgreSQL (core), ClickHouse (analytics), Redis (caching), Qdrant (vector DB).
- **monitoring**: Prometheus & Grafana.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.10+

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   ```
3. Build and start the services:
   ```bash
   docker-compose up --build
   ```

## API Documentation

Once the services are up, visit:
- API Service: [http://localhost:8000/docs](http://localhost:8000/docs)
- AI Service: [http://localhost:8001/docs](http://localhost:8001/docs)
- Kafka UI: [http://localhost:8080](http://localhost:8080)
- Grafana: [http://localhost:3000](http://localhost:3000)
