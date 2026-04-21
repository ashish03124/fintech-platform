# 💳 Fintech Platform

> A modern, production-grade fintech microservices platform featuring AI-driven financial advice, real-time transaction streaming with Kafka, big data processing with Spark, and full observability with Prometheus & Grafana.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-AI-green?style=for-the-badge)](https://langchain.com/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white)](https://kafka.apache.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white)](https://spark.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://terraform.io/)

---

## 📖 What is this project?

**Fintech Platform** is a full-stack, microservices-based financial technology system built for scale. It combines an AI-powered financial advisory layer (built with LangChain and RAG), a real-time event streaming pipeline (Apache Kafka), distributed analytics (Apache Spark), a multi-database backend, and a complete monitoring stack — all orchestrated via Docker Compose and deployable to Kubernetes via Terraform.

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────────┐
│   Frontend  │────▶│   api-service    │────▶│    ai-services     │
│  (JS/CSS)   │     │ (FastAPI :8000)  │     │ (LangChain :8001)  │
└─────────────┘     └────────┬─────────┘     └────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │      Kafka       │  ◀── transactions / alerts
                    │  Event Stream    │      / recommendations
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Apache Spark    │
                    │ (Analytics Jobs) │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
     PostgreSQL          ClickHouse           Redis
    (core data)         (analytics)          (cache)
                             │
                          Qdrant
                        (vector DB)
```

---

## 📦 Services

| Service | Description | Port |
|---|---|---|
| `api-service` | FastAPI gateway — handles all client requests from web/mobile | `8000` |
| `ai-services` | LangChain-based agentic financial advisors + RAG system | `8001` |
| `kafka` | Apache Kafka event streaming for transactions, alerts, and recommendations | `9092` |
| `spark` | Optional Apache Spark jobs for real-time analytical processing | — |
| `databases` | PostgreSQL (core), ClickHouse (analytics), Redis (cache), Qdrant (vector DB) | — |
| `monitoring` | Prometheus metrics collection + Grafana dashboards | `3000` |
| `frontend` | Web client (JavaScript/CSS) | — |

---

## ✨ Key Features

- **AI Financial Advisor** — LangChain agentic advisor with a RAG (Retrieval-Augmented Generation) system backed by Qdrant vector DB for context-aware financial guidance
- **Real-time Event Streaming** — Kafka topics for `transactions`, `alerts`, and `recommendations` with 3-partition, fault-tolerant setup
- **Big Data Analytics** — Apache Spark jobs submit against a Spark master for distributed transaction processing
- **Multi-database Architecture** — PostgreSQL for ACID transactional data, ClickHouse for fast analytics queries, Redis for low-latency caching, Qdrant for vector search
- **Full Observability** — Prometheus scraping metrics from all services, visualised in Grafana (default: `admin/admin`)
- **Infrastructure as Code** — Terraform configs for cloud provisioning and Kubernetes manifests (`k8s/`) for production deployment
- **Developer-friendly Makefile** — One-command workflows for start, stop, build, test, deploy, and more

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| API Gateway | FastAPI + Uvicorn |
| AI / Agents | LangChain, RAG pipeline |
| Event Streaming | Apache Kafka |
| Batch / Stream Analytics | Apache Spark |
| Core Database | PostgreSQL |
| Analytics Database | ClickHouse |
| Cache | Redis |
| Vector Database | Qdrant |
| Monitoring | Prometheus + Grafana |
| Containerisation | Docker + Docker Compose |
| IaC / Cloud Deploy | Terraform, Kubernetes |
| Language | Python 3.10+ |

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) & Docker Compose
- Python 3.10+

### 1. Clone the repository

```bash
git clone https://github.com/ashish03124/fintech-platform.git
cd fintech-platform
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys and secrets
```

### 3. Start all services

```bash
make start
# or: docker-compose up -d
```

### 4. Create Kafka topics

```bash
make kafka-topics
```

### 5. Initialise the database

```bash
make init-db
```

All services are now running. Access them at:

| Service | URL |
|---|---|
| API Docs (Swagger) | http://localhost:8000/docs |
| AI Service Docs | http://localhost:8001/docs |
| Kafka UI | http://localhost:8080 |
| Grafana | http://localhost:3000 (admin / admin) |

---

## 🧰 Makefile Commands

```bash
make start          # Start all services with docker-compose
make stop           # Stop all services
make build          # Rebuild all Docker images
make test           # Run the full test suite
make deploy         # Deploy to Kubernetes (kubectl apply -f k8s/)
make clean          # Remove all containers and volumes
make logs           # Tail logs from all services
make kafka-topics   # Create transactions, alerts, recommendations topics
make init-db        # Initialise PostgreSQL schema
make data-generate  # Run the transaction data generator
make spark-submit   # Submit the Spark transaction processor job
```

---

## 📂 Project Structure

```
fintech-platform/
├── api-service/         # FastAPI gateway service
├── ai-services/         # LangChain agents & RAG system
├── frontend/            # Web client (JS/CSS)
├── kafka/               # Kafka configuration & producers/consumers
├── spark/               # Spark job definitions
├── databases/           # DB init scripts & configs
├── monitoring/          # Prometheus & Grafana configs
├── terraform/           # Infrastructure as Code (HCL)
├── tests/               # Test suite
├── docker-compose.yml   # Full local stack orchestration
├── Makefile             # Developer workflow commands
└── requirements.txt     # Python dependencies
```

---

## 🧪 Running Tests

```bash
make test
# or:
docker-compose run --rm api-service pytest /app/tests/ -v
```

---

## ☁️ Deploying to Kubernetes

```bash
make deploy
# or:
kubectl apply -f k8s/
```

Infrastructure provisioning is handled via Terraform configs in the `terraform/` directory.

---

## 📄 License

This project is private. All rights reserved.

---

<p align="center">Built by <a href="https://github.com/ashish03124">ashish03124</a></p>
