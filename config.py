"""Environment-driven configuration shared by the API and the worker."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'potter.db'}")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", BASE_DIR)).resolve()

# How long the worker pretends to be busy, to make the polling pattern visible.
WORK_SECONDS = float(os.environ.get("WORK_SECONDS", "30"))
