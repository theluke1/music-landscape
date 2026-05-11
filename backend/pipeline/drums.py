"""
Drum feature extraction from the drums stem.

Per-instrument energy via bandpass filtering:
  kick:     20–120 Hz
  snare:    120–500 Hz
  hihat:    5000–12000 Hz
  cymbal:   8000–(nyquist) Hz   (open vs closed distinguished by energy envelope)
  softperc: 200–2000 Hz         (brushes, shakers, etc.)

Sharpness per instrument: per-frame onset strength on the bandpassed signal,
normalised 0–1.  High sharpness = sharp transient (hard stick hit vs brush).

Frame count: all arrays are trimmed to min(librosa_rms_length, n_expected)
before being zipped into the output list.
"""

from __future__ import annotations
import numpy as np
import librosa
from scipy.signal import butter, sosfilt

_BANDS: dict[str, tuple[float, float]] = {
    "kick":     (20.0,    120.0),
    "snare":    (120.0,   500.0),
    "hihat":    (5000.0,  12000.0),
    "cymbal":   (8000.0,  20000.0),
    "softperc": (200.0,   2000.0),
}


def _safe_bandpass(lo: float, hi: float, nyq: float) -> np.ndarray:
    """Return a butterworth SOS array, clamping frequencies to valid range."""
    lo_n = max(lo / nyq, 1e-4)
    hi_n = min(hi / nyq, 0.999)
    return butter(4, [lo_n, hi_n], btype="bandpass", output="sos")


def _rms(audio: np.ndarray, hop: int) -> np.ndarray:
    arr = librosa.feature.rms(y=audio, hop_length=hop)[0]
    p99 = float(np.percentile(arr, 99)) or 1.0
    return np.clip(arr / p99, 0.0, 1.0).astype(np.float32)


def _onset_strength(audio: np.ndarray, sr: int, hop: int) -> np.ndarray:
    arr = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop)
    p99 = float(np.percentile(arr, 99)) or 1.0
    return np.clip(arr / p99, 0.0, 1.0).astype(np.float32)


def extract_drum_features(
    drums_audio: np.ndarray,
    sr: int,
    fps: int = 30,
) -> list[dict]:
    hop = sr // fps
    nyq = sr / 2.0

    energies: dict[str, np.ndarray] = {}
    sharpness: dict[str, np.ndarray] = {}

    for name, (lo, hi) in _BANDS.items():
        # Clamp hi to just below Nyquist — cymbal upper edge varies with SR
        hi = min(hi, nyq * 0.999)
        sos = _safe_bandpass(lo, hi, nyq)
        filtered = sosfilt(sos, drums_audio).astype(np.float32)
        energies[name] = _rms(filtered, hop)
        sharpness[name] = _onset_strength(filtered, sr, hop)

    # Determine frame count from the shortest array (all should be nearly equal)
    n = min(len(a) for a in energies.values())

    frames: list[dict] = []
    for i in range(n):
        frames.append({
            "kick":     round(float(energies["kick"][i]),     4),
            "snare":    round(float(energies["snare"][i]),    4),
            "hihat":    round(float(energies["hihat"][i]),    4),
            "cymbal":   round(float(energies["cymbal"][i]),   4),
            "softperc": round(float(energies["softperc"][i]), 4),
            "sharpness": {
                "kick":     round(float(sharpness["kick"][i]),     4),
                "snare":    round(float(sharpness["snare"][i]),    4),
                "hihat":    round(float(sharpness["hihat"][i]),    4),
                "cymbal":   round(float(sharpness["cymbal"][i]),   4),
                "softperc": round(float(sharpness["softperc"][i]), 4),
            },
        })

    return frames
