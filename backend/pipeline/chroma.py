"""
Chroma extraction and chord template matching.

Uses librosa CQT-based chroma on the (vocals + other) harmonic mix.

Template qualities: maj, min, dom7, maj7, min7, dim, aug, hdim7, sus2, sus4
→ 120 templates total (10 qualities × 12 roots)

Bug fixed vs scaffold: cosine similarity requires both vectors to be L2-normalised.
The scaffold normalised chroma columns by their max value (not L2 norm), biasing
similarity scores toward louder frames.  Fixed: L2-normalise each column before
dot-producting against the L2-normalised template matrix.
"""

from __future__ import annotations
import numpy as np
import librosa

# Chord template intervals (semitones above root)
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

_CONF_THRESHOLD = 0.5   # cosine similarity threshold (higher = more confident)


def _build_template_matrix() -> tuple[np.ndarray, list[tuple[int, str]]]:
    """Build (n_templates, 12) L2-normalised matrix and parallel label list."""
    rows = []
    labels: list[tuple[int, str]] = []
    for quality, intervals in _TEMPLATES.items():
        for root in range(12):
            t = np.zeros(12)
            for iv in intervals:
                t[(root + iv) % 12] = 1.0
            t /= np.linalg.norm(t)
            rows.append(t)
            labels.append((root, quality))
    return np.stack(rows), labels   # (120, 12)


_TEMPLATE_MATRIX, _TEMPLATE_LABELS = _build_template_matrix()


def extract_chroma_and_chords(
    stems: dict[str, tuple[np.ndarray, int]],
    fps: int = 30,
) -> tuple[list[list[float]], list[dict]]:
    vocals, sr = stems["vocals"]
    other, _ = stems["other"]

    mix = vocals + other
    hop = sr // fps

    # CQT chroma with extra octave bins for better pitch resolution
    raw_chroma = librosa.feature.chroma_cqt(
        y=mix, sr=sr, hop_length=hop, bins_per_octave=36
    )   # shape: (12, n_frames)

    chroma_frames: list[list[float]] = []
    chord_frames: list[dict] = []

    for i in range(raw_chroma.shape[1]):
        col = raw_chroma[:, i].astype(np.float64)

        # Store the raw chroma (max-normalised) for the visualiser
        col_max = col.max()
        col_display = (col / (col_max + 1e-8)).tolist()
        chroma_frames.append([round(v, 4) for v in col_display])

        # L2-normalise for cosine similarity template match
        col_norm = col_max  # reuse
        l2 = float(np.linalg.norm(col))
        if l2 < 1e-6:
            # Silent frame — no chord
            chord_frames.append({"root": None, "quality": None, "conf": 0.0})
            continue

        col_unit = col / l2
        sims = _TEMPLATE_MATRIX @ col_unit   # (120,) cosine similarities in [-1, 1]
        best_idx = int(np.argmax(sims))
        conf = float(sims[best_idx])

        if conf >= _CONF_THRESHOLD:
            root, quality = _TEMPLATE_LABELS[best_idx]
            chord_frames.append({"root": root, "quality": quality, "conf": round(conf, 3)})
        else:
            chord_frames.append({"root": None, "quality": None, "conf": round(conf, 3)})

    return chroma_frames, chord_frames
