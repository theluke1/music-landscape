"""
FastAPI server — Harmonic Landscape backend

Endpoints:
  POST   /process          — upload audio file → returns {job_id}
  GET    /stream/{job_id}  — Server-Sent Events progress stream (primary)
  GET    /status/{job_id}  — polling fallback for environments without SSE
  GET    /hviz/{job_id}    — download completed .hviz JSON
  GET    /audio/{job_id}   — stream original audio for WebAudio playback
  DELETE /jobs/{job_id}    — delete job + files
  GET    /health           — health check for deploy platforms

Concurrency: Demucs uses ~3–6 GB RAM. Max 1 concurrent job via a semaphore.
The pipeline runs in a ThreadPoolExecutor (CPU-bound, not async-compatible).
Progress is forwarded to SSE clients via per-job asyncio.Queue.

Start with:
  cd backend && uvicorn api.server:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.responses import StreamingResponse

# Pipeline lives one directory up from api/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from process_audio import run_pipeline

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Harmonic Landscape API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    # FastAPI's CORSMiddleware doesn't support wildcard subdomains like *.vercel.app.
    # For a portfolio project, allow_origins=["*"] is fine — there's no auth here.
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR = Path(__file__).parent.parent / "jobs"
JOBS_DIR.mkdir(exist_ok=True)

# Only one Demucs job at a time
_pipeline_semaphore = asyncio.Semaphore(1)
_executor = ThreadPoolExecutor(max_workers=1)


# ---------------------------------------------------------------------------
# Job state
# ---------------------------------------------------------------------------

@dataclass
class JobState:
    job_id: str
    audio_path: Path
    status: str = "queued"      # queued | processing | done | error
    step: str = ""
    pct: int = 0
    msg: str = "Queued"
    error: str | None = None
    hviz_path: Path | None = None
    # SSE subscribers receive dicts from this queue; None = stream closed
    _queue: asyncio.Queue = field(default_factory=asyncio.Queue)

    def snapshot(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "step": self.step,
            "pct": self.pct,
            "msg": self.msg,
            "error": self.error,
        }

    def push(self, step: str, pct: int, msg: str) -> None:
        self.step = step
        self.pct = pct
        self.msg = msg
        self._queue.put_nowait(self.snapshot())

    def finish(self) -> None:
        self.status = "done"
        self.pct = 100
        self._queue.put_nowait({**self.snapshot(), "status": "done"})
        self._queue.put_nowait(None)   # sentinel — close the stream

    def fail(self, error: str) -> None:
        self.status = "error"
        self.error = error
        self._queue.put_nowait({**self.snapshot(), "status": "error", "error": error})
        self._queue.put_nowait(None)


_jobs: dict[str, JobState] = {}


def _get_job(job_id: str) -> JobState:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "jobs": len(_jobs)})


@app.post("/process")
async def process_audio(file: UploadFile = File(...)) -> JSONResponse:
    """Save uploaded audio and queue the pipeline."""
    job_id = str(uuid.uuid4())[:8]
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir()

    filename = file.filename or "audio.mp3"
    audio_path = job_dir / filename
    audio_path.write_bytes(await file.read())

    job = JobState(job_id=job_id, audio_path=audio_path)
    _jobs[job_id] = job

    asyncio.create_task(_run_job(job))
    return JSONResponse({"job_id": job_id})


@app.get("/stream/{job_id}")
async def stream_progress(job_id: str) -> StreamingResponse:
    """
    Server-Sent Events stream.  Each event is a JSON object:
      data: {"job_id","status","step","pct","msg","error"}\n\n
    The stream closes with a final event when status becomes "done" or "error".
    """
    job = _get_job(job_id)

    async def generator() -> AsyncGenerator[str, None]:
        # Immediately send current state so the client isn't left blank
        yield _sse(job.snapshot())
        while True:
            event = await job._queue.get()
            if event is None:
                break
            yield _sse(event)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
        },
    )


@app.get("/status/{job_id}")
async def job_status(job_id: str) -> JSONResponse:
    """Polling fallback — returns current job snapshot."""
    return JSONResponse(_get_job(job_id).snapshot())


@app.get("/hviz/{job_id}")
async def get_hviz(job_id: str) -> FileResponse:
    job = _get_job(job_id)
    if job.hviz_path is None or not job.hviz_path.exists():
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(job.hviz_path, media_type="application/json")


@app.get("/audio/{job_id}")
async def get_audio(job_id: str) -> FileResponse:
    job = _get_job(job_id)
    return FileResponse(job.audio_path)


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str) -> JSONResponse:
    job = _get_job(job_id)
    job_dir = JOBS_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    del _jobs[job_id]
    return JSONResponse({"deleted": job_id})


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

async def _run_job(job: JobState) -> None:
    """Acquire semaphore then run pipeline in thread pool."""
    loop = asyncio.get_running_loop()

    async with _pipeline_semaphore:
        job.status = "processing"
        job.push("queued", 0, "Starting pipeline…")

        out_path = job.audio_path.with_suffix(".hviz")

        def on_progress(step: str, pct: int, msg: str) -> None:
            # Called from the pipeline thread — post to the event loop safely
            loop.call_soon_threadsafe(job.push, step, pct, msg)

        def run() -> None:
            run_pipeline(
                audio_path=job.audio_path,
                out_path=out_path,
                on_progress=on_progress,
            )

        try:
            await loop.run_in_executor(_executor, run)
            job.hviz_path = out_path
            job.finish()
        except Exception as exc:
            job.fail(str(exc))


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
