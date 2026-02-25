# api-service/main.py
import os
import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fintech Platform API",
    description="Core API for managing transactions, authentication, and AI-powered financial advice",
    version="1.0.0",
)

# CORS Middleware — restrict origins in production via env var
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    try:
        from database import engine
        from models.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.warning(f"Could not create DB tables: {e}")


@app.get("/health", tags=["system"])
async def health_check():
    """Health check — reports database and service status."""
    services: dict = {}

    # Check database
    try:
        from database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        services["database"] = "healthy"
    except Exception:
        services["database"] = "unavailable"

    return {
        "status": "healthy",
        "service": "api-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services,
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "message": "Welcome to the Fintech Platform API",
        "docs": "/docs",
        "version": "1.0.0",
    }


# ── Router inclusions ─────────────────────────────────────────────────────────
from routers import transactions, advice, auth
from routers.websocket import router as ws_router
from routers.metrics import router as metrics_router

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["auth"],
)
app.include_router(
    transactions.router,
    prefix="/api/v1/transactions",
    tags=["transactions"],
)
app.include_router(
    advice.router,
    prefix="/api/v1/advice",
    tags=["advice"],
)
app.include_router(
    ws_router,
    tags=["websocket"],
)
app.include_router(
    metrics_router,
    tags=["monitoring"],
)
