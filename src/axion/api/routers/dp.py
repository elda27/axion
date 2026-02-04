"""DP Job API router"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, status

from axion.api.deps import BatchPath, DPJobRepo
from axion.dp.runner import DPRunner
from axion.schemas import DPJobCreate, DPJobResponse

router = APIRouter(tags=["DP Jobs"])


def _build_dp_job_response(job) -> DPJobResponse:
    """Build DP job response"""
    return DPJobResponse(
        job_id=job.job_id,
        batch_id=job.batch_id,
        mode=job.mode,
        recompute=bool(job.recompute),
        status=job.status,
        requested_by=job.requested_by,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_text=job.error_text,
    )


@router.post(
    "/batches/{batch_id}/dp/compute",
    response_model=DPJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dp_job(
    data: DPJobCreate,
    batch: BatchPath,
    repo: DPJobRepo,
    background_tasks: BackgroundTasks,
) -> DPJobResponse:
    """Create and trigger a DP computation job"""
    # Check if there's already a running job
    has_running = await repo.has_running_job(batch.batch_id)
    if has_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A DP job is already running for this batch",
        )

    # Create job
    job = await repo.create(batch.batch_id, data)

    # Start DP runner in background
    background_tasks.add_task(
        DPRunner.run_job,
        job.job_id,
        batch.batch_id,
        data.mode,
        data.recompute,
    )

    return _build_dp_job_response(job)


@router.get(
    "/dp/jobs/{job_id}",
    response_model=DPJobResponse,
)
async def get_dp_job(
    job_id: str = Path(),
    repo: DPJobRepo = ...,
) -> DPJobResponse:
    """Get DP job status"""
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DP Job not found: {job_id}",
        )
    return _build_dp_job_response(job)
