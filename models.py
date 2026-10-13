"""SQLModel tables and the SQLite engine."""

from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine

from config import DATABASE_URL


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = "QUEUED"
    filename: Optional[str] = None


engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_job(job_id: int) -> Optional[Job]:
    with Session(engine) as session:
        return session.get(Job, job_id)


def update_job(job_id: int, **fields) -> None:
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if job is None:
            raise ValueError(f"No job with id {job_id}")
        for key, value in fields.items():
            setattr(job, key, value)
        session.add(job)
        session.commit()
