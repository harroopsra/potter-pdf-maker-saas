"""Celery app and the background task that generates the PDF."""

import random
import time

import requests
from celery import Celery
from fpdf import FPDF

from config import CELERY_BROKER_URL, OUTPUT_DIR, WORK_SECONDS
from models import update_job

celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

WIZARD_WORLD_API = "https://wizard-world-api.herokuapp.com/Houses"


@celery_app.task()
def make_pdf_with_random_values(job_id: int) -> None:
    update_job(job_id, status="PROCESSING")

    # Simulated slow work, so the client has something to poll for.
    time.sleep(WORK_SECONDS)

    try:
        response = requests.get(WIZARD_WORLD_API, timeout=10)
        response.raise_for_status()
        chosen_house = random.choice(response.json())["name"]

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(text=chosen_house)

        filename = f"potter_report_{job_id}.pdf"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        pdf.output(str(OUTPUT_DIR / filename))

        update_job(job_id, status="COMPLETED", filename=filename)
    except Exception:
        update_job(job_id, status="FAILED")
        raise
