import pytest
from sqlmodel import Session, select

from models import Job, create_db_and_tables, engine, get_job, update_job


@pytest.fixture(autouse=True)
def fresh_db():
    create_db_and_tables()
    with Session(engine) as session:
        for job in session.exec(select(Job)).all():
            session.delete(job)
        session.commit()
    yield


def test_create_and_read_job():
    with Session(engine) as session:
        job = Job(status="QUEUED")
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    fetched = get_job(job_id)
    assert fetched is not None
    assert fetched.id == job_id
    assert fetched.status == "QUEUED"
    assert fetched.filename is None


def test_update_job_fields():
    with Session(engine) as session:
        job = Job(status="QUEUED")
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    update_job(job_id, status="COMPLETED", filename="potter_report_1.pdf")

    fetched = get_job(job_id)
    assert fetched.status == "COMPLETED"
    assert fetched.filename == "potter_report_1.pdf"


def test_update_missing_job_raises():
    with pytest.raises(ValueError):
        update_job(999, status="COMPLETED")


def test_get_missing_job_returns_none():
    assert get_job(999) is None
