"""API routes for X-Ray backend."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Run, RunStatus, Step, StepType
from .schemas import (
    AnalyzeResponseSchema,
    DecisionFunnelStep,
    IngestRequestSchema,
    RunSchema,
    StepSchema,
)

router = APIRouter()


@router.post("/ingest", status_code=200)
async def ingest_events(
    request: IngestRequestSchema, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Ingest batch of events from SDK.

    Processes events and stores runs/steps in the database.
    """
    for event in request.events:
        event_type = event.type
        event_data = event.data

        if event_type == "run_complete":
            # Update existing run or create new one
            run_id = UUID(event_data["id"])
            run = await db.get(Run, run_id)
            if run:
                run.status = RunStatus.COMPLETED
                run.completed_at = event_data.get("completed_at")
                run.total_cost = event_data.get("total_cost", 0.0)
            else:
                run = Run(
                    id=run_id,
                    name=event_data["name"],
                    status=RunStatus.COMPLETED,
                    total_cost=event_data.get("total_cost", 0.0),
                    tags=event_data.get("tags", {}),
                    started_at=event_data.get("started_at"),
                    completed_at=event_data.get("completed_at"),
                )
                db.add(run)

        elif event_type == "run_failed":
            run_id = UUID(event_data["id"])
            run = await db.get(Run, run_id)
            if run:
                run.status = RunStatus.FAILED
                run.completed_at = event_data.get("completed_at")
                run.error = event_data.get("error")
            else:
                run = Run(
                    id=run_id,
                    name=event_data["name"],
                    status=RunStatus.FAILED,
                    total_cost=event_data.get("total_cost", 0.0),
                    tags=event_data.get("tags", {}),
                    started_at=event_data.get("started_at"),
                    completed_at=event_data.get("completed_at"),
                    error=event_data.get("error"),
                )
                db.add(run)

        elif event_type == "step_complete":
            # Create or update step
            step_id = UUID(event_data["id"])
            run_id = UUID(event_data["run_id"])
            step = await db.get(Step, step_id)
            if step:
                step.outputs = event_data.get("outputs", {})
                step.step_metadata = event_data.get("metadata", {})  # Use step_metadata attribute
                step.completed_at = event_data.get("completed_at")
                step.cost = event_data.get("cost", 0.0)
            else:
                step = Step(
                    id=step_id,
                    run_id=run_id,
                    name=event_data["name"],
                    type=StepType(event_data["type"]),
                    inputs=event_data.get("inputs", {}),
                    outputs=event_data.get("outputs", {}),
                    step_metadata=event_data.get("metadata", {}),  # Use step_metadata attribute
                    reasoning=event_data.get("reasoning"),
                    cost=event_data.get("cost", 0.0),
                    started_at=event_data.get("started_at"),
                    completed_at=event_data.get("completed_at"),
                )
                db.add(step)

                # Update run total cost
                run = await db.get(Run, run_id)
                if run:
                    run.total_cost = (run.total_cost or 0.0) + step.cost

        elif event_type == "step_failed":
            step_id = UUID(event_data["id"])
            run_id = UUID(event_data["run_id"])
            step = await db.get(Step, step_id)
            if step:
                step.error = event_data.get("error")
                step.completed_at = event_data.get("completed_at")
            else:
                step = Step(
                    id=step_id,
                    run_id=run_id,
                    name=event_data["name"],
                    type=StepType(event_data["type"]),
                    inputs=event_data.get("inputs", {}),
                    outputs=event_data.get("outputs", {}),
                    step_metadata=event_data.get("metadata", {}),  # Use step_metadata attribute
                    reasoning=event_data.get("reasoning"),
                    cost=event_data.get("cost", 0.0),
                    started_at=event_data.get("started_at"),
                    completed_at=event_data.get("completed_at"),
                    error=event_data.get("error"),
                )
                db.add(step)

    await db.commit()

    return {"status": "ok", "processed": len(request.events)}


@router.get("/analyze/{run_id}", response_model=AnalyzeResponseSchema)
async def analyze_run(run_id: UUID, db: AsyncSession = Depends(get_db)) -> AnalyzeResponseSchema:
    """
    Analyze a run and reconstruct the decision funnel.

    Shows how many candidates started, how many were filtered at each step,
    and the final selection reasoning.
    """
    # Get run
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Get all steps for this run, ordered by started_at
    result = await db.execute(
        select(Step).where(Step.run_id == run_id).order_by(Step.started_at)
    )
    steps = result.scalars().all()

    # Build decision funnel
    funnel: List[DecisionFunnelStep] = []
    final_output = None

    for step in steps:
        step_dict = step.to_dict()

        # Extract funnel information from metadata
        metadata = step.step_metadata or {}  # Use step_metadata attribute
        inputs = step.inputs or {}
        outputs = step.outputs or {}

        # Determine input/output counts
        input_count = None
        output_count = None

        if step.type == StepType.FILTER:
            # For filter steps, check metadata for counts
            input_count = metadata.get("total_count") or inputs.get("candidate_count")
            output_count = metadata.get("survivor_count") or (
                len(outputs.get("survivors", [])) if isinstance(outputs.get("survivors"), list) else None
            )

        elif step.type == StepType.RETRIEVAL:
            # For retrieval steps, check outputs
            if isinstance(outputs, dict):
                output_count = outputs.get("count") or (
                    len(outputs.get("items", [])) if isinstance(outputs.get("items"), list) else None
                )

        elif step.type == StepType.LOGIC:
            # Logic steps might have final outputs
            final_output = outputs

        # Calculate drop rate
        drop_rate = metadata.get("drop_rate")
        if drop_rate is None and input_count is not None and output_count is not None:
            if input_count > 0:
                drop_rate = (input_count - output_count) / input_count

        funnel_step = DecisionFunnelStep(
            step_id=step.id,
            step_name=step.name,
            step_type=step.type,
            input_count=input_count,
            output_count=output_count,
            drop_rate=drop_rate,
            rejection_histogram=metadata.get("rejection_histogram"),
            reasoning=step.reasoning,
            cost=step.cost,
        )
        funnel.append(funnel_step)

    return AnalyzeResponseSchema(
        run_id=run.id,
        run_name=run.name,
        status=run.status,
        total_cost=run.total_cost,
        funnel=funnel,
        final_output=final_output,
    )


@router.get("/runs", response_model=List[RunSchema])
async def list_runs(db: AsyncSession = Depends(get_db), limit: int = 100) -> List[RunSchema]:
    """List all runs."""
    result = await db.execute(select(Run).order_by(Run.started_at.desc()).limit(limit))
    runs = result.scalars().all()
    return [RunSchema.model_validate(run) for run in runs]


@router.get("/runs/{run_id}", response_model=RunSchema)
async def get_run(run_id: UUID, db: AsyncSession = Depends(get_db)) -> RunSchema:
    """Get a specific run with all its steps."""
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunSchema.model_validate(run)


@router.get("/runs/{run_id}/steps", response_model=List[StepSchema])
async def get_run_steps(run_id: UUID, db: AsyncSession = Depends(get_db)) -> List[StepSchema]:
    """Get all steps for a run."""
    result = await db.execute(
        select(Step).where(Step.run_id == run_id).order_by(Step.started_at)
    )
    steps = result.scalars().all()
    return [StepSchema.model_validate(step) for step in steps]

