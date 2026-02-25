// frontend/src/hooks/useWebSocket.js
// Uses native WebSocket to match the FastAPI raw-WS endpoint (/ws/{userId}).
import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY_MS = 1000;
const PING_INTERVAL_MS = 30000;

export const useWebSocket = (userId) => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const pingIntervalRef = useRef(null);

  const connect = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE_URL}/ws/${userId}`);
    socketRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;
      console.log('WebSocket connected');

      // Subscribe to events
      ws.send(JSON.stringify({
        type: 'subscribe',
        events: ['transactions', 'alerts', 'recommendations', 'market_updates']
      }));

      // Keep-alive ping
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, PING_INTERVAL_MS);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type !== 'pong') {
          setMessages((prev) => [...prev, data]);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setIsConnected(false);
      clearInterval(pingIntervalRef.current);
      console.log('WebSocket disconnected');

      // Automatic reconnect with back-off
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_DELAY_MS * Math.pow(2, reconnectAttempts.current);
        reconnectAttempts.current += 1;
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})...`);
        setTimeout(connect, delay);
      }
    };
  }, [userId]);

  const disconnect = useCallback(() => {
    reconnectAttempts.current = MAX_RECONNECT_ATTEMPTS; // prevent auto-reconnect
    clearInterval(pingIntervalRef.current);
    if (socketRef.current) {
      socketRef.current.close();
      setIsConnected(false);
    }
  }, []);

  const sendMessage = useCallback((type, data) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type, data }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    messages,
    sendMessage,
    disconnect,
    connect
  };
};