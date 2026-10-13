"""Test configuration: isolate the DB and PDF output before any app import."""

import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/potter.db"
os.environ["OUTPUT_DIR"] = tempfile.mkdtemp()
os.environ["WORK_SECONDS"] = "0"
