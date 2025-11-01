"""
FastAPI application entry point for Mental Health Annotation System.

UPGRADED: Now includes automatic watchdog monitoring and config validation.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import asyncio

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.middleware.error_handler import validation_exception_handler, generic_exception_handler
from backend.core.worker_watchdog import WorkerWatchdog
from backend.core.config_validator import ConfigValidator
from backend.core.logger_config import setup_logging


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
    # Setup logging
    logger = setup_logging("main", log_level="INFO")

    logger.info("=" * 70)
    logger.info("Mental Health Annotation API Starting...")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("=" * 70)

    # Validate configuration
    logger.info("Validating configuration...")
    validator = ConfigValidator()
    is_valid, config_objects, errors = validator.validate_all()

    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.warning("System will start but may encounter errors")
    else:
        logger.info("Configuration validation passed")
        summary = validator.get_validation_summary()
        if "statistics" in summary:
            stats = summary["statistics"]
            logger.info(f"Enabled workers: {stats['enabled_workers']}")
            logger.info(f"Total target samples: {stats['total_target_samples']}")

    # Start WebSocket broadcast task
    try:
        from backend.websocket_manager import ws_manager
        ws_manager.start_broadcast_task()
        logger.info("WebSocket manager started")
    except Exception as e:
        logger.warning(f"Could not start WebSocket manager: {e}")

    # NEW: Start Worker Watchdog
    logger.info("Starting Worker Watchdog...")
    try:
        app.state.watchdog = WorkerWatchdog(
            check_interval=60,  # Check every minute
            max_restart_attempts=3
        )
        asyncio.create_task(app.state.watchdog.monitor_loop())
        logger.info("Worker Watchdog started successfully")
    except Exception as e:
        logger.error(f"Failed to start Worker Watchdog: {e}")
        logger.error("Automatic recovery will NOT be available")

    logger.info("=" * 70)
    logger.info("System Ready!")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger = setup_logging("main", log_level="INFO")

    logger.info("=" * 70)
    logger.info("Mental Health Annotation API Shutting Down...")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("=" * 70)

    # NEW: Stop Worker Watchdog
    if hasattr(app.state, 'watchdog'):
        logger.info("Stopping Worker Watchdog...")
        try:
            await app.state.watchdog.stop()
            logger.info("Worker Watchdog stopped")
        except Exception as e:
            logger.error(f"Error stopping watchdog: {e}")

    # Stop WebSocket broadcast task
    try:
        from backend.websocket_manager import ws_manager
        ws_manager.stop_broadcast_task()
        logger.info("WebSocket manager stopped")
    except Exception as e:
        logger.warning(f"Could not stop WebSocket manager: {e}")

    logger.info("Shutdown complete")


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
