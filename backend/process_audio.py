"""
process_audio.py — Harmonic Landscape audio pipeline

Public API:
  run_pipeline(audio_path, out_path, fps, device, on_progress) → dict
      Core pipeline — importable by the API server, no subprocess needed.
      on_progress(step_key, pct, message) is called at each stage.

CLI (thin wrapper around run_pipeline):
  python process_audio.py <input_audio> [--out <output.hviz>] [--fps 30] [--device cpu]

Pipeline stages and their progress allocations:
  separate   0 → 50  (Demucs — dominates wall time)
  pitch     50 → 70  (CREPE on 2 stems)
  chroma    70 → 78
  drums     78 → 84
  structure 84 → 88
  stft      88 → 93
  perceptual 93 → 96
  assemble  96 → 100
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

import click
import numpy as np

from pipeline.separate import separate_stems
from pipeline.pitch import track_pitch
from pipeline.chroma import extract_chroma_and_chords
from pipeline.drums import extract_drum_features
from pipeline.structure import extract_segments
from pipeline.stft import extract_spectrogram
from models.perceptual import PerceptualModel

FPS = 30
HVIZ_VERSION = "0.1"

ProgressCallback = Callable[[str, int, str], None]


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    audio_path: Path,
    out_path: Path,
    fps: int = FPS,
    device: str = "cpu",
    on_progress: ProgressCallback | None = None,
) -> dict:
    """
    Run the full audio analysis pipeline.

    Parameters
    ----------
    audio_path  : input audio file
    out_path    : where to write the .hviz JSON
    fps         : feature frames per second (default 30)
    device      : Demucs/CREPE device — "cpu", "cuda", or "mps"
    on_progress : optional callback(step_key, pct_int, message_str)

    Returns
    -------
    The assembled hviz dict (also written to out_path).
    """
    def progress(step: str, pct: int, msg: str) -> None:
        if on_progress:
            on_progress(step, pct, msg)

    # 1 — Source separation
    progress("separate", 0, f"Separating stems with Demucs ({device})…")
    t0 = time.time()
    stems = separate_stems(audio_path, device=device)
    progress("separate", 50, f"Stems separated in {time.time()-t0:.1f}s")

    sr = stems["vocals"][1]
    duration_s = len(stems["vocals"][0]) / sr

    # 2 — Pitch tracking
    progress("pitch", 50, "Tracking melody pitch (CREPE full)…")
    melody_frames, bass_frames = track_pitch(stems, fps=fps)
    progress("pitch", 70, f"Pitch tracked — {len(melody_frames)} frames")

    # 3 — Chroma + chords
    progress("chroma", 70, "Extracting chroma and matching chord templates…")
    chroma_frames, chord_frames = extract_chroma_and_chords(stems, fps=fps)
    progress("chroma", 78, "Chroma done")

    # 4 — Drum features
    progress("drums", 78, "Extracting drum energies and sharpness…")
    drum_frames = extract_drum_features(stems["drums"][0], sr=sr, fps=fps)
    progress("drums", 84, "Drum features done")

    # 5 — Structure
    progress("structure", 84, "Segmenting song structure…")
    segments = extract_segments(stems, sr=sr)
    progress("structure", 88, f"Found {len(segments)} segments")

    # 6 — Spectrogram
    progress("stft", 88, "Computing mel spectrogram…")
    spec_frames = extract_spectrogram(audio_path, fps=fps, n_mels=128)
    progress("stft", 93, "Spectrogram done")

    # 7 — Perceptual model
    progress("perceptual", 93, "Running perceptual model…")
    perceptual_model = PerceptualModel()
    perceptual_frames = perceptual_model.predict(
        chroma_frames=chroma_frames,
        melody_frames=melody_frames,
        drum_frames=drum_frames,
    )
    progress("perceptual", 96, "Perceptual features done")

    # 8 — Assemble + write
    progress("assemble", 96, "Assembling .hviz…")
    n = min(len(melody_frames), len(bass_frames))
    frames = [
        {
            "t": round(i / fps, 4),
            "melody": melody_frames[i],
            "bass": bass_frames[i],
            "chord": chord_frames[i],
            "drums": drum_frames[i],
            "chroma": chroma_frames[i],
            "spectrogram_row": spec_frames[i] if i < len(spec_frames) else [],
            "perceptual": perceptual_frames[i],
        }
        for i in range(n)
    ]

    hviz = {
        "meta": {
            "title": audio_path.stem,
            "duration_s": round(duration_s, 3),
            "fps": fps,
            "stem_sr": sr,
            "version": HVIZ_VERSION,
        },
        "frames": frames,
        "segments": segments,
    }

    out_path.write_text(json.dumps(hviz, separators=(",", ":")))
    size_mb = out_path.stat().st_size / 1e6
    progress("assemble", 100, f"Written {out_path.name} ({size_mb:.1f} MB, {len(frames)} frames)")

    return hviz


# ---------------------------------------------------------------------------
# CLI (thin wrapper)
# ---------------------------------------------------------------------------

@click.command()
@click.argument("input_audio", type=click.Path(exists=True))
@click.option("--out", default=None, help="Output .hviz path (default: <input>.hviz)")
@click.option("--fps", default=FPS, show_default=True, help="Frames per second")
@click.option("--device", default="cpu", show_default=True, help="cpu | cuda | mps")
def cli(input_audio: str, out: str | None, fps: int, device: str) -> None:
    audio_path = Path(input_audio)
    out_path = Path(out) if out else audio_path.with_suffix(".hviz")

    def on_progress(step: str, pct: int, msg: str) -> None:
        print(f"[{pct:3d}%] {msg}")

    run_pipeline(audio_path, out_path, fps=fps, device=device, on_progress=on_progress)


if __name__ == "__main__":
    cli()
