"""
smoke_test.py — validate the pipeline end-to-end without a real audio file.

Generates a 10-second synthetic signal (sum of harmonically-rich sine waves),
bypasses Demucs by faking the stems dict, then runs steps 2–8 of the pipeline
and validates the .hviz output schema.

Usage:
    cd backend
    python smoke_test.py

What it tests:
  - CREPE pitch tracking (melody + bass)
  - Chroma extraction + chord template match
  - Drum bandpass energy + onset sharpness
  - Structural segmentation
  - Mel spectrogram
  - Perceptual model stub (zeros)
  - Full .hviz JSON schema conformance

What it does NOT test:
  - Demucs separation (requires ~3 GB model download + GPU/CPU time)
  - Real-world audio (pitch accuracy, chord recall, etc.)
"""

from __future__ import annotations
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf


# ---------------------------------------------------------------------------
# Synthetic audio: 10 s of C major chord (C4 + E4 + G4) + bass C2
# ---------------------------------------------------------------------------
SR = 44100
DURATION = 10.0
FPS = 30


def _make_synthetic_audio() -> np.ndarray:
    t = np.linspace(0, DURATION, int(SR * DURATION), endpoint=False)
    # Melody: C4 (261.6 Hz) + harmonics, fading in/out
    melody = (
        0.4 * np.sin(2 * np.pi * 261.63 * t) +
        0.2 * np.sin(2 * np.pi * 523.25 * t) +
        0.1 * np.sin(2 * np.pi * 329.63 * t)   # E4
    )
    # Bass: C2 (65.4 Hz)
    bass = 0.5 * np.sin(2 * np.pi * 65.41 * t)
    # Drums: short clicks at 1 Hz (simulated kick)
    drums = np.zeros_like(t)
    for beat in np.arange(0, DURATION, 0.5):
        idx = int(beat * SR)
        drums[idx:idx+100] = 0.8 * np.hanning(100)
    # Other: soft pad
    other = 0.1 * np.sin(2 * np.pi * 392.0 * t)   # G4

    full_mix = melody + bass * 0.5 + drums + other
    full_mix /= np.abs(full_mix).max() + 1e-8
    return full_mix.astype(np.float32), melody.astype(np.float32), bass.astype(np.float32), drums.astype(np.float32), other.astype(np.float32)


def _fake_stems(mix, melody, bass_sig, drums_sig, other):
    """Build a stems dict shaped like separate_stems() output."""
    return {
        "vocals": (melody,   SR),
        "bass":   (bass_sig, SR),
        "drums":  (drums_sig, SR),
        "other":  (other,    SR),
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def main() -> None:
    print("Generating synthetic audio…")
    mix, melody, bass_sig, drums_sig, other = _make_synthetic_audio()
    stems = _fake_stems(mix, melody, bass_sig, drums_sig, other)

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "smoke.wav"
        hviz_path  = Path(tmpdir) / "smoke.hviz"
        sf.write(str(audio_path), mix, SR)

        # Patch sys.path so pipeline imports work from backend/
        sys.path.insert(0, str(Path(__file__).parent))

        from pipeline.pitch     import track_pitch
        from pipeline.chroma    import extract_chroma_and_chords
        from pipeline.drums     import extract_drum_features
        from pipeline.structure import extract_segments
        from pipeline.stft      import extract_spectrogram
        from models.perceptual  import PerceptualModel

        results: dict[str, object] = {}

        print("[1/6] Pitch tracking…")
        t0 = time.time()
        melody_frames, bass_frames = track_pitch(stems, fps=FPS)
        results["pitch_frames"] = len(melody_frames)
        print(f"      {len(melody_frames)} melody frames, {len(bass_frames)} bass frames  ({time.time()-t0:.1f}s)")

        print("[2/6] Chroma + chords…")
        t0 = time.time()
        chroma_frames, chord_frames = extract_chroma_and_chords(stems, fps=FPS)
        results["chroma_frames"] = len(chroma_frames)
        print(f"      {len(chroma_frames)} frames  ({time.time()-t0:.1f}s)")

        print("[3/6] Drum features…")
        t0 = time.time()
        drum_frames = extract_drum_features(drums_sig, sr=SR, fps=FPS)
        results["drum_frames"] = len(drum_frames)
        print(f"      {len(drum_frames)} frames  ({time.time()-t0:.1f}s)")

        print("[4/6] Structure…")
        t0 = time.time()
        segments = extract_segments(stems, sr=SR)
        results["segments"] = len(segments)
        print(f"      {len(segments)} segments: {[s['label'] for s in segments]}  ({time.time()-t0:.1f}s)")

        print("[5/6] Spectrogram…")
        t0 = time.time()
        spec_frames = extract_spectrogram(audio_path, fps=FPS, n_mels=128)
        results["spec_frames"] = len(spec_frames)
        print(f"      {len(spec_frames)} frames  ({time.time()-t0:.1f}s)")

        print("[6/6] Perceptual model (stub)…")
        perceptual_frames = PerceptualModel().predict(chroma_frames, melody_frames, drum_frames)

        # Assemble minimal .hviz
        n = min(len(melody_frames), len(bass_frames), len(chroma_frames),
                len(chord_frames), len(drum_frames), len(spec_frames))
        frames = [
            {
                "t": round(i / FPS, 4),
                "melody": melody_frames[i],
                "bass": bass_frames[i],
                "chord": chord_frames[i],
                "drums": drum_frames[i],
                "chroma": chroma_frames[i],
                "spectrogram_row": spec_frames[i],
                "perceptual": perceptual_frames[i],
            }
            for i in range(n)
        ]
        hviz = {
            "meta": {"title": "smoke_test", "duration_s": DURATION, "fps": FPS, "stem_sr": SR, "version": "0.1"},
            "frames": frames,
            "segments": segments,
        }
        hviz_path.write_text(json.dumps(hviz, separators=(",", ":")))

        # ----- Schema validation -----
        print("\nValidating schema…")
        errors: list[str] = []

        if len(frames) < int(DURATION * FPS * 0.9):
            errors.append(f"Too few frames: {len(frames)} (expected ~{int(DURATION*FPS)})")

        sample = frames[len(frames)//2]
        for key in ("melody", "bass", "chord", "drums", "chroma", "spectrogram_row", "perceptual"):
            if key not in sample:
                errors.append(f"Frame missing key: {key}")

        if len(sample["chroma"]) != 12:
            errors.append(f"chroma length {len(sample['chroma'])} ≠ 12")

        if len(sample["spectrogram_row"]) != 128:
            errors.append(f"spectrogram_row length {len(sample['spectrogram_row'])} ≠ 128")

        for k in ("energy", "valence", "tension", "density"):
            if k not in sample["perceptual"]:
                errors.append(f"perceptual missing: {k}")

        if errors:
            print("FAILED:")
            for e in errors:
                print(f"  ✗ {e}")
            sys.exit(1)
        else:
            size_kb = hviz_path.stat().st_size / 1024
            print(f"PASSED  ({n} frames, {size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
