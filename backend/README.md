# X-Ray Backend API

The ingestion and query engine for the X-Ray observability system. Built with FastAPI and PostgreSQL.

## Tech Stack

* **Framework:** FastAPI 0.109+
* **Database:** PostgreSQL 15+
* **ORM:** SQLAlchemy 2.0 (Async)
* **Database Driver:** asyncpg
* **Validation:** Pydantic 2.5+
* **Server:** Uvicorn

---

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.10 or higher** installed
2. **PostgreSQL 15+** running (or Docker for containerized setup)
3. **pip** (Python package installer)

---

## Installation Steps

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv

# Mac/Linux
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

After activation, you should see `(venv)` in your terminal prompt.

### Step 4: Install X-Ray SDK (as a Library)

First, install the SDK as a Python package:

```bash
# From backend directory, install SDK from parent directory
pip install -e ../sdk
```

Or if you're in the project root:

```bash
# From project root
pip install -e ./sdk
```

The `-e` flag installs it in "editable" mode, so changes to SDK code are immediately available.

This makes the SDK available as `sdk` package that can be imported in backend code.

### Step 5: Install Backend Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `fastapi>=0.109.0` - Web framework
- `uvicorn[standard]>=0.27.0` - ASGI server
- `sqlalchemy[asyncio]>=2.0.25` - ORM with async support
- `asyncpg>=0.29.0` - PostgreSQL async driver
- `pydantic>=2.5.0` - Data validation
- `python-dotenv>=1.0.0` - Environment variable management

### Step 5: Setup PostgreSQL Database

You need a PostgreSQL database. Choose one option:

#### Option A: Using Docker (Recommended for Development)

```bash
# Start PostgreSQL container
docker run --name xray-postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=xray_db \
  -p 5432:5432 \
  -d postgres:15

# Verify it's running
docker ps
```

To stop the container later:
```bash
docker stop xray-postgres
docker rm xray-postgres  # To remove it
```

#### Option B: Using Local PostgreSQL

If you have PostgreSQL installed locally:

```bash
# Create database
createdb xray_db

# Or using psql
psql -U postgres -c "CREATE DATABASE xray_db;"
```

### Step 6: Configure Database Connection (Optional)

Create a `.env` file in the `backend/` directory to customize the database URL:

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/xray_db
```

**Note:** If you don't create a `.env` file, the application will use the default connection string:
```
postgresql+asyncpg://user:password@localhost:5432/xray_db
```

Make sure the credentials match your PostgreSQL setup.

---

## Using the SDK in Backend Code

The SDK is installed as a package and can be imported in your backend code:

```python
# backend/app/your_module.py
from xray_sdk import start_run, step, process_candidates

def your_backend_function():
    with start_run(name="backend_operation", tags={"source": "backend"}):
        with step(name="process_data", step_type="logic"):
            # Your backend logic here
            pass
```

See `backend/app/example_sdk_usage.py` for a complete example.

## Running the Server

### Start the Development Server

Make sure your virtual environment is activated, then run:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Flags explained:**
- `--reload` - Auto-reload on code changes (development only)
- `--host 0.0.0.0` - Listen on all network interfaces
- `--port 8000` - Port to run on

You should see output like:
```
INFO:     Will watch for changes in these directories: ['C:\\Users\\...\\backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Verify Server is Running

Open your browser and visit:

- **API Root:** http://localhost:8000/
- **Interactive API Docs (Swagger):** http://localhost:8000/docs
- **Alternative API Docs (ReDoc):** http://localhost:8000/redoc

### Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## Database Schema

The application automatically creates the database tables on first startup. The schema includes:

### `runs` Table
- `id` (UUID, Primary Key)
- `name` (String, Indexed)
- `status` (Enum: RUNNING, COMPLETED, FAILED)
- `total_cost` (Float)
- `tags` (JSONB)
- `started_at` (Text/ISO timestamp)
- `completed_at` (Text/ISO timestamp, nullable)
- `error` (Text, nullable)
- `created_at` (Timestamp)

### `steps` Table
- `id` (UUID, Primary Key)
- `run_id` (UUID, Foreign Key to runs)
- `name` (String)
- `type` (Enum: llm, retrieval, filter, logic)
- `inputs` (JSONB)
- `outputs` (JSONB)
- `metadata` (JSONB)
- `reasoning` (Text, nullable)
- `cost` (Float)
- `started_at` (Text/ISO timestamp)
- `completed_at` (Text/ISO timestamp, nullable)
- `error` (Text, nullable)
- `created_at` (Timestamp)

---

## API Endpoints

### Root

- **GET /** - API information and status

### Ingestion

- **POST /ingest** - Batch ingestion endpoint for SDK events
  - Accepts: `{"events": [{"type": "...", "data": {...}}, ...]}`
  - Returns: `{"status": "ok", "processed": <count>}`

### Query

- **GET /runs** - List all runs
  - Query params: `limit` (default: 100)
  - Returns: Array of run objects

- **GET /runs/{run_id}** - Get specific run details
  - Returns: Run object with all fields

- **GET /runs/{run_id}/steps** - Get all steps for a run
  - Returns: Array of step objects

- **GET /analyze/{run_id}** - Analyze run and reconstruct decision funnel
  - Returns: Run details with funnel analysis showing:
    - Input/output counts per step
    - Drop rates
    - Rejection histograms
    - Final outputs

---

## Testing the API

### Using the Interactive Docs

1. Visit http://localhost:8000/docs
2. Click on an endpoint to expand it
3. Click "Try it out"
4. Fill in parameters (if any)
5. Click "Execute"
6. View the response

### Using curl

```bash
# Get API status
curl http://localhost:8000/

# List runs
curl http://localhost:8000/runs

# Get a specific run (replace {run_id} with actual UUID)
curl http://localhost:8000/runs/{run_id}

# Analyze a run
curl http://localhost:8000/analyze/{run_id}

# Ingest events (example)
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"events": [{"type": "step_complete", "data": {...}}]}'
```

### Using Python requests

```python
import requests

# List runs
response = requests.get("http://localhost:8000/runs")
runs = response.json()
print(runs)

# Analyze a run
run_id = "your-run-id-here"
response = requests.get(f"http://localhost:8000/analyze/{run_id}")
analysis = response.json()
print(analysis)
```

---

## Troubleshooting

### Database Connection Errors

**Error:** `asyncpg.exceptions.InvalidPasswordError` or connection refused

**Solutions:**
1. Verify PostgreSQL is running:
   ```bash
   docker ps  # If using Docker
   # Or check PostgreSQL service status
   ```

2. Check database credentials in `.env` file match your PostgreSQL setup

3. Test connection manually:
   ```bash
   psql -U user -d xray_db -h localhost
   ```

4. Verify port 5432 is not blocked by firewall

### Port Already in Use

**Error:** `Address already in use` or `port 8000 is already in use`

**Solutions:**
1. Find what's using port 8000:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Mac/Linux
   lsof -i :8000
   ```

2. Stop the process or use a different port:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
   ```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solutions:**
1. Make sure you're in the `backend/` directory when running uvicorn
2. Make sure virtual environment is activated
3. Reinstall dependencies: `pip install -r requirements.txt`

### Tables Not Created

**Error:** Tables don't exist in database

**Solutions:**
1. Check database connection is working
2. Check application logs for errors during startup
3. Tables are created automatically on first startup via `init_db()` in `database.py`
4. Verify database user has CREATE TABLE permissions

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/xray_db` | PostgreSQL connection string |

---

## SDK Integration

**Important:** The SDK does NOT need to be imported in the backend. The SDK and backend are separate components that communicate via HTTP.

The SDK sends HTTP POST requests to `/ingest`, and the backend receives and stores them in PostgreSQL.

See [SDK_INTEGRATION.md](SDK_INTEGRATION.md) for detailed information about how the SDK and backend communicate.

---

## Production Deployment

For production deployment, consider:

1. **Remove `--reload` flag** (development only)
2. **Use environment variables** for sensitive data (never commit `.env` files)
3. **Use a production ASGI server** like Gunicorn with Uvicorn workers
4. **Set up proper database connection pooling**
5. **Add authentication/authorization** for API endpoints
6. **Set up logging and monitoring**
7. **Use HTTPS** with proper SSL certificates
8. **Database migrations** using Alembic (not implemented in this version)

Example production command:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Development Notes

- The database schema is created automatically on startup (`init_db()` in `database.py`)
- All timestamps are stored as ISO format strings (not native timestamp types)
- JSONB columns allow flexible schema for different pipeline types
- The `/analyze/{run_id}` endpoint reconstructs the decision funnel from step metadata
