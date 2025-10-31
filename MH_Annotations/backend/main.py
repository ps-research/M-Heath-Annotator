"""
FastAPI application entry point for Mental Health Annotation System.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.middleware.error_handler import validation_exception_handler, generic_exception_handler


# Create FastAPI app
app = FastAPI(
    title="Mental Health Annotation API",
    description="API for managing mental health text annotation system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Mental Health Annotation API"
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("=" * 60)
    print("Mental Health Annotation API Starting...")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    # Start WebSocket broadcast task
    try:
        from backend.websocket_manager import ws_manager
        ws_manager.start_broadcast_task()
    except Exception as e:
        print(f"Warning: Could not start WebSocket manager: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("=" * 60)
    print("Mental Health Annotation API Shutting Down...")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    # Stop WebSocket broadcast task
    try:
        from backend.websocket_manager import ws_manager
        ws_manager.stop_broadcast_task()
    except Exception as e:
        print(f"Warning: Could not stop WebSocket manager: {e}")


# Import and include routers
# These will be uncommented as we create each router
try:
    from backend.api import config, control, monitoring, data, export_api, websocket
    
    app.include_router(config.router, prefix="/api/config", tags=["Configuration"])
    app.include_router(control.router, prefix="/api/control", tags=["Control"])
    app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])
    app.include_router(data.router, prefix="/api/data", tags=["Data"])
    app.include_router(export_api.router, prefix="/api/export", tags=["Export"])
    app.include_router(websocket.router, prefix="/api/ws", tags=["WebSocket"])
except ImportError as e:
    print(f"Warning: Could not import all routers: {e}")
    print("Some API endpoints may not be available yet.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
