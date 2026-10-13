# 🧙 potter-pdf-maker-saas

[![CI](https://github.com/harroopsra/potter-pdf-maker-saas/actions/workflows/ci.yml/badge.svg)](https://github.com/harroopsra/potter-pdf-maker-saas/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A tiny "SaaS" that generates a PDF naming a random Hogwarts house — built as a learning project to understand how real job-queue architectures work: an API accepts a request, hands the heavy work to a background worker, and the client polls until the result is ready.

**Example output:** [`examples/example_output.pdf`](examples/example_output.pdf) — a Sorting certificate-style page: a school crest at the top, the house name in a banner of house colours, house details and traits, a quote from the Sorting Hat's song, and a footer with the date. Regenerate it with `python scripts/generate_example.py`.

## Why this project exists

I wanted to demystify the "submit a job → wait → download the result" pattern used by real SaaS products (video render farms, report generators, thumbnailers), so I built the smallest possible version of one. Along the way it covers:

- **FastAPI** — a small HTTP API with three endpoints (enqueue, poll, download)
- **Celery + Redis** — pushing work to a background task queue instead of blocking the request
- **The polling pattern** — the client keeps asking "is it done yet?" instead of holding the connection open
- **SQLModel + SQLite** — persisting job state so status survives across processes
- **fpdf2** — laying out a polished PDF: vector-drawn crest, house-colour banner and swatches, a quote box, and typography (plus swapping cp1252 into core fonts for proper em dashes)
- **Consuming a real public API** — house data comes from the [Wizard World API](https://wizard-world-api.herokuapp.com/Houses)
- **Tests & CI** — a pytest suite with the broker and network mocked out, run by GitHub Actions on every push

## How it works

```
client          FastAPI (main.py)       Redis broker        Celery worker (tasks.py)             SQLite (potter.db)
  │                   │                      │                       │                              │
  │ POST /make_pdf ──▶│ create Job ────────────────────────────────────────────────────────────────▶│ status=QUEUED
  │                   │ enqueue task ───────▶│ ──▶ task picked up ──▶│ status=PROCESSING ───────────▶│
  │◀── {task_id} ─────│                      │                       │ sleep WORK_SECONDS            │
  │                   │                      │                       │ fetch house from Wizard World │
  │ GET /jobs?id=… ──▶│ ◀────────────────────────────────────────── status query ──────────────────│
  │◀── {status} ──────│                      │                       │ write potter_report_<id>.pdf  │
  │                   │                      │                       │ status=COMPLETED ────────────▶│
  │ GET /files?fname=potter_report_1.pdf ───▶│ (FileResponse serves the PDF)                        │
```

## Running it yourself

You need Python 3.11+ and Redis.

```bash
# 1. clone and enter the repo
git clone https://github.com/harroopsra/potter-pdf-maker-saas.git
cd potter-pdf-maker-saas

# 2. create an environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # add -r requirements-dev.txt for tests & linting

# 3. start Redis (either way works)
brew services start redis        # macOS via Homebrew
# or: docker run --rm -p 6379:6379 redis
# or: redis-server               # foreground, in its own terminal
```

Then start two processes (each in its own terminal, venv activated):

```bash
# terminal 1 — the web API
uvicorn main:backend_app --reload

# terminal 2 — the background worker
celery -A tasks.celery_app worker --loglevel=info
```

## Using the API

```bash
# 1. enqueue a PDF job
curl -X POST localhost:8000/make_pdf
# → {"message":"Started the task","task_id":1}

# 2. poll until done (the worker sleeps WORK_SECONDS=30 on purpose, to make you feel the async-ness)
curl "localhost:8000/jobs?job_id=1"
# → {"task_id":1,"status":"PROCESSING","filename":null}   … eventually …
# → {"task_id":1,"status":"COMPLETED","filename":"potter_report_1.pdf"}

# 3. download the PDF
curl -OJ "localhost:8000/files?fname=potter_report_1.pdf"
```

## API reference

| Method | Path       | Params  | Returns                                                                 |
|--------|------------|---------|-------------------------------------------------------------------------|
| POST   | `/make_pdf`| —       | `{message, task_id}` — job enqueued                                     |
| GET    | `/jobs`    | `job_id`| `{task_id, status, filename}` — status is `QUEUED` / `PROCESSING` / `COMPLETED` / `FAILED` |
| GET    | `/files`   | `fname` | The generated PDF as an attachment (404 for anything outside the output directory) |

## Configuration

Everything is overridable via environment variables:

| Variable            | Default                    | Purpose                              |
|---------------------|----------------------------|--------------------------------------|
| `DATABASE_URL`      | `sqlite:///potter.db`      | SQLModel database connection         |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery message broker                |
| `OUTPUT_DIR`        | project root               | Where generated PDFs are written     |
| `WORK_SECONDS`      | `30`                       | Simulated work duration in the task  |

## Project layout

```
config.py          environment-driven configuration
models.py          SQLModel Job table + SQLite engine
report.py          the sorting certificate PDF builder
tasks.py           Celery app + the task: fetch house, build PDF
main.py            FastAPI app: enqueue job, poll status, serve file
tests/             pytest suite (broker + network mocked)
scripts/           helper to regenerate the example PDF
examples/          example of the generated PDF
LICENSE            MIT
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest               # runs the whole suite; no Redis or network needed
ruff check .         # lint
```

The tests stub out the Celery broker and the Wizard World API, so they run anywhere — including the GitHub Actions CI workflow that runs on every push. PDF output is checked with `pypdf` text extraction (house name, founder, quote, date), not just "a file appeared".

## Notes & known limitations

- The worker's `time.sleep(WORK_SECONDS)` is intentional — it stands in for genuinely slow work (video encoding, report rendering) so the polling pattern has something to poll for.
- If the Wizard World API is unreachable, the task marks the job `FAILED` and re-raises, so the worker logs the error.
- SQLite is used for simplicity; a real deployment would use Postgres and run the API/worker as separate services.
- The crest on each report is original vector art drawn at fixed page coordinates (so it lands in exactly the same place every time). To use your own artwork instead, drop an image at `assets/hogwarts_logo.png` and it takes over that slot — only use artwork you have the rights to, since official Harry Potter imagery is copyrighted.
- Quotes are short excerpts from the Sorting Hat's song and Dumbledore, attributed on the PDF.

## License

MIT — see [LICENSE](LICENSE).
