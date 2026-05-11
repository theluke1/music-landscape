"""
Mel spectrogram extraction on the full mix for the Chladni floor shader.

Returns a list of 128-bin mel-scale rows, one per frame, normalised 0–1.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import librosa


def extract_spectrogram(
    audio_path: Path,
    fps: int = 30,
    n_mels: int = 128,
) -> list[list[float]]:
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    hop = sr // fps

    mel = librosa.feature.melspectrogram(y=y, sr=sr, hop_length=hop, n_mels=n_mels)
    mel_db = librosa.power_to_db(mel, ref=np.max)

    # Normalise: shift so min=0, scale so max=1
    mel_db -= mel_db.min()
    peak = mel_db.max() or 1.0
    mel_norm = (mel_db / peak).astype(np.float32)  # (n_mels, n_frames)

    frames: list[list[float]] = []
    for i in range(mel_norm.shape[1]):
        frames.append([round(float(v), 4) for v in mel_norm[:, i]])

    return frames
