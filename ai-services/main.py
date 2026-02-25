# ai-services/main.py
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fintech Platform AI Service",
    description="AI-driven financial advice and RAG service",
    version="1.0.0",
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


class AdviceRequest(BaseModel):
    query: str
    user_id: str
    context: dict = {}


class AdviceResponse(BaseModel):
    advice: str
    confidence: float
    sources: list = []


@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-service",
        "llm_configured": bool(OPENAI_API_KEY),
    }


@app.post("/api/v1/advice", response_model=AdviceResponse, tags=["advice"])
async def get_advice(request: AdviceRequest):
    logger.info(f"Advice request — user={request.user_id} query='{request.query[:80]}'")

    # If OpenAI key is available, use the real FinancialAgent
    if OPENAI_API_KEY:
        try:
            from agents.financial_agent import FinancialAgent

            user_context = {
                "risk_tolerance": request.context.get("risk_tolerance", "Moderate"),
                "investment_horizon": request.context.get("investment_horizon", "5-10 years"),
                "financial_goals": request.context.get("financial_goals", "Wealth accumulation"),
                "portfolio_value": request.context.get("portfolio_value", "$100,000"),
            }

            agent = FinancialAgent(user_id=request.user_id, user_context=user_context)
            result = await agent.process_query(request.query)

            return AdviceResponse(
                advice=result.get("response", "No advice generated."),
                confidence=result.get("confidence", 0.75),
                sources=result.get("sources", []),
            )
        except Exception as e:
            logger.error(f"FinancialAgent error: {e}. Falling back to mock response.")

    # Fallback mock response (no API key or agent failure)
    logger.warning("OPENAI_API_KEY not set or agent failed — returning mock response.")
    return AdviceResponse(
        advice=(
            f"Based on your query '{request.query}', I recommend diversifying your portfolio "
            "across tech and energy sectors. Consider a mix of index funds for lower risk. "
            "Set OPENAI_API_KEY in your environment for AI-powered personalised advice."
        ),
        confidence=0.60,
        sources=["Mock response — configure OPENAI_API_KEY for real advice"],
    )


# ── Mount metrics endpoint (fixes Prometheus 404) ────────────────────────────
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
try:
    from routers.metrics import router as metrics_router
    app.include_router(metrics_router, tags=["monitoring"])
except Exception:
    pass  # metrics router is optional


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
