# 🧙 potter-pdf-maker-saas

A tiny "SaaS" that generates a PDF naming a random Hogwarts house — built as a learning project to understand how real job-queue architectures work: an API accepts a request, hands the heavy work to a background worker, and the client polls until the result is ready.

**Example output:** [`examples/example_output.pdf`](examples/example_output.pdf) — a one-page PDF with a randomly chosen house (in this run: a house name in plain Helvetica — deliberately minimal).

## Why this project exists

I wanted to demystify the "submit a job → wait → download the result" pattern used by real SaaS products (video render farms, report generators, thumbnailers), so I built the smallest possible version of one. Along the way it covers:

- **FastAPI** — a small HTTP API with three endpoints (enqueue, poll, download)
- **Celery + Redis** — pushing work to a background task queue instead of blocking the request
- **The polling pattern** — the client keeps asking "is it done yet?" instead of holding the connection open
- **SQLModel + SQLite** — persisting job state so status survives across processes
- **fpdf2** — generating a PDF in Python
- **Consuming a real public API** — house data comes from the [Wizard World API](https://wizard-world-api.herokuapp.com/Houses)

## How it works

```
client          FastAPI (main.py)       Redis broker        Celery worker (celery_stuff.py)      SQLite (potter.db)
  │                   │                      │                       │                              │
  │ POST /make_pdf ──▶│ create Job ────────────────────────────────────────────────────────────────▶│ status=STARTED
  │                   │ enqueue task ───────▶│ ──▶ task picked up ──▶│ status=PROCESSING ───────────▶│
  │◀── {task_id} ─────│                      │                       │ sleep 30s (simulated work)    │
  │                   │                      │                       │ fetch house from Wizard World │
  │ GET /jobs?id=… ──▶│ ◀────────────────────────────────────────── status query ──────────────────│
  │◀── {status} ──────│                      │                       │ write hello_world.pdf         │
  │                   │                      │                       │ status=COMPLETED ────────────▶│
  │ GET /files?fname=hello_world.pdf ───────▶│ (FileResponse serves the PDF)                        │
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
pip install -r requirements.txt

# 3. start Redis (either way works)
brew services start redis        # macOS via Homebrew
# or: docker run --rm -p 6379:6379 redis
# or: redis-server               # foreground, in its own terminal
```

Then start three processes (each in its own terminal, venv activated):

```bash
# terminal 1 — the web API
uvicorn main:backend_app --reload

# terminal 2 — the background worker
celery -A celery_stuff.celery_app worker --loglevel=info
```

## Using the API

```bash
# 1. enqueue a PDF job
curl -X POST localhost:8000/make_pdf
# → {"message":"Started the task","task_id":1}

# 2. poll until done (the worker sleeps 30s on purpose, to make you feel the async-ness)
curl "localhost:8000/jobs?job_id=1"
# → {"task_id":"1","status":"PROCESSING"}   … eventually …
# → {"task_id":"1","status":"COMPLETED at hello_world.pdf"}

# 3. download the PDF (written to the project root)
curl -OJ "localhost:8000/files?fname=hello_world.pdf"
```

## API reference

| Method | Path       | Params              | Returns                                              |
|--------|------------|---------------------|------------------------------------------------------|
| POST   | `/make_pdf`| —                   | `{message, task_id}` — job enqueued                  |
| GET    | `/jobs`    | `job_id`            | `{task_id, status}` — `STARTED` / `PROCESSING` / `COMPLETED at hello_world.pdf` |
| GET    | `/files`   | `fname`             | The generated PDF as an attachment                   |

## Project layout

```
main.py          FastAPI app: enqueue job, poll status, serve file
celery_stuff.py  Celery app + the task: fetch house, build PDF
db_stuff.py      SQLModel Job table + SQLite engine
examples/        example of the generated PDF
```

## Notes & known limitations

- The worker's `time.sleep(30)` is intentional — it stands in for genuinely slow work (video encoding, report rendering) so the polling pattern has something to poll for.
- SQLite is used for simplicity; a real deployment would use Postgres and run the API/worker as separate services.
- House data is fetched live from the Wizard World API at job time; if the API is unreachable the task fails and the job status won't reach `COMPLETED`.
- The generated PDF is intentionally bare-bones (just the house name) — the interesting part of this project is the architecture, not the typography.
