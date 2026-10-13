"""FastAPI app: enqueue a PDF job, poll its status, download the result."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session

from config import OUTPUT_DIR
from models import Job, create_db_and_tables, engine
from tasks import make_pdf_with_random_values


class JobStartResponse(BaseModel):
    message: str
    task_id: int


class JobStatusResponse(BaseModel):
    task_id: int
    status: str
    filename: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


backend_app = FastAPI(lifespan=lifespan)


@backend_app.post("/make_pdf", response_model=JobStartResponse)
def create_pdf() -> JobStartResponse:
    job = Job(status="QUEUED")
    with Session(engine) as session:
        session.add(job)
        session.commit()
        session.refresh(job)

    # Push the heavy work to the Celery worker; the client polls /jobs instead
    # of holding the request open.
    make_pdf_with_random_values.delay(job.id)

    return JobStartResponse(message="Started the task", task_id=job.id)


@backend_app.get("/jobs", response_model=JobStatusResponse)
def job_status(job_id: int) -> JobStatusResponse:
    with Session(engine) as session:
        job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"No job with id {job_id}")
    return JobStatusResponse(task_id=job.id, status=job.status, filename=job.filename)


@backend_app.get("/files")
def give_file(fname: str) -> FileResponse:
    # Only serve files that live directly inside OUTPUT_DIR.
    path = (OUTPUT_DIR / fname).resolve()
    if path.parent != OUTPUT_DIR or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path,
        headers={"Content-Disposition": f"attachment; filename={path.name}"},
    )
