from celery import Celery
import requests
import random
from fpdf import FPDF
from db_stuff import engine, Job
from sqlmodel import Session, select
import time

celery_app = Celery('tasks',broker="redis://localhost:6379/0")

@celery_app.task()
def make_pdf_with_random_values(job_id):
    with Session(engine) as session:
        statement = select(Job).where(Job.id==job_id)
        results = session.exec(statement)
        job = results.one()
        job.status = "PROCESSING"
        session.add(job)
        session.commit()
        session.refresh(job)
    
    time.sleep(30)

    response = requests.get("http://wizard-world-api.herokuapp.com/Houses")
    chosen_house = random.choice(response.json())["name"]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica',size=12)
    pdf.cell(text=chosen_house)
    pdf.output("hello_world.pdf")
    
    with Session(engine) as session:
        statement = select(Job).where(Job.id==job_id)
        results = session.exec(statement)
        job = results.one()
        job.status = "COMPLETED at hello_world.pdf"
        session.add(job)
        session.commit()
        session.refresh(job)

