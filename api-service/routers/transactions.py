# api-service/routers/transactions.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid as uuid_lib
from datetime import datetime

from database import get_db
from models.models import Transaction as TransactionModel
from models.schemas import Transaction as TransactionSchema, TransactionResponse

router = APIRouter()


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionSchema,
    db: Session = Depends(get_db),
):
    """Create and persist a new transaction to PostgreSQL."""
    tx_id = str(uuid_lib.uuid4())
    db_tx = TransactionModel(
        id=tx_id,
        amount=transaction.amount,
        currency=transaction.currency,
        description=transaction.description or "",
        merchant=transaction.merchant or "",
        category=transaction.category.value if hasattr(transaction.category, "value") else str(transaction.category),
        status="PENDING",
        timestamp=datetime.utcnow(),
    )
    db.add(db_tx)
    try:
        db.commit()
        db.refresh(db_tx)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return TransactionResponse(
        transaction_id=db_tx.id,
        status=db_tx.status,
        amount=db_tx.amount,
        currency=db_tx.currency,
        timestamp=db_tx.timestamp,
        message="Transaction created successfully",
    )


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List transactions from PostgreSQL with pagination."""
    transactions = db.query(TransactionModel).offset(skip).limit(limit).all()
    return [
        TransactionResponse(
            transaction_id=tx.id,
            status=tx.status,
            amount=tx.amount,
            currency=tx.currency,
            timestamp=tx.timestamp,
        )
        for tx in transactions
    ]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific transaction by ID."""
    tx = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse(
        transaction_id=tx.id,
        status=tx.status,
        amount=tx.amount,
        currency=tx.currency,
        timestamp=tx.timestamp,
    )
