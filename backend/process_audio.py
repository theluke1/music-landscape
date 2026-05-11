"""
process_audio.py — Harmonic Landscape audio pipeline
Usage: python process_audio.py <input_audio> [--out <output.hviz>] [--fps 30]

Phases run in order:
  1. Source separation (Demucs)  → 4 stems: vocals, bass, drums, other
  2. Pitch tracking (CREPE)      → melody (vocals) + bass pitch per frame
  3. Chroma + chord matching     → 12-dim chroma + chord root/quality per frame
  4. Drum onset detection        → per-instrument energy + sharpness per frame
  5. Structural segmentation     → [(start, end, label)]
  6. Spectrogram (mel)           → 128-bin row per frame (for Chladni floor)
  7. Perceptual ML               → energy/valence/tension/density (Phase 7, zeros until trained)
  8. Assemble + write .hviz JSON
"""

import json
import time
from pathlib import Path

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


def build_frames(
    fps: int,
    duration_s: float,
    melody_frames: list[dict],
    bass_frames: list[dict],
    chord_frames: list[dict],
    drum_frames: list[dict],
    chroma_frames: list[list[float]],
    spec_frames: list[list[float]],
    perceptual_frames: list[dict],
) -> list[dict]:
    n = len(melody_frames)
    frames = []
    for i in range(n):
        frames.append({
            "t": round(i / fps, 4),
            "melody": melody_frames[i],
            "bass": bass_frames[i],
            "chord": chord_frames[i],
            "drums": drum_frames[i],
            "chroma": chroma_frames[i],
            "spectrogram_row": spec_frames[i],
            "perceptual": perceptual_frames[i],
        })
    return frames


@click.command()
@click.argument("input_audio", type=click.Path(exists=True))
@click.option("--out", default=None, help="Output .hviz path (default: <input>.hviz)")
@click.option("--fps", default=FPS, show_default=True, help="Frames per second")
@click.option("--device", default="cpu", show_default=True, help="Demucs device: cpu | cuda | mps")
def main(input_audio: str, out: str | None, fps: int, device: str) -> None:
    audio_path = Path(input_audio)
    out_path = Path(out) if out else audio_path.with_suffix(".hviz")

    print(f"[1/7] Separating stems ({device})…")
    t0 = time.time()
    stems = separate_stems(audio_path, device=device)
    # stems = { "vocals": (samples, sr), "bass": …, "drums": …, "other": … }
    print(f"      done in {time.time()-t0:.1f}s")

    sr = stems["vocals"][1]
    duration_s = len(stems["vocals"][0]) / sr

    print("[2/7] Tracking pitch…")
    melody_frames, bass_frames = track_pitch(stems, fps=fps)

    print("[3/7] Extracting chroma + chords…")
    chroma_frames, chord_frames = extract_chroma_and_chords(stems, fps=fps)

    print("[4/7] Extracting drum features…")
    drum_frames = extract_drum_features(stems["drums"], sr=sr, fps=fps)

    print("[5/7] Structural segmentation…")
    segments = extract_segments(stems, sr=sr)

    print("[6/7] Extracting spectrogram…")
    spec_frames = extract_spectrogram(audio_path, fps=fps, n_mels=128)

    print("[7/7] Running perceptual model…")
    perceptual_model = PerceptualModel()
    perceptual_frames = perceptual_model.predict(
        chroma_frames=chroma_frames,
        melody_frames=melody_frames,
        drum_frames=drum_frames,
    )

    print("Assembling .hviz…")
    frames = build_frames(
        fps=fps,
        duration_s=duration_s,
        melody_frames=melody_frames,
        bass_frames=bass_frames,
        chord_frames=chord_frames,
        drum_frames=drum_frames,
        chroma_frames=chroma_frames,
        spec_frames=spec_frames,
        perceptual_frames=perceptual_frames,
    )

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
    print(f"Written: {out_path}  ({size_mb:.1f} MB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
