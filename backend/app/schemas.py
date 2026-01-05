"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Run status enumeration."""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StepType(str, Enum):
    """Step type enumeration."""

    LLM = "llm"
    RETRIEVAL = "retrieval"
    FILTER = "filter"
    LOGIC = "logic"


class RunSchema(BaseModel):
    """Run schema for API responses."""

    id: UUID
    name: str
    status: RunStatus
    total_cost: float = 0.0
    tags: Dict[str, Any] = {}
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class StepSchema(BaseModel):
    """Step schema for API responses."""

    id: UUID
    run_id: UUID
    name: str
    type: StepType
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    reasoning: Optional[str] = None
    cost: float = 0.0
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class IngestEventSchema(BaseModel):
    """Schema for individual ingest events."""

    type: str  # "run_complete", "step_complete", etc.
    data: Dict[str, Any]


class IngestRequestSchema(BaseModel):
    """Schema for batch ingest request."""

    events: List[IngestEventSchema]


class DecisionFunnelStep(BaseModel):
    """Represents a step in the decision funnel."""

    step_id: UUID
    step_name: str
    step_type: StepType
    input_count: Optional[int] = None
    output_count: Optional[int] = None
    drop_rate: Optional[float] = None
    rejection_histogram: Optional[Dict[str, int]] = None
    reasoning: Optional[str] = None
    cost: float = 0.0


class AnalyzeResponseSchema(BaseModel):
    """Response schema for analyze endpoint."""

    run_id: UUID
    run_name: str
    status: RunStatus
    total_cost: float
    funnel: List[DecisionFunnelStep]
    final_output: Optional[Dict[str, Any]] = None
