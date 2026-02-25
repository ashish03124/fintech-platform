# api-service/routers/advice.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any
import json
from datetime import datetime
import httpx
import os

from models.schemas import FinancialQuery, AdviceResponse

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-service:8000")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Validate JWT and return user payload. Returns a guest user if no token."""
    if not token:
        # Allow unauthenticated access with limited privileges for dev convenience
        return {"user_id": "guest", "email": "guest@example.com", "role": "guest"}
    try:
        import jwt as pyjwt
        secret_key = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
        payload = pyjwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/", response_model=AdviceResponse)
async def get_financial_advice(
    query: FinancialQuery,
    current_user: dict = Depends(get_current_user),
):
    """Get AI-powered financial advice via the ai-service."""
    query_id = str(uuid.uuid4())

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/api/v1/advice",
                json={
                    "query": query.question,
                    "user_id": current_user.get("user_id", "unknown"),
                    "context": query.context or {},
                },
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

    return AdviceResponse(
        query_id=query_id,
        question=query.question,
        advice=result.get("advice", "Unable to generate advice at this time."),
        confidence=result.get("confidence", 0.0),
        sources=result.get("sources", []),
        timestamp=datetime.utcnow(),
        disclaimer="This is for informational purposes only. Consult a qualified financial advisor.",
    )


@router.post("/agent")
async def get_agent_advice(
    query: FinancialQuery,
    current_user: dict = Depends(get_current_user),
):
    """Get streaming advice from the autonomous AI agent."""
    user_id = current_user.get("user_id", "unknown")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/api/v1/advice",
                json={
                    "query": query.question,
                    "user_id": user_id,
                    "context": {**(query.context or {}), "mode": "agent"},
                },
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

    async def stream_response():
        yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        yield f"data: {json.dumps({'type': 'reasoning', 'content': 'Analysing your financial profile...'})}\n\n"
        yield f"data: {json.dumps({'type': 'response', 'content': result.get('advice', '')})}\n\n"
        if result.get("sources"):
            yield f"data: {json.dumps({'type': 'sources', 'content': result['sources']})}\n\n"
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.get("/compliance/{advice_id}")
async def get_advice_compliance(
    advice_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get compliance audit record for an advice session (stub — extend with DB)."""
    return {
        "advice_id": advice_id,
        "user_id": current_user.get("user_id"),
        "status": "logged",
        "timestamp": datetime.utcnow().isoformat(),
        "disclaimer": "This is for informational purposes only.",
    }