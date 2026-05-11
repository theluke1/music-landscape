"""
Chroma extraction and chord template matching.

Uses librosa CQT-based chroma on (vocals + other) mix.
Chord templates: 24 templates (12 maj + 12 min) → extended to 7ths/dim for SH orb color.

Template qualities supported (for chord.quality field):
  "maj", "min", "dom7", "maj7", "min7", "dim", "aug", "hdim7", "sus2", "sus4"
"""

from __future__ import annotations
import numpy as np
import librosa

# Chord template intervals (semitones above root, normalised binary vector len=12)
_TEMPLATES: dict[str, list[int]] = {
    "maj":   [0, 4, 7],
    "min":   [0, 3, 7],
    "dom7":  [0, 4, 7, 10],
    "maj7":  [0, 4, 7, 11],
    "min7":  [0, 3, 7, 10],
    "dim":   [0, 3, 6],
    "aug":   [0, 4, 8],
    "hdim7": [0, 3, 6, 10],
    "sus2":  [0, 2, 7],
    "sus4":  [0, 5, 7],
}

_CONF_THRESHOLD = 0.4


def _build_template_matrix() -> tuple[np.ndarray, list[tuple[int, str]]]:
    """Build (n_templates, 12) matrix and parallel label list."""
    rows = []
    labels: list[tuple[int, str]] = []
    for quality, intervals in _TEMPLATES.items():
        for root in range(12):
            template = np.zeros(12)
            for interval in intervals:
                template[(root + interval) % 12] = 1.0
            template /= np.linalg.norm(template)
            rows.append(template)
            labels.append((root, quality))
    return np.stack(rows), labels


_TEMPLATE_MATRIX, _TEMPLATE_LABELS = _build_template_matrix()


def extract_chroma_and_chords(
    stems: dict[str, tuple[np.ndarray, int]],
    fps: int = 30,
) -> tuple[list[list[float]], list[dict]]:
    vocals, sr = stems["vocals"]
    other, _ = stems["other"]

    # Mix vocals + other for harmonic content
    mix = vocals + other
    hop = sr // fps

    chroma = librosa.feature.chroma_cqt(y=mix, sr=sr, hop_length=hop, bins_per_octave=36)
    # chroma shape: (12, n_frames) — normalise columns
    chroma_norm = chroma / (chroma.max(axis=0, keepdims=True) + 1e-8)

    chroma_frames: list[list[float]] = []
    chord_frames: list[dict] = []

    for i in range(chroma_norm.shape[1]):
        col = chroma_norm[:, i]
        chroma_frames.append([round(float(v), 4) for v in col])

        # Template match
        sims = _TEMPLATE_MATRIX @ col
        best_idx = int(np.argmax(sims))
        conf = float(sims[best_idx])

        if conf >= _CONF_THRESHOLD:
            root, quality = _TEMPLATE_LABELS[best_idx]
            chord_frames.append({
                "root": root,
                "quality": quality,
                "conf": round(conf, 3),
            })
        else:
            chord_frames.append({"root": None, "quality": None, "conf": round(conf, 3)})

    return chroma_frames, chord_frames
