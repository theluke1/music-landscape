"""
Structural segmentation via librosa agglomerative segmentation.

Returns a list of segment dicts compatible with HvizSegment:
  [{ "start": float, "end": float, "label": str }, ...]

Labels are assigned by cluster index ("seg_0", "seg_1", ...) unless
the number of segments matches a conventional song structure heuristic,
in which case common labels (intro, verse, chorus, bridge, outro) are applied.
"""

from __future__ import annotations
import numpy as np
import librosa


_LABEL_HEURISTIC = {
    1: ["chorus"],
    2: ["verse", "chorus"],
    3: ["intro", "verse", "chorus"],
    4: ["intro", "verse", "chorus", "outro"],
    5: ["intro", "verse", "chorus", "bridge", "outro"],
}


def extract_segments(
    stems: dict[str, tuple[np.ndarray, int]],
    sr: int,
    k: int | None = None,
) -> list[dict]:
    """
    stems: dict with at least "vocals" key
    sr:    sample rate
    k:     number of segments (None = auto-detect via librosa)
    """
    # Use the full mix (sum of all stems) for structural analysis
    mix = sum(audio for audio, _ in stems.values())
    mix = mix.astype(np.float32)

    # CQT chromagram for structural features
    hop_length = 512
    chroma = librosa.feature.chroma_cqt(y=mix, sr=sr, hop_length=hop_length)
    bounds = librosa.segment.agglomerative(chroma, k or _auto_k(mix, sr))
    bound_times = librosa.frames_to_time(bounds, sr=sr, hop_length=hop_length)

    duration = len(mix) / sr
    starts = [0.0] + list(bound_times)
    ends = list(bound_times) + [duration]

    n_segs = len(starts)
    label_map = _LABEL_HEURISTIC.get(n_segs, None)

    segments: list[dict] = []
    for i, (start, end) in enumerate(zip(starts, ends)):
        label = label_map[i] if label_map else f"seg_{i}"
        segments.append({
            "start": round(float(start), 3),
            "end": round(float(end), 3),
            "label": label,
        })

    return segments


def _auto_k(mix: np.ndarray, sr: int) -> int:
    """Heuristic: one segment per ~30s, clamped 2–8."""
    duration = len(mix) / sr
    return int(np.clip(round(duration / 30), 2, 8))
