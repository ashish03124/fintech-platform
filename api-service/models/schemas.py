# api-service/models/schemas.py
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TransactionType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    TRANSFER = "TRANSFER"
    REFUND = "REFUND"

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    FRAUD = "FRAUD"
    CANCELLED = "CANCELLED"

class TransactionCategory(str, Enum):
    FOOD = "FOOD"
    TRANSPORT = "TRANSPORT"
    SHOPPING = "SHOPPING"
    BILLS = "BILLS"
    ENTERTAINMENT = "ENTERTAINMENT"
    HEALTHCARE = "HEALTHCARE"
    EDUCATION = "EDUCATION"
    OTHER = "OTHER"

class RiskTolerance(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"

class InvestmentHorizon(str, Enum):
    SHORT_TERM = "SHORT_TERM"  # < 1 year
    MEDIUM_TERM = "MEDIUM_TERM"  # 1-5 years
    LONG_TERM = "LONG_TERM"  # > 5 years

# Request Models
class Transaction(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    merchant: Optional[str] = Field(None, max_length=255)
    category: TransactionCategory = Field(default=TransactionCategory.OTHER)
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    device_id: Optional[str] = Field(None, max_length=100)
    ip_address: Optional[str] = Field(None, max_length=45)
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 1000000:  # $1M limit
            raise ValueError('Amount exceeds maximum limit')
        return round(v, 2)
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        if v:
            import ipaddress
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v

class FinancialQuery(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000, description="Financial question")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")

class UserRegistration(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    date_of_birth: Optional[str] = Field(None, pattern="^\d{4}-\d{2}-\d{2}$")
    phone_number: Optional[str] = Field(None, pattern="^\+?[1-9]\d{1,14}$")
    
    @validator('password')
    def validate_password(cls, v):
        import re
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

# Response Models
class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    amount: float
    currency: str
    timestamp: datetime
    message: Optional[str] = None

class AdviceResponse(BaseModel):
    query_id: str
    question: str
    advice: str
    confidence: float = Field(..., ge=0, le=1)
    sources: List[Dict[str, Any]] = Field(default=[])
    timestamp: datetime
    disclaimer: str = "This is for informational purposes only. Consult a financial advisor."

class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    risk_tolerance: Optional[RiskTolerance] = None
    investment_horizon: Optional[InvestmentHorizon] = None
    accounts: List[Dict[str, Any]] = Field(default=[])
    created_at: datetime

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str = "1.0.0"

# Internal Models
class KafkaTransaction(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    merchant: Optional[str]
    category: str
    timestamp: int
    location: Optional[str]
    device_id: Optional[str]
    ip_address: Optional[str]
    status: str = "PENDING"

class AuditLog(BaseModel):
    log_id: str
    user_id: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]