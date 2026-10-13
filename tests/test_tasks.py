import random
import time

import pytest
import requests
from sqlmodel import Session

import tasks
from config import OUTPUT_DIR
from models import Job, create_db_and_tables, engine, get_job


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return [{"name": "Gryffindor"}, {"name": "Ravenclaw"}]


def make_job() -> int:
    create_db_and_tables()
    with Session(engine) as session:
        job = Job(status="QUEUED")
        session.add(job)
        session.commit()
        session.refresh(job)
        return job.id


def test_task_writes_pdf_and_completes(monkeypatch):
    job_id = make_job()

    monkeypatch.setattr(tasks.requests, "get", lambda url, timeout: FakeResponse())
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    tasks.make_pdf_with_random_values.run(job_id)

    job = get_job(job_id)
    assert job.status == "COMPLETED"
    assert job.filename == f"potter_report_{job_id}.pdf"

    pdf_path = OUTPUT_DIR / job.filename
    assert pdf_path.is_file()
    assert pdf_path.read_bytes().startswith(b"%PDF")


def test_task_marks_job_failed_when_api_is_down(monkeypatch):
    job_id = make_job()

    def broken_get(url, timeout):
        raise requests.RequestException("API is down")

    monkeypatch.setattr(tasks.requests, "get", broken_get)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    with pytest.raises(requests.RequestException):
        tasks.make_pdf_with_random_values.run(job_id)

    job = get_job(job_id)
    assert job.status == "FAILED"
    assert job.filename is None
