from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import main
from config import OUTPUT_DIR
from models import create_db_and_tables


@pytest.fixture()
def client(monkeypatch):
    create_db_and_tables()
    # Don't talk to Redis in tests: record the enqueue instead.
    enqueued = []
    monkeypatch.setattr(
        main,
        "make_pdf_with_random_values",
        SimpleNamespace(delay=lambda job_id: enqueued.append(job_id)),
    )
    with TestClient(main.backend_app) as test_client:
        test_client.enqueued = enqueued
        yield test_client


def test_make_pdf_enqueues_job(client):
    response = client.post("/make_pdf")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Started the task"
    assert isinstance(body["task_id"], int)
    assert client.enqueued == [body["task_id"]]


def test_jobs_returns_status(client):
    task_id = client.post("/make_pdf").json()["task_id"]

    response = client.get("/jobs", params={"job_id": task_id})

    assert response.status_code == 200
    assert response.json() == {"task_id": task_id, "status": "QUEUED", "filename": None}


def test_jobs_unknown_id_returns_404(client):
    response = client.get("/jobs", params={"job_id": 12345})

    assert response.status_code == 404
    assert response.json()["detail"] == "No job with id 12345"


def test_jobs_rejects_non_numeric_id(client):
    response = client.get("/jobs", params={"job_id": "abc"})

    assert response.status_code == 422


def test_files_returns_pdf_as_attachment(client):
    (OUTPUT_DIR / "potter_report_1.pdf").write_bytes(b"%PDF-1.3 fake")

    response = client.get("/files", params={"fname": "potter_report_1.pdf"})

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert response.headers["content-disposition"] == "attachment; filename=potter_report_1.pdf"


def test_files_missing_returns_404(client):
    response = client.get("/files", params={"fname": "nope.pdf"})

    assert response.status_code == 404


def test_files_rejects_path_traversal(client):
    response = client.get("/files", params={"fname": "../potter.db"})

    assert response.status_code == 404
