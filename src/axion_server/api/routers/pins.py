"""Pin API router"""

from fastapi import APIRouter, HTTPException, Path, status

from axion_server.api.deps import BatchRepo, RunPath, RunPinRepo
from axion.schemas import PinCreate, PinResponse, PinType

router = APIRouter(tags=["Pins"])


@router.post(
    "/runs/{run_id}/pins",
    response_model=PinResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pin(
    data: PinCreate,
    run: RunPath,
    repo: RunPinRepo,
    batch_repo: BatchRepo,
) -> PinResponse:
    """Create a pin for a run (champion or user_selected)"""
    # Verify batch exists
    batch = await batch_repo.get_by_id(run.batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {run.batch_id}",
        )

    # Check if pin already exists
    existing = await repo.get_by_run_and_type(run.run_id, data.pin_type)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pin already exists for run {run.run_id} with type {data.pin_type}",
        )

    pin = await repo.create(
        run_id=run.run_id,
        batch_id=run.batch_id,
        pin_type=data.pin_type,
    )
    return PinResponse.model_validate(pin)


@router.delete(
    "/runs/{run_id}/pins/{pin_type}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pin(
    run: RunPath,
    pin_type: PinType = Path(),
    repo: RunPinRepo = ...,
) -> None:
    """Delete a pin from a run"""
    deleted = await repo.delete_by_run_and_type(run.run_id, pin_type)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pin not found for run {run.run_id} with type {pin_type}",
        )
