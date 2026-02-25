# tests/integration/test_api_endpoints.py
import pytest
import json
from fastapi.testclient import TestClient
from api_service.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data

def test_transaction_processing():
    """Test transaction processing endpoint"""
    transaction_data = {
        "amount": 100.50,
        "currency": "USD",
        "merchant": "Test Store",
        "category": "SHOPPING",
        "description": "Test transaction"
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=transaction_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code in [200, 401]  # 401 if no auth

def test_financial_advice():
    """Test financial advice endpoint"""
    query_data = {
        "question": "Should I invest in index funds?",
        "context": {
            "risk_tolerance": "MODERATE",
            "investment_horizon": "10 years"
        }
    }
    
    response = client.post(
        "/api/v1/advice/",
        json=query_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code in [200, 401]

def test_websocket_connection():
    """Test WebSocket connection"""
    with client.websocket_connect("/ws/user_001") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection_established"