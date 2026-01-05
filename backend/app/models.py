"""Database models for X-Ray system."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from .database import Base


class RunStatus(PyEnum):
    """Run status enumeration."""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StepType(PyEnum):
    """Step type enumeration."""

    LLM = "llm"
    RETRIEVAL = "retrieval"
    FILTER = "filter"
    LOGIC = "logic"


class Run(Base):
    """Run model - represents a single pipeline execution."""

    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    status = Column(Enum(RunStatus), nullable=False, default=RunStatus.RUNNING, index=True)
    total_cost = Column(Float, default=0.0)
    tags = Column(JSONB, default={})
    started_at = Column(Text, nullable=False)
    completed_at = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(Text, server_default=func.now())

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status.value,
            "total_cost": self.total_cost,
            "tags": self.tags,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


class Step(Base):
    """Step model - represents a discrete action within a run."""

    __tablename__ = "steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(StepType), nullable=False, index=True)
    inputs = Column(JSONB, default={})
    outputs = Column(JSONB, default={})
    step_metadata = Column("metadata", JSONB, default={})  # Column name is "metadata" in DB, attribute is "step_metadata"
    reasoning = Column(Text, nullable=True)
    cost = Column(Float, default=0.0)
    started_at = Column(Text, nullable=False)
    completed_at = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(Text, server_default=func.now())

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "name": self.name,
            "type": self.type.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "metadata": self.step_metadata,  # Use step_metadata attribute, but output as "metadata"
            "reasoning": self.reasoning,
            "cost": self.cost,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }
