from fastapi import FastAPI
from fastapi.responses import FileResponse
from celery_stuff import make_pdf_with_random_values, celery_app
from celery.result import AsyncResult
from db_stuff import create_db_and_tables, engine, Job
from contextlib import asynccontextmanager
from sqlmodel import Session, select

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

backend_app = FastAPI(lifespan=lifespan)


@backend_app.post("/make_pdf")
def create_pdf():
    #mark started in DB
    job = Job(status="STARTED")
    with Session(engine) as session:
        session.add(job)
        session.commit()
        session.refresh(job)
    #send to celery
    make_pdf_with_random_values.delay(job.id)
    ## We async push to Redis and then Celery does the job on its own
    # basically redis will run separately in the terminal
    # we create a job, push the job to redis, and then we're done
    # the client has to poll (so maybe make a get) to check if Job is ready. if it is, we return the PDF.

    return {"message": "Started the task", "task_id":job.id}

@backend_app.get("/jobs")
def is_finished(job_id:str):
    with Session(engine) as session:
        statement = select(Job).where(Job.id==job_id)
        results = session.exec(statement)
        job = results.one()

    return {
        "task_id": job_id,
        "status": job.status
    }
    
    
@backend_app.get("/files")
def give_file(fname:str):
    pdf_headers= {"Content-Disposition": "attachment; filename=final_report.pdf"}
    return FileResponse(fname, headers=pdf_headers)