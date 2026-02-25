# api-service/routers/metrics.py
from fastapi import APIRouter
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST
)
from fastapi.responses import Response
import time

router = APIRouter()

# ── Prometheus metrics ────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)
TRANSACTION_COUNT = Counter(
    "transactions_total",
    "Total number of transactions processed",
    ["status", "currency"]
)
ACTIVE_CONNECTIONS = Gauge(
    "active_websocket_connections",
    "Number of active WebSocket connections"
)


@router.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
