# SDK and Backend Integration

## Overview

The X-Ray SDK is a **Python package** that can be installed and imported in both client applications and backend code.

## Installation

### Install SDK as a Package

The SDK must be installed as a Python package before use:

```bash
# From project root
pip install -e ./sdk

# Or from backend directory
pip install -e ../sdk
```

The `-e` flag installs it in "editable" mode, so changes to SDK code are immediately available.

After installation, the SDK can be imported as:

```python
from sdk import start_run, step, process_candidates
```

## Usage Patterns

### 1. Client Application Usage

In client applications, the SDK sends events to the backend via HTTP:

```python
# In your application code
from sdk import start_run, step, process_candidates

with start_run(name="my_pipeline", tags={"version": "1.0"}):
    with step(name="filter", step_type="filter"):
        candidates = [1, 2, 3, 4, 5]
        
        def filter_fn(x):
            return (x > 3, None if x > 3 else "too_small")
        
        survivors = process_candidates(candidates, filter_fn)
```

The SDK:
- Tracks context using `contextvars`
- Batches events in a background thread
- Sends HTTP POST requests to `http://localhost:8000/ingest`
- Uses `httpx` library for HTTP communication

### 2. Backend Code Usage

The SDK can also be imported and used directly in backend code:

```python
# backend/app/your_module.py
from sdk import start_run, step, process_candidates

def process_backend_data():
    with start_run(name="backend_processing", tags={"source": "backend"}):
        with step(name="validate", step_type="logic"):
            # Your backend logic
            data = validate_input()
        
        with step(name="filter", step_type="filter"):
            def filter_fn(item):
                return (item.is_valid, None if item.is_valid else "invalid")
            
            filtered = process_candidates(data.items, filter_fn)
            return filtered
```

**Important:** When using SDK in backend code, events are still sent via HTTP to the `/ingest` endpoint. This means:
- The backend can instrument its own operations
- Events are stored in the same database
- You get observability into backend processing

See `backend/app/example_sdk_usage.py` for a complete example.

## Communication Protocol

### SDK → Backend: Event Ingestion

The SDK sends batches of events to the backend:

**Endpoint:** `POST http://localhost:8000/ingest`

**Request Body:**
```json
{
  "events": [
    {
      "type": "step_complete",
      "data": {
        "id": "uuid-here",
        "run_id": "uuid-here",
        "name": "filter_candidates",
        "type": "filter",
        "inputs": {...},
        "outputs": {...},
        "metadata": {
          "rejection_histogram": {"price_too_high": 4950},
          "drop_rate": 0.99
        },
        "reasoning": "...",
        "cost": 0.0,
        "started_at": "2024-01-01T12:00:00",
        "completed_at": "2024-01-01T12:00:01"
      }
    }
  ]
}
```

**Response:**
```json
{
  "status": "ok",
  "processed": 1
}
```

## Configuration

### SDK Configuration

Configure the SDK to point to your backend:

```python
from sdk import initialize

# Initialize SDK with backend URL
client = initialize(api_url="http://localhost:8000")

# Or use default (http://localhost:8000)
from xray_sdk import start_run  # Uses default URL
```

### Backend Configuration

The backend runs on:
- Default port: `8000`
- Change port: `uvicorn app.main:app --port 8080`

Update SDK initialization if backend runs on different port:

```python
from sdk import initialize
initialize(api_url="http://localhost:8080")
```

## Fail-Safe Design

If the backend is unavailable:
- SDK events are **silently dropped**
- Your application **continues running** (fail-safe)
- No exceptions are raised to your code

This ensures the SDK never breaks your application if the backend is down.

## Testing the Integration

### 1. Install SDK

```bash
pip install -e ./sdk
```

### 2. Start the Backend

```bash
cd backend
.\run.bat  # Windows
# OR
python -m uvicorn app.main:app --reload
```

### 3. Use SDK in Your Code

**Client Application:**
```python
from xray_sdk import start_run, step

with start_run(name="test_run"):
    with step(name="test_step", step_type="logic"):
        print("This step will be sent to the backend")
```

**Backend Code:**
```python
# backend/app/test.py
from xray_sdk import start_run, step

with start_run(name="backend_test"):
    with step(name="backend_step", step_type="logic"):
        print("Backend step sent to /ingest")
```

### 4. Verify Events Were Received

```bash
# Check if run was created
curl http://localhost:8000/runs

# Or visit http://localhost:8000/docs
```

## Common Questions

### Q: How do I install the SDK?

**A:** Use `pip install -e ./sdk` to install it as a package. Then import with `from sdk import ...`

### Q: Can the backend import the SDK?

**A:** Yes! After installing with `pip install -e ./sdk`, you can import it in backend code: `from sdk import start_run, step`

### Q: How do I change the backend URL in the SDK?

**A:** Initialize the SDK with a custom URL:

```python
from sdk import initialize
client = initialize(api_url="http://your-backend:8000")
```

### Q: What if the backend is down?

**A:** The SDK is fail-safe. Events are dropped silently, and your application continues running normally.

### Q: Can I use SDK in both client and backend code?

**A:** Yes! The SDK is a Python package that can be imported anywhere. Events from both client and backend code are sent to the same `/ingest` endpoint.

## Example: Complete Integration

### Client Application (uses SDK)

```python
# my_app.py
from sdk import start_run, step, process_candidates

def my_pipeline():
    with start_run(name="competitor_selection", tags={"version": "1.0"}):
        with step(name="filter", step_type="filter"):
            candidates = [1, 2, 3, 4, 5]
            
            def filter_fn(x):
                return (x > 3, None if x > 3 else "too_small")
            
            survivors = process_candidates(candidates, filter_fn)
            return survivors

if __name__ == "__main__":
    result = my_pipeline()
    print(f"Survivors: {result}")
```

### Backend Code (also uses SDK)

```python
# backend/app/processor.py
from xray_sdk import start_run, step

def process_request(data):
    with start_run(name="request_processing", tags={"source": "backend"}):
        with step(name="validate", step_type="logic"):
            # Validation logic
            validated = validate(data)
        return validated
```

Both send events to the same backend API at `/ingest`.
