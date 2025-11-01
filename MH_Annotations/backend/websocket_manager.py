"""
WebSocket connection manager for real-time updates.
"""

import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime
from fastapi import WebSocket

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.monitoring_service import MonitoringService


class WebSocketManager:
    """Manages WebSocket connections and broadcasts updates."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: List[WebSocket] = []
        self.last_state: Dict[str, Any] = {}
        self.broadcast_task: asyncio.Task = None
        self.monitoring_service = MonitoringService()

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send initial state immediately
        await self.send_initial_state(websocket)
        
        print(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def send_initial_state(self, websocket: WebSocket):
        """Send initial full state to newly connected client."""
        try:
            overview = self.monitoring_service.get_system_overview()
            workers = self.monitoring_service.get_all_worker_statuses()
            
            message = {
                "type": "full_state",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "overview": overview,
                    "workers": workers
                }
            }
            
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending initial state: {e}")

    async def broadcast_updates(self):
        """
        Background task to broadcast updates every 2 seconds.

        FIXED: Always sends updates instead of comparing state to ensure cards always refresh.
        """
        while True:
            try:
                await asyncio.sleep(2)

                if not self.active_connections:
                    continue

                # Get current state
                overview = self.monitoring_service.get_system_overview()
                workers = self.monitoring_service.get_all_worker_statuses()

                current_state = {
                    "overview": overview,
                    "workers": workers,
                    "timestamp": datetime.utcnow().isoformat()  # Force uniqueness
                }

                # FIXED: Always send update to ensure UI stays fresh
                # Old behavior: Only sent if state changed (comparison could miss timestamp-only changes)
                # New behavior: Always send to ensure cards update properly
                message = {
                    "type": "update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": current_state
                }

                await self.send_to_all(message)
                self.last_state = current_state

            except Exception as e:
                print(f"Error in broadcast loop: {e}")

    async def send_to_all(self, message: Dict[str, Any]):
        """Send message to all connected clients."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_heartbeat(self):
        """Send heartbeat to all clients."""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_all(message)

    def start_broadcast_task(self):
        """Start the background broadcast task."""
        if self.broadcast_task is None or self.broadcast_task.done():
            self.broadcast_task = asyncio.create_task(self.broadcast_updates())
            print("WebSocket broadcast task started")

    def stop_broadcast_task(self):
        """Stop the background broadcast task."""
        if self.broadcast_task and not self.broadcast_task.done():
            self.broadcast_task.cancel()
            print("WebSocket broadcast task stopped")


# Global instance
ws_manager = WebSocketManager()
