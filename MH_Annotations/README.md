# Mental Health Annotation System - Phase 1

**Core Annotation Engine for Multi-Domain Mental Health Dataset**

Version: 1.0
Phase: 1 - Core Backend
Status: Production Ready

---

## Overview

This system annotates mental health text data across 6 clinical domains using Google's Gemini API:

1. **Urgency** (LEVEL_0 to LEVEL_4) - Crisis triage assessment
2. **Therapeutic** (TA-1 to TA-9) - Recommended therapy approaches
3. **Intensity** (INT-1 to INT-5) - Intervention intensity level
4. **Adjunct** (ADJ-1 to ADJ-8) - Additional support services
5. **Modality** (MOD-1 to MOD-6) - Treatment delivery format
6. **Redressal** (JSON array) - Specific issues to address

### Key Features

- ✅ **30 parallel workers** (5 annotators × 6 domains)
- ✅ **Checkpointing** - Resume from any point after crashes
- ✅ **Atomic operations** - No data corruption
- ✅ **Graceful control** - Pause/resume/stop workers
- ✅ **Error handling** - Auto-pause on API errors
- ✅ **Progress tracking** - Real-time monitoring via files

---

## Directory Structure

```
MH_Annotations/
├── backend/
│   ├── core/              # Core annotation logic
│   │   ├── annotator.py   # Gemini API wrapper
│   │   ├── parser.py      # Response parser
│   │   ├── worker.py      # Worker process
│   │   ├── worker_manager.py  # Process manager
│   │   ├── dataset_loader.py  # Dataset loader
│   │   └── progress_logger.py # Progress tracking
│   ├── utils/
│   │   └── file_operations.py  # Atomic file ops
│   └── models/
│       └── schemas.py     # Data models
├── config/
│   ├── api_keys.json      # API keys (user fills)
│   ├── settings.json      # Configuration
│   └── prompts/
│       └── base/          # Prompt templates
├── data/
│   ├── source/            # Source dataset (Excel)
│   ├── annotations/       # Output annotations (JSONL)
│   └── logs/              # System logs
├── control/               # Control signal files
├── scripts/               # Test scripts
└── requirements.txt
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd MH_Annotations
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `config/api_keys.json` and add your Gemini API keys:

```json
{
  "annotator_1": "your-api-key-here",
  "annotator_2": "your-api-key-here",
  "annotator_3": "",
  "annotator_4": "",
  "annotator_5": ""
}
```

### 3. Place Dataset

Place your Excel dataset at:

```
data/source/m_help_dataset.xlsx
```

**Required columns:**
- `ID` - Sample identifier (string)
- `Text` - Mental health text to annotate (string)

### 4. Configure Settings

Edit `config/settings.json` to:

1. Enable annotators (set `"enabled": true`)
2. Set target counts (e.g., `"target_count": 500`)
3. Adjust model name, delays, etc.

**Example:**

```json
{
  "annotators": {
    "1": {
      "urgency": {"enabled": true, "target_count": 500},
      "therapeutic": {"enabled": true, "target_count": 500}
    }
  }
}
```

---

## Usage

### Test API Connection

```bash
python scripts/test_gemini_api.py
```

This verifies:
- API keys are valid
- Gemini API is accessible
- Parser is working

### Test Progress Logger

```bash
python scripts/test_progress_logger.py
```

This verifies:
- Atomic file operations work
- Progress tracking works
- Checkpointing works

### Test Single Worker

```bash
python scripts/test_single_worker.py
```

This runs a single worker on 5 samples to verify:
- Full worker loop works
- Annotations are saved correctly
- Resume from checkpoint works

### Run Single Worker Manually

```bash
python backend/core/worker.py --annotator 1 --domain urgency
```

### Use Worker Manager (Python)

```python
from backend.core.worker_manager import WorkerManager

manager = WorkerManager()

# Start a single worker
manager.start_worker(1, "urgency")

# Start all enabled workers
manager.start_all_enabled()

# Get status
status = manager.get_worker_status(1, "urgency")
print(status)

# Pause a worker
manager.pause_worker(1, "urgency")

# Resume a worker
manager.resume_worker(1, "urgency")

# Stop a worker
manager.stop_worker(1, "urgency")

# Stop all workers
manager.stop_all_workers()
```

---

## Data Formats

### Progress File (`data/annotations/annotator_X/DOMAIN/progress.json`)

```json
{
  "annotator_id": 1,
  "domain": "urgency",
  "enabled": true,
  "target_count": 500,
  "status": "running",
  "completed_ids": ["sample_001", "sample_002"],
  "malformed_ids": ["sample_003"],
  "last_processed_id": "sample_002",
  "last_updated": "2025-01-26T10:30:00Z",
  "pid": 12345,
  "stats": {
    "total_completed": 2,
    "malformed_count": 1,
    "start_time": "2025-01-26T10:00:00Z",
    "last_speed_check": "2025-01-26T10:30:00Z",
    "samples_per_min": 5.2
  }
}
```

### Annotations File (`data/annotations/annotator_X/DOMAIN/annotations.jsonl`)

JSONL format (one JSON object per line):

```json
{"id": "sample_001", "text": "I feel depressed...", "response": "Based on analysis...", "label": "LEVEL_2", "malformed": false, "parsing_error": null, "validity_error": null, "timestamp": "2025-01-26T10:15:00Z"}
{"id": "sample_002", "text": "I have anxiety...", "response": "Based on analysis...", "label": "LEVEL_1", "malformed": false, "parsing_error": null, "validity_error": null, "timestamp": "2025-01-26T10:16:00Z"}
```

### Control Signal File (`control/annotator_X_DOMAIN.json`)

```json
{
  "command": "pause",
  "timestamp": "2025-01-26T10:30:00Z"
}
```

Commands: `pause`, `resume`, `stop`

---

## Worker States

- **not_started** - Worker has not been started yet
- **running** - Worker is actively processing samples
- **paused** - Worker is paused (waiting for resume)
- **stopped** - Worker was stopped gracefully
- **completed** - Worker finished all target samples
- **crashed** - Worker crashed or became unresponsive (stale)

---

## Control Mechanism

Workers check for control signals:
- **Every 5 iterations** OR
- **Every 10 seconds**

Whichever comes first.

### Pause

```python
manager.pause_worker(1, "urgency")
```

Worker will:
1. Finish current sample
2. Enter pause loop
3. Check for resume/stop every 5 seconds

### Resume

```python
manager.resume_worker(1, "urgency")
```

Worker will:
1. Exit pause loop
2. Continue processing

### Stop

```python
manager.stop_worker(1, "urgency", timeout=30)
```

Worker will:
1. Finish current sample
2. Exit gracefully
3. If timeout exceeded, force kill

---

## Error Handling

### Rate Limits

When Gemini API rate limit is hit:
1. Worker logs error
2. Updates status to "paused"
3. Exits gracefully
4. User can resume later when quota resets

### Invalid API Key

When API key is invalid:
1. Worker logs error
2. Updates status to "stopped"
3. Exits immediately

### Malformed Responses

When AI response doesn't follow format:
1. Logged in `malformed_ids`
2. Saved to annotations file with `"malformed": true`
3. Worker continues to next sample

### Crashed Workers

Detected via staleness check:
- If progress not updated in 5 minutes AND status is "running"
- Status marked as "crashed"
- Can be restarted manually

---

## Monitoring Progress

### Check Worker Status

```python
status = manager.get_worker_status(1, "urgency")

print(f"Status: {status['status']}")
print(f"Running: {status['running']}")
print(f"Completed: {status['progress']['completed']}")
print(f"Target: {status['progress']['target']}")
print(f"Speed: {status['progress']['speed']} samples/min")
```

### Check All Workers

```python
all_statuses = manager.get_all_statuses()

for status in all_statuses:
    if status['progress']['target'] > 0:  # Only show enabled
        print(f"Annotator {status['annotator_id']}, {status['domain']}: {status['status']}")
```

### Read Annotations

```python
import json

with open('data/annotations/annotator_1/urgency/annotations.jsonl', 'r') as f:
    for line in f:
        annotation = json.loads(line)
        print(f"{annotation['id']}: {annotation['label']}")
```

---

## Troubleshooting

### Worker won't start

**Check:**
1. API key is configured in `config/api_keys.json`
2. Domain is enabled in `config/settings.json`
3. Dataset exists at `data/source/m_help_dataset.xlsx`
4. Required columns (ID, Text) exist in dataset

### Worker crashes immediately

**Check:**
1. Run test scripts to identify issue
2. Check logs in console output
3. Verify API key is valid
4. Ensure dataset is not corrupted

### Rate limit errors

**Solution:**
1. Wait for quota to reset (usually daily)
2. Reduce `request_delay_seconds` in settings
3. Use multiple API keys across annotators

### Malformed responses

**Common causes:**
1. Prompt template doesn't include `{text}` placeholder
2. AI doesn't follow `<< >>` format
3. Response doesn't match domain validation rules

**Solution:**
1. Check prompt templates in `config/prompts/base/`
2. Review malformed samples in annotations file
3. Adjust prompt wording if needed

### Progress not updating

**Check:**
1. Worker is actually running (check PID)
2. Progress file timestamp in `data/annotations/annotator_X/DOMAIN/progress.json`
3. If stale (>5 min), worker may have crashed

---

## Performance Tips

1. **Parallel workers:** Run multiple annotator-domain pairs simultaneously
2. **Rate limiting:** Adjust `request_delay_seconds` (1-2 seconds recommended)
3. **Target counts:** Set realistic targets per annotator
4. **API keys:** Use different keys for each annotator to avoid quota limits
5. **Monitoring:** Check speed stats to optimize settings

---

## Customization

### Custom Prompts

Create override prompts at:

```
config/prompts/overrides/annotator_X/DOMAIN.txt
```

This overrides the base prompt for that specific annotator-domain pair.

### Custom Model

Edit `config/settings.json`:

```json
{
  "global": {
    "model_name": "gemini-2.0-flash-exp"
  }
}
```

### Custom Delays

Edit `config/settings.json`:

```json
{
  "global": {
    "request_delay_seconds": 2,
    "control_check_iterations": 10,
    "control_check_seconds": 30
  }
}
```

---

## Data Export

Annotations are stored in JSONL format for easy processing:

```python
import json
import pandas as pd

# Load all annotations for annotator 1, urgency domain
annotations = []
with open('data/annotations/annotator_1/urgency/annotations.jsonl', 'r') as f:
    for line in f:
        annotations.append(json.loads(line))

# Convert to DataFrame
df = pd.DataFrame(annotations)

# Export to CSV
df.to_csv('urgency_annotations.csv', index=False)

# Export to Excel
df.to_excel('urgency_annotations.xlsx', index=False)
```

---

## Next Steps (Future Phases)

- **Phase 2:** FastAPI backend with REST endpoints
- **Phase 3:** React dashboard with Material-UI
- **Phase 4:** WebSocket integration for live updates
- **Phase 5:** Export functionality with multiple formats
- **Phase 6:** Inter-annotator agreement analysis

---

## Support

For issues or questions:
1. Check troubleshooting section
2. Review test script outputs
3. Examine log files and progress files
4. Verify configuration files

---

## License

This project is proprietary. All rights reserved.

---

**End of README**
