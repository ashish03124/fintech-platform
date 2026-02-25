# ai-services/routers/metrics.py
from fastapi import APIRouter
from prometheus_client import (
    Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
)
from fastapi.responses import Response

router = APIRouter()

AI_REQUEST_COUNT = Counter(
    "ai_requests_total",
    "Total AI advice requests",
    ["user_id", "has_openai_key"]
)
AI_LATENCY = Histogram(
    "ai_request_duration_seconds",
    "AI advice request latency"
)


@router.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint for AI service."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
