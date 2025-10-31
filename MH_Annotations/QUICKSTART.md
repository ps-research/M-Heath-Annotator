# Quick Start Guide

Get the annotation system up and running in 5 minutes.

---

## Step 1: Install Dependencies (1 minute)

```bash
cd MH_Annotations
pip install -r requirements.txt
```

---

## Step 2: Configure API Keys (1 minute)

Edit `config/api_keys.json`:

```json
{
  "annotator_1": "YOUR_GEMINI_API_KEY_HERE",
  "annotator_2": "",
  "annotator_3": "",
  "annotator_4": "",
  "annotator_5": ""
}
```

Get API keys from: https://aistudio.google.com/app/apikey

---

## Step 3: Place Dataset (1 minute)

Place your Excel file at:

```
data/source/m_help_dataset.xlsx
```

**Required columns:**
- `ID` (sample identifier)
- `Text` (mental health text)

---

## Step 4: Test Setup (1 minute)

```bash
# Test API connection
python scripts/test_gemini_api.py

# Test progress logger
python scripts/test_progress_logger.py
```

---

## Step 5: Run First Worker (1 minute)

```bash
# Manually run a single worker
python backend/core/worker.py --annotator 1 --domain urgency
```

Or use Python:

```python
from backend.core.worker_manager import WorkerManager

manager = WorkerManager()
manager.start_worker(1, "urgency")

# Monitor progress
status = manager.get_worker_status(1, "urgency")
print(status)

# Stop when done
manager.stop_worker(1, "urgency")
```

---

## What Next?

1. **Configure more annotators** in `config/settings.json`
2. **Start multiple workers** with `manager.start_all_enabled()`
3. **Monitor progress** in `data/annotations/annotator_X/DOMAIN/progress.json`
4. **Check annotations** in `data/annotations/annotator_X/DOMAIN/annotations.jsonl`

See **README.md** for complete documentation.

---

## Troubleshooting

**"API key not found"**
- Fill in your API key in `config/api_keys.json`

**"Dataset file not found"**
- Place Excel file at `data/source/m_help_dataset.xlsx`

**"Domain disabled"**
- Enable in `config/settings.json` by setting `"enabled": true`

**Rate limit errors**
- Wait for quota to reset (usually daily)
- Increase `request_delay_seconds` in settings

---

## Support

See **README.md** for detailed documentation and troubleshooting.
