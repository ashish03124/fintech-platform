# api-service/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime

router = APIRouter()

# Store active connections
active_connections: Dict[str, List[WebSocket]] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id not in active_connections:
            active_connections[user_id] = []
        active_connections[user_id].append(websocket)
        
        # Send connection confirmation
        await self.send_personal_message(
            websocket,
            {
                "type": "connection_established",
                "message": f"Connected as {user_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Subscribe to Kafka topics for this user
        asyncio.create_task(
            self.stream_user_events(websocket, user_id)
        )
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in active_connections:
            active_connections[user_id].remove(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)
    
    async def stream_user_events(self, websocket: WebSocket, user_id: str):
        """Stream real-time events from Kafka via aiokafka."""
        import os
        try:
            from aiokafka import AIOKafkaConsumer
        except ImportError:
            print("aiokafka not installed — skipping Kafka event streaming")
            return

        bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        topics = [
            f"user_{user_id}_transactions",
            f"user_{user_id}_alerts",
            f"user_{user_id}_recommendations",
            "market_updates",
            "system_alerts",
        ]

        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap,
            group_id=f"websocket_{user_id}",
            auto_offset_reset="latest",
        )

        try:
            await consumer.start()
            async for message in consumer:
                payload = json.loads(message.value.decode("utf-8")) if message.value else {}
                await websocket.send_json({
                    "type": "event",
                    "data": payload,
                    "topic": message.topic,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"Error in event streaming: {e}")
        finally:
            await consumer.stop()

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            await handle_websocket_message(websocket, user_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"Client {user_id} disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)

async def handle_websocket_message(websocket: WebSocket, user_id: str, message: dict):
    """Handle incoming WebSocket messages"""
    
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # Subscribe to specific event types
        event_types = message.get("events", [])
        await subscribe_to_events(user_id, event_types)
        
        await manager.send_personal_message(
            websocket,
            {
                "type": "subscription_confirmed",
                "events": event_types,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    elif message_type == "unsubscribe":
        # Unsubscribe from event types
        event_types = message.get("events", [])
        await unsubscribe_from_events(user_id, event_types)
    
    elif message_type == "query":
        # Handle real-time query
        query = message.get("query")
        response = await handle_realtime_query(user_id, query)
        
        await manager.send_personal_message(
            websocket,
            {
                "type": "query_response",
                "query": query,
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    elif message_type == "ping":
        # Keep-alive ping
        await manager.send_personal_message(
            websocket,
            {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

async def handle_realtime_query(user_id: str, query: str) -> dict:
    """Handle real-time query by delegating to the ai-service over HTTP."""
    import os
    import httpx

    ai_url = os.environ.get("AI_SERVICE_URL", "http://ai-service:8000")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{ai_url}/api/v1/advice",
                json={"query": query, "user_id": user_id, "context": {}},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": "AI service unavailable", "details": str(e)}