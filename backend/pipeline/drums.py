"""
Drum feature extraction from the drums stem.

Per-instrument energy via bandpass filtering:
  kick:     20–120 Hz
  snare:    120–500 Hz
  hihat:    5000–12000 Hz
  cymbal:   8000–20000 Hz  (overlaps hihat — open vs closed distinguished by energy envelope)
  softperc: 200–2000 Hz (brushes, shakers, etc.)

Sharpness per instrument: onset strength at the frame of detected hits.
"""

from __future__ import annotations
import numpy as np
import librosa
from scipy.signal import butter, sosfilt

_BANDS: dict[str, tuple[float, float]] = {
    "kick":     (20.0,   120.0),
    "snare":    (120.0,  500.0),
    "hihat":    (5000.0, 12000.0),
    "cymbal":   (8000.0, 20000.0),
    "softperc": (200.0,  2000.0),
}

_SHARPNESS_WINDOW = 3   # frames around onset peak to capture max strength


def _bandpass_energy(audio: np.ndarray, sr: int, lo: float, hi: float, hop: int) -> np.ndarray:
    """Bandpass filter → per-frame RMS energy, normalised 0–1."""
    nyq = sr / 2.0
    lo_n = max(lo / nyq, 1e-4)
    hi_n = min(hi / nyq, 0.999)
    sos = butter(4, [lo_n, hi_n], btype="bandpass", output="sos")
    filtered = sosfilt(sos, audio)
    rms = librosa.feature.rms(y=filtered, hop_length=hop)[0]
    p99 = np.percentile(rms, 99) or 1.0
    return np.clip(rms / p99, 0.0, 1.0).astype(np.float32)


def _onset_sharpness(audio: np.ndarray, sr: int, hop: int, n_frames: int) -> np.ndarray:
    """Per-frame onset sharpness (0–1)."""
    strength = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop)
    # Pad/trim to n_frames
    if len(strength) < n_frames:
        strength = np.pad(strength, (0, n_frames - len(strength)))
    else:
        strength = strength[:n_frames]
    p99 = np.percentile(strength, 99) or 1.0
    return np.clip(strength / p99, 0.0, 1.0).astype(np.float32)


def extract_drum_features(
    drums_audio: np.ndarray,
    sr: int,
    fps: int = 30,
) -> list[dict]:
    hop = sr // fps
    n_frames = int(np.ceil(len(drums_audio) / hop))

    energies: dict[str, np.ndarray] = {}
    sharpness: dict[str, np.ndarray] = {}

    for name, (lo, hi) in _BANDS.items():
        band_audio = drums_audio.copy()
        nyq = sr / 2.0
        if hi >= nyq * 0.999:
            hi = nyq * 0.999
        if lo <= 0:
            lo = 1.0
        energies[name] = _bandpass_energy(band_audio, sr, lo, hi, hop)

        # Bandpass first, then compute onset sharpness on that band
        sos = butter(4, [lo / nyq, hi / nyq], btype="bandpass", output="sos")
        filtered = sosfilt(sos, band_audio)
        sharpness[name] = _onset_sharpness(filtered.astype(np.float32), sr, hop, n_frames)

    frames: list[dict] = []
    for i in range(n_frames):
        def e(name: str) -> float:
            arr = energies[name]
            return round(float(arr[i]) if i < len(arr) else 0.0, 4)

        def s(name: str) -> float:
            arr = sharpness[name]
            return round(float(arr[i]) if i < len(arr) else 0.0, 4)

        frames.append({
            "kick":     e("kick"),
            "snare":    e("snare"),
            "hihat":    e("hihat"),
            "cymbal":   e("cymbal"),
            "softperc": e("softperc"),
            "sharpness": {
                "kick":     s("kick"),
                "snare":    s("snare"),
                "hihat":    s("hihat"),
                "cymbal":   s("cymbal"),
                "softperc": s("softperc"),
            },
        })

    return frames
