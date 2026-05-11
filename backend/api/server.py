"""
FastAPI server — serves .hviz files and triggers processing jobs.

Endpoints:
  POST /process          — upload audio → run pipeline → return job_id
  GET  /status/{job_id}  — poll processing progress
  GET  /hviz/{job_id}    — download completed .hviz JSON
  GET  /audio/{job_id}   — stream original audio for WebAudio playback
"""

import asyncio
import json
import subprocess
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

app = FastAPI(title="Harmonic Landscape API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://*.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR = Path(__file__).parent.parent / "jobs"
JOBS_DIR.mkdir(exist_ok=True)

# In-memory job registry — replace with Redis for multi-worker deploys
_jobs: dict[str, dict] = {}


@app.post("/process")
async def process_audio(file: UploadFile = File(...)) -> JSONResponse:
    """Accept an audio file, kick off background processing, return job_id."""
    job_id = str(uuid.uuid4())[:8]
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir()

    audio_path = job_dir / file.filename
    audio_path.write_bytes(await file.read())

    _jobs[job_id] = {"status": "queued", "progress": 0, "error": None}

    asyncio.create_task(_run_pipeline(job_id, audio_path))
    return JSONResponse({"job_id": job_id})


@app.get("/status/{job_id}")
async def job_status(job_id: str) -> JSONResponse:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse(_jobs[job_id])


@app.get("/hviz/{job_id}")
async def get_hviz(job_id: str) -> FileResponse:
    job_dir = JOBS_DIR / job_id
    hviz_files = list(job_dir.glob("*.hviz"))
    if not hviz_files:
        raise HTTPException(status_code=404, detail="Not ready")
    return FileResponse(hviz_files[0], media_type="application/json")


@app.get("/audio/{job_id}")
async def get_audio(job_id: str) -> FileResponse:
    job_dir = JOBS_DIR / job_id
    audio_files = [f for f in job_dir.iterdir() if f.suffix in {".mp3", ".wav", ".flac", ".ogg"}]
    if not audio_files:
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(audio_files[0])


async def _run_pipeline(job_id: str, audio_path: Path) -> None:
    _jobs[job_id]["status"] = "processing"
    pipeline_script = Path(__file__).parent.parent / "process_audio.py"
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(pipeline_script), str(audio_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = stderr.decode()[-500:]
    else:
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["progress"] = 100
