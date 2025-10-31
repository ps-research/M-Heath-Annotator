# Mental Health Annotation System - Phase 2 API

## Overview

This is the FastAPI backend for the Mental Health Annotation System. It provides a comprehensive REST API and WebSocket interface for managing the annotation workflow.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running the Server

```bash
# From MH_Annotations directory
cd MH_Annotations
python -m backend.main

# Or using uvicorn directly
uvicorn backend.main:app --reload --port 8000
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Swagger Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## API Endpoints

### Configuration Management

- `GET /api/config/settings` - Get current system settings
- `PUT /api/config/settings` - Update system settings
- `GET /api/config/api-keys` - Get API keys (masked)
- `PUT /api/config/api-keys/{annotator_id}` - Update API key
- `GET /api/config/annotators/{annotator_id}/domains/{domain}` - Get domain config
- `PUT /api/config/annotators/{annotator_id}/domains/{domain}` - Update domain config
- `GET /api/config/prompts` - List all prompts
- `GET /api/config/prompts/{annotator_id}/{domain}` - Get prompt content
- `PUT /api/config/prompts/{annotator_id}/{domain}` - Update prompt
- `DELETE /api/config/prompts/{annotator_id}/{domain}` - Delete prompt override

### Worker Control

- `POST /api/control/start` - Start worker(s)
- `POST /api/control/stop` - Stop worker(s)
- `POST /api/control/pause` - Pause worker(s)
- `POST /api/control/resume` - Resume worker(s)
- `POST /api/control/reset` - Reset annotation data (DESTRUCTIVE)
- `POST /api/control/restart/{annotator_id}/{domain}` - Restart specific worker

### Monitoring

- `GET /api/monitoring/overview` - System-wide statistics
- `GET /api/monitoring/workers` - Get all worker statuses
- `GET /api/monitoring/workers/{annotator_id}/{domain}` - Get specific worker status
- `GET /api/monitoring/health` - Detect crashed/stalled workers
- `GET /api/monitoring/quota` - API quota usage estimates

### Data Access

- `GET /api/data/annotations` - Get paginated annotations with filters
- `GET /api/data/annotations/{annotator_id}/{domain}/{sample_id}` - Get specific annotation
- `GET /api/data/statistics` - Aggregated statistics
- `POST /api/data/retry/{annotator_id}/{domain}/{sample_id}` - Re-annotate malformed sample

### Export

- `POST /api/export` - Export annotations (JSON or Excel)
- `GET /api/export/preview` - Preview export data

### WebSocket

- `WS /api/ws` - Real-time updates (connects via WebSocket)

## Example Usage

### Start a Worker

```bash
curl -X POST "http://localhost:8000/api/control/start" \
  -H "Content-Type: application/json" \
  -d '{
    "annotator_id": 1,
    "domain": "urgency"
  }'
```

### Get System Overview

```bash
curl "http://localhost:8000/api/monitoring/overview"
```

### Update Settings

```bash
curl -X PUT "http://localhost:8000/api/config/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "request_delay_seconds": 2,
    "max_retries": 5
  }'
```

### Export to Excel

```bash
curl -X POST "http://localhost:8000/api/export" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "excel",
    "filters": {
      "annotator_ids": [1, 2],
      "domains": ["urgency", "therapeutic"]
    }
  }' \
  --output annotations.xlsx
```

### WebSocket Connection (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

## Architecture

```
React Dashboard (Phase 3)
      ↕ HTTP REST + WebSocket
FastAPI Backend (Phase 2) ← YOU ARE HERE
      ↕ File System
Core Engine (Phase 1)
```

## Project Structure

```
MH_Annotations/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── websocket_manager.py    # WebSocket connection manager
│   ├── api/                    # API route handlers
│   │   ├── config.py
│   │   ├── control.py
│   │   ├── monitoring.py
│   │   ├── data.py
│   │   ├── export_api.py
│   │   └── websocket.py
│   ├── services/               # Business logic
│   │   ├── config_service.py
│   │   ├── worker_service.py
│   │   ├── monitoring_service.py
│   │   ├── data_service.py
│   │   └── export_service.py
│   ├── models/                 # Pydantic schemas
│   │   ├── schemas.py
│   │   └── responses.py
│   └── middleware/             # Error handling
│       └── error_handler.py
└── tests/                      # API tests
```

## Features

- ✅ RESTful API with proper HTTP methods
- ✅ CORS enabled for React frontend
- ✅ Pydantic validation for all requests/responses
- ✅ WebSocket server for live updates
- ✅ Error handling with proper status codes
- ✅ Background tasks for worker management
- ✅ File-based state (no database needed)
- ✅ Auto-generated OpenAPI documentation

## Development

### Running Tests

```bash
pytest tests/
```

### API Documentation

Visit http://localhost:8000/api/docs for interactive Swagger documentation.

## Next Steps

Phase 3 will implement the React dashboard frontend that consumes this API.

## Troubleshooting

### Port Already in Use

```bash
# Kill existing process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Import Errors

Ensure you're running from the MH_Annotations directory and Python path is set correctly.

### CORS Errors

CORS is configured to allow all origins in development. In production, update the `allow_origins` in `main.py`.
