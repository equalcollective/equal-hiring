"""
X-Ray SDK Client

A lightweight wrapper for instrumenting multi-step decision processes.
Provides context-aware tracing with background batching and fail-safe error handling.
"""

import contextvars
import json
import queue
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import httpx

# Context variables for tracking current run and step across nested calls
_current_run: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "_current_run", default=None
)
_current_step: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "_current_step", default=None
)


class XRayClient:
    """Main X-Ray SDK client for decision observability."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        batch_size: int = 50,
        flush_interval: float = 2.0,
        timeout: float = 5.0,
    ):
        """
        Initialize the X-Ray client.

        Args:
            api_url: Base URL for the X-Ray API
            batch_size: Number of events to batch before flushing
            flush_interval: Time in seconds between automatic flushes
            timeout: HTTP request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.timeout = timeout

        # Queue for batching events
        self._queue: queue.Queue = queue.Queue()
        self._shutdown = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        # Start background worker thread
        self._start_worker()

    def _start_worker(self):
        """Start the background worker thread for batching and sending events."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._shutdown.clear()
            self._worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True, name="xray-worker"
            )
            self._worker_thread.start()

    def _worker_loop(self):
        """Background worker loop that batches and sends events."""
        batch: List[Dict[str, Any]] = []
        last_flush = time.time()

        while not self._shutdown.is_set():
            try:
                # Try to get an event with a timeout
                try:
                    event = self._queue.get(timeout=0.5)
                    batch.append(event)
                except queue.Empty:
                    event = None

                # Check if we should flush
                now = time.time()
                should_flush = (
                    len(batch) >= self.batch_size
                    or (event is None and len(batch) > 0 and (now - last_flush) >= self.flush_interval)
                )

                if should_flush and len(batch) > 0:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = now

            except Exception as e:
                # Fail-safe: log error but continue running
                # In production, you might want to log this to a logger
                print(f"X-Ray worker error (non-fatal): {e}")
                continue

    def _flush_batch(self, batch: List[Dict[str, Any]]):
        """Send a batch of events to the API (fail-safe)."""
        if not batch:
            return

        try:
            # Prepare batch payload
            payload = {"events": batch}

            # Send to API (fail-safe: catch all exceptions)
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.api_url}/ingest",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

        except Exception:
            # Fail-safe: silently drop events if API is unavailable
            # The user's application must continue without interruption
            pass  # Events are dropped, but application continues

    def shutdown(self, timeout: float = 5.0):
        """Gracefully shutdown the worker thread and flush remaining events."""
        if self._worker_thread and self._worker_thread.is_alive():
            self._shutdown.set()
            self._worker_thread.join(timeout=timeout)

            # Flush any remaining events
            remaining = []
            while not self._queue.empty():
                try:
                    remaining.append(self._queue.get_nowait())
                except queue.Empty:
                    break

            if remaining:
                self._flush_batch(remaining)

    @contextmanager
    def start_run(self, name: str, tags: Optional[Dict[str, Any]] = None):
        """
        Start a new trace run.

        Args:
            name: Name of the pipeline/run
            tags: Optional metadata tags (user_id, region, version, etc.)

        Yields:
            Dict containing run information
        """
        run_id = str(uuid.uuid4())
        run_data = {
            "id": run_id,
            "name": name,
            "tags": tags or {},
            "status": "RUNNING",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "steps": [],
        }

        # Set context variable
        token = _current_run.set(run_data)

        try:
            yield run_data

            # Mark as completed
            run_data["status"] = "COMPLETED"
            run_data["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Send run completion event
            self._queue.put({"type": "run_complete", "data": run_data})

        except Exception as e:
            # Mark as failed
            run_data["status"] = "FAILED"
            run_data["error"] = str(e)
            run_data["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Send run failure event
            self._queue.put({"type": "run_failed", "data": run_data})

            raise

        finally:
            # Restore previous context
            _current_run.reset(token)

    @contextmanager
    def step(
        self,
        name: str,
        step_type: str = "logic",
        reasoning: Optional[str] = None,
        inputs: Optional[Any] = None,
        cost: Optional[float] = None,
        token_usage: Optional[Dict[str, int]] = None,
    ):
        """
        Create a step within the current run.

        Args:
            name: Name of the step
            step_type: Type of step (llm, retrieval, filter, logic)
            reasoning: Optional reasoning/explanation for this step
            inputs: Optional input data for this step
            cost: Optional pre-calculated cost
            token_usage: Optional token usage dict with 'prompt' and 'completion' keys

        Yields:
            Dict containing step information
        """
        run_data = _current_run.get()
        if run_data is None:
            # No active run, create a no-op context manager
            yield {}
            return

        step_id = str(uuid.uuid4())
        step_data = {
            "id": step_id,
            "run_id": run_data["id"],
            "name": name,
            "type": step_type,
            "reasoning": reasoning,
            "inputs": self._serialize(inputs),
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        # Calculate cost if token_usage is provided
        if token_usage and cost is None:
            step_data["cost"] = self._calculate_llm_cost(token_usage)
        elif cost is not None:
            step_data["cost"] = cost

        # Set context variable
        token = _current_step.set(step_data)

        try:
            yield step_data

            # Mark as completed
            step_data["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Send step completion event
            self._queue.put({"type": "step_complete", "data": step_data})

        except Exception as e:
            # Mark as failed
            step_data["error"] = str(e)
            step_data["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Send step failure event
            self._queue.put({"type": "step_failed", "data": step_data})

            raise

        finally:
            # Restore previous context
            _current_step.reset(token)

    def process_candidates(
        self,
        candidates: List[Any],
        filter_fn: Callable[[Any], Tuple[bool, Optional[str]]],
        step_name: Optional[str] = None,
    ) -> List[Any]:
        """
        Process a list of candidates with filtering, tracking rejection reasons.

        This is a specialized helper that efficiently handles large candidate sets
        by summarizing rejection reasons instead of logging each individual rejection.

        Args:
            candidates: List of candidate items to filter
            filter_fn: Function that takes a candidate and returns (bool, reason_string)
                       where bool indicates acceptance (True) or rejection (False)
                       and reason_string explains why it was rejected (None if accepted)
            step_name: Optional name for this filtering step

        Returns:
            List of accepted candidates (survivors)
        """
        run_data = _current_run.get()
        if run_data is None:
            # No active run, just apply the filter
            return [c for c in candidates if filter_fn(c)[0]]

        step_name = step_name or "filter_candidates"
        survivors: List[Any] = []
        rejection_histogram: Dict[str, int] = {}
        total_count = len(candidates)

        # Process each candidate
        for candidate in candidates:
            accepted, reason = filter_fn(candidate)
            if accepted:
                survivors.append(candidate)
            else:
                # Track rejection reason
                reason_key = reason or "unknown"
                rejection_histogram[reason_key] = rejection_histogram.get(reason_key, 0) + 1

        # Create step data with summary
        step_data = {
            "id": str(uuid.uuid4()),
            "run_id": run_data["id"],
            "name": step_name,
            "type": "filter",
            "inputs": {
                "candidate_count": total_count,
                "sample_input": self._serialize(candidates[0]) if candidates else None,
            },
            "outputs": {
                "survivor_count": len(survivors),
                "survivors": self._serialize(survivors),
            },
            "metadata": {
                "rejection_histogram": rejection_histogram,
                "drop_rate": (total_count - len(survivors)) / total_count if total_count > 0 else 0.0,
                "total_count": total_count,
            },
            "reasoning": f"Filtered {total_count} candidates, {len(survivors)} survived. "
            f"Rejection reasons: {rejection_histogram}",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Send step event
        self._queue.put({"type": "step_complete", "data": step_data})

        return survivors

    def _serialize(self, obj: Any) -> Any:
        """Serialize an object to JSON-serializable format."""
        if obj is None:
            return None

        # Try JSON serialization
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # If not JSON-serializable, convert to string representation
            return str(obj)

    @staticmethod
    def _calculate_llm_cost(token_usage: Dict[str, int]) -> float:
        """
        Calculate LLM cost based on token usage.

        Uses standard pricing (as of 2024):
        - GPT-4: $0.03 per 1K prompt tokens, $0.06 per 1K completion tokens
        - GPT-3.5-turbo: $0.0015 per 1K prompt tokens, $0.002 per 1K completion tokens

        Defaults to GPT-4 pricing if model not specified.

        Args:
            token_usage: Dict with 'prompt' and 'completion' keys (token counts)

        Returns:
            Cost in USD
        """
        prompt_tokens = token_usage.get("prompt", 0)
        completion_tokens = token_usage.get("completion", 0)
        model = token_usage.get("model", "gpt-4")

        # Pricing per 1K tokens (default to GPT-4)
        pricing = {
            "gpt-4": (0.03, 0.06),
            "gpt-4-turbo": (0.01, 0.03),
            "gpt-3.5-turbo": (0.0015, 0.002),
            "gpt-4o": (0.005, 0.015),
        }

        prompt_price, completion_price = pricing.get(model, pricing["gpt-4"])

        cost = (prompt_tokens / 1000.0 * prompt_price) + (
            completion_tokens / 1000.0 * completion_price
        )

        return round(cost, 6)


# Global client instance (can be initialized by user)
_client: Optional[XRayClient] = None


def initialize(api_url: str = "http://localhost:8000", **kwargs) -> XRayClient:
    """Initialize the global X-Ray client."""
    global _client
    _client = XRayClient(api_url=api_url, **kwargs)
    return _client


def get_client() -> XRayClient:
    """Get the global X-Ray client (creates one if not initialized)."""
    global _client
    if _client is None:
        _client = XRayClient()
    return _client


# Convenience functions that use the global client
def start_run(name: str, tags: Optional[Dict[str, Any]] = None):
    """Start a new run using the global client."""
    return get_client().start_run(name, tags)


def step(name: str, step_type: str = "logic", **kwargs):
    """Create a step using the global client."""
    return get_client().step(name, step_type, **kwargs)


def process_candidates(candidates: List[Any], filter_fn: Callable[[Any], Tuple[bool, Optional[str]]], **kwargs):
    """Process candidates using the global client."""
    return get_client().process_candidates(candidates, filter_fn, **kwargs)


def calculate_llm_cost(token_usage: Dict[str, int]) -> float:
    """Calculate LLM cost using the utility function."""
    return XRayClient._calculate_llm_cost(token_usage)
