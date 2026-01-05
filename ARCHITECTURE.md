Youtube video: https://youtu.be/GHeFLikN2uA

# X-Ray Architecture

## 1. Overview
X-Ray is a decision-observability system designed for non-deterministic pipelines (LLMs, RAG, Search). Unlike standard distributed tracing (which tracks *latency* and *errors*), X-Ray tracks *candidates*, *logic*, and *reasoning*.

## 2. System Design

### High-Level Components


1.  **X-Ray SDK (Python Client)**
    * **Role:** Instrumentation layer integrated into the user's pipeline.
    * **Design Philosophy:** "Fail-Safe & Non-Blocking." The SDK runs a background thread that flushes logs to the API. If the API is down, the user's application **must continue** without interruption.
    * **Key Feature:** "Smart Summarization." When filtering large datasets (e.g., 5,000 items), the SDK aggregates rejection reasons client-side instead of sending raw data for every item.

2.  **X-Ray API (FastAPI Service)**
    * **Role:** Ingestion and Query layer.
    * **Ingest:** Accepts batched traces asynchronously.
    * **Query:** Allows retrieval of runs by ID, name, or specific decision metrics (e.g., "drop_rate > 90%").

3.  **Data Storage (PostgreSQL)**
    * **Role:** Persistent storage for structured traces.
    * **Schema Strategy:** Relational backbone for indexing (Run IDs, timestamps) + `JSONB` for flexible step payloads (inputs, outputs, reasoning).

## 3. Data Model

### `runs` Table
Represents a single execution of a pipeline (e.g., "Competitor Selection Run #123").

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key |
| `name` | String | Pipeline name (indexed for search) |
| `status` | Enum | RUNNING, COMPLETED, FAILED |
| `total_cost` | Float | Aggregated cost of all LLM steps |
| `tags` | JSONB | User-defined metadata (user_id, region, version) |

### `steps` Table
Represents a discrete action within a run (e.g., "Filter Candidates").

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key |
| `run_id` | UUID | Foreign Key to `runs` |
| `step_type` | Enum | `llm`, `retrieval`, `filter`, `logic` |
| `inputs` | JSONB | The context entering the step |
| `outputs` | JSONB | The result of the step |
| `metadata` | JSONB | Reasoning data (e.g., rejection histograms) |
| `cost` | Float | Calculated cost for this specific step |

## 4. Key Workflows

### The "Smart Summarization" Flow (Handling 5k Items)
1.  **SDK:** User calls `xray.capture_list(candidates, filter_func)`.
2.  **Processing:** SDK iterates 5,000 items. 30 pass, 4,970 fail.
3.  **Aggregation:** SDK counts rejection reasons: `{"price_too_high": 4000, "wrong_category": 970}`.
4.  **Payload:** The API receives *only* the histogram and the 30 survivors.
5.  **Benefit:** Massive bandwidth saving while retaining debugging value.

### Cross-Pipeline Querying
To answer questions like *"Show runs where filtering eliminated 90% of candidates,"* we enforce a strict schema for the `metadata` JSONB field on specific step types.
* **Query:** `SELECT * FROM steps WHERE metadata->>'drop_rate' > 0.9`

## 5. Security & Performance
* **Async Ingestion:** API uses `async/await` to handle high concurrency.
* **Batching:** SDK buffers logs and sends them every 2 seconds or when the buffer reaches 50 items.
* **Retention:** (Future Work) Old traces can be archived to S3 or partitioned by date.