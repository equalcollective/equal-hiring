Youtube video: https://youtu.be/GHeFLikN2uA

# X-Ray SDK and API

A decision observability system for debugging non-deterministic, multi-step algorithmic systems.

## Overview

X-Ray provides transparency into multi-step decision processes by tracking candidates, filters, and reasoning at each step—not just performance metrics like traditional tracing systems.

**Key Features:**
- Context-aware tracing using `contextvars`
- Smart summarization for large candidate sets (e.g., 5,000 → histogram)
- Background batching with fail-safe error handling
- PostgreSQL storage with JSONB for flexible step data
- Decision funnel analysis via `/analyze/{run_id}` endpoint

## Project Structure

```
.
├── sdk/                    # X-Ray SDK (Python client)
│   ├── __init__.py        # Package exports
│   ├── client.py          # Core SDK implementation
│   └── requirements.txt   # SDK dependencies (httpx)
├── backend/               # FastAPI backend API
│   ├── app/              # Application code
│   │   ├── __init__.py
│   │   ├── main.py       # FastAPI app
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── routes.py     # API endpoints
│   │   └── database.py   # Database configuration
│   ├── requirements.txt  # Backend dependencies
│   └── README.md         # Backend-specific documentation
├── simulation.py          # Demo script showing SDK usage
├── ARCHITECTURE.md        # Architecture documentation
└── README.md             # This file
```

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 15+ (or Docker for running PostgreSQL)
- Docker (optional, for running PostgreSQL in a container)

---

## Step-by-Step Installation and Running

### Step 1: Setup PostgreSQL Database

You need a PostgreSQL database running. Choose one option:

#### Option A: Using Docker (Recommended)

```bash
# Run PostgreSQL in a Docker container
docker run --name xray-postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=xray_db \
  -p 5432:5432 \
  -d postgres:15
```

Verify it's running:
```bash
docker ps
```

#### Option B: Using Local PostgreSQL

If you have PostgreSQL installed locally, create a database:
```bash
createdb xray_db
# Or using psql:
psql -U postgres -c "CREATE DATABASE xray_db;"
```

---

### Step 2: Setup SDK as a Library

First, install the SDK as a proper Python package:

#### 2.1 Navigate to SDK directory
```bash
cd sdk
```

#### 2.2 Install SDK as a package
```bash
# Install in editable mode (recommended for development)
pip install -e .
```

Or from project root:
```bash
# From project root
pip install -e ./sdk
```

This makes the SDK available as `sdk` package that can be imported anywhere.

#### 2.3 (Optional) Create virtual environment for SDK
```bash
# If you want a separate venv for SDK (optional)
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e .
```

---

### Step 3: Setup Backend

#### 3.1 Navigate to backend directory
```bash
cd backend
```

#### 3.2 Create virtual environment
```bash
# Windows
python -m venv venv

# Mac/Linux
python3 -m venv venv
```

#### 3.3 Activate virtual environment
```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

#### 3.4 Install SDK in backend environment
```bash
# Install SDK as a package (from backend directory)
pip install -e ../sdk

# Or from project root (if venv is activated)
pip install -e ./sdk
```

#### 3.5 Install backend dependencies
```bash
pip install -r requirements.txt
```

This installs:
- FastAPI
- Uvicorn (ASGI server)
- SQLAlchemy (async)
- asyncpg (PostgreSQL driver)
- Pydantic
- python-dotenv
- X-Ray SDK (from step 3.4)

#### 3.6 (Optional) Create .env file
Create a `.env` file in the `backend/` directory if you want to customize the database URL:

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/xray_db
```

If you don't create this file, it will use the default connection string.

#### 3.7 Run the backend server

**Option A: Using the startup script (Recommended)**
```bash
# Windows Command Prompt
.\run.bat

# Windows PowerShell
.\run.ps1
```

**Option B: Manual start**
```bash
# Make sure your virtual environment is activated, then:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# OR using python -m (if uvicorn command not found):
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal window open** - the server needs to keep running.

You can verify it's working by visiting:
- API root: http://localhost:8000/
- API documentation: http://localhost:8000/docs
- Interactive API docs: http://localhost:8000/redoc

---

### Step 4: Run the Simulation

The simulation script demonstrates the SDK in action. It runs from the project root.

#### 4.1 Navigate to project root
```bash
# From anywhere, go to project root
cd /path/to/equal-hiring  # or wherever your project is
```

#### 4.2 Ensure SDK is installed

Make sure the SDK is installed (from Step 2):
```bash
# If not already installed
pip install -e ./sdk
```

#### 4.3 Run simulation
```bash
python simulation.py
```

You should see output showing:
- Generated keywords
- Retrieved candidate count
- Filtered candidate counts
- Selected competitor details
- Summary of key points demonstrated

**Note:** If the backend is not running, the simulation will still work (fail-safe design), but events won't be stored in the database.

---

## Usage Examples

### Using the SDK in Your Code

```python
from sdk import start_run, step, process_candidates

# Start a run
with start_run(name="my_pipeline", tags={"version": "1.0", "user_id": "123"}):
    
    # Create a step
    with step(name="filter_products", step_type="filter", reasoning="Filter by price"):
        candidates = [{"id": i, "price": i * 10} for i in range(1, 6)]
        
        def filter_fn(item):
            if item["price"] < 30:
                return True, None  # Accepted
            return False, "price_too_high"  # Rejected with reason
        
        survivors = process_candidates(candidates, filter_fn)
        print(f"Survivors: {survivors}")
```

### Querying the API

Once the backend is running, you can query it:

```bash
# List all runs
curl http://localhost:8000/runs

# Get a specific run
curl http://localhost:8000/runs/{run_id}

# Analyze a run (decision funnel)
curl http://localhost:8000/analyze/{run_id}

# Get steps for a run
curl http://localhost:8000/runs/{run_id}/steps
```

Or use the interactive API docs at http://localhost:8000/docs

---

## API Endpoints

- **GET /** - API root and status
- **POST /ingest** - Batch ingestion of events from SDK
- **GET /analyze/{run_id}** - Reconstruct decision funnel for a run
- **GET /runs** - List all runs
- **GET /runs/{run_id}** - Get run details
- **GET /runs/{run_id}/steps** - Get all steps for a run

---

## Troubleshooting

### Backend won't start

1. **Check PostgreSQL is running:**
   ```bash
   docker ps  # If using Docker
   # Or check PostgreSQL service
   ```

2. **Check database connection:**
   - Verify DATABASE_URL matches your PostgreSQL setup
   - Default: `postgresql+asyncpg://user:password@localhost:5432/xray_db`

3. **Check port 8000 is available:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Mac/Linux
   lsof -i :8000
   ```

### Simulation script errors

1. **Import errors:** Make sure httpx is installed (`pip install httpx`)
2. **SDK not found:** Make sure you're running from project root and `sdk/` directory exists
3. **Backend connection errors:** The SDK is fail-safe, so your script will continue even if backend is down

### Database connection errors

1. **Check PostgreSQL credentials:** User, password, database name
2. **Check PostgreSQL is accessible:** Try connecting with psql
3. **Check port 5432:** Make sure PostgreSQL is on the default port or update DATABASE_URL

---

## Key Design Decisions

### Smart Summarization
When processing large candidate sets, the SDK aggregates rejection reasons into a histogram instead of logging every item. This dramatically reduces bandwidth and storage while retaining debugging value.

### Fail-Safe Design
The SDK runs a background thread for batching and sending events. If the API is unreachable, events are silently dropped—the user's application continues without interruption.

### JSONB Storage
Step inputs, outputs, and metadata are stored as JSONB in PostgreSQL, allowing different pipeline types (competitor selection, listing optimization, categorization, etc.) to have different schemas while remaining queryable.

---

## SDK and Backend Integration

The SDK is installed as a Python package and can be imported in both:
- **Client applications** - Uses SDK to send events via HTTP to backend
- **Backend code** - Can import and use SDK directly for server-side instrumentation

The SDK sends events to the backend via HTTP POST to `/ingest` endpoint, but can also be used directly as a library in backend code.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and design decisions
- [backend/README.md](backend/README.md) - Backend-specific documentation
- [backend/SDK_INTEGRATION.md](backend/SDK_INTEGRATION.md) - How SDK and backend communicate

---

## Development

### Code Structure

- **SDK** (`sdk/client.py`): Context tracking, batching, fail-safe error handling
- **Backend** (`backend/app/`): FastAPI routes, SQLAlchemy models, PostgreSQL storage
- **Simulation** (`simulation.py`): Example usage demonstrating competitor selection

### Running Tests

(To be implemented)
