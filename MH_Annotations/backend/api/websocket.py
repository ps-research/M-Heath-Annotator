"""
WebSocket API endpoint.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.websocket_manager import ws_manager

router = APIRouter()


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            # Handle client messages (ping, subscribe, etc.)
            # For now, just echo or ignore
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
