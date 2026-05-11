"""
Phase 7 — Perceptual ML model.

Input:  rolling 2s window of [spectral centroid, RMS, chroma vector (12),
         onset rate, harmonic ratio, tempo] → 30-dim feature vector
Output: [energy, valence, tension, density] — all 0–1

Until Phase 7 training is complete, predict() returns zeros for all frames.
The model slot is wired up in process_audio.py so it's a drop-in when ready.
"""

from __future__ import annotations
import numpy as np


class PerceptualModel:
    """
    Stub — returns zero vectors until the Phase 7 MLP is trained.
    Replace _predict_batch() with the trained model inference when ready.
    """

    def __init__(self, weights_path: str | None = None) -> None:
        self._trained = False
        if weights_path:
            self._load(weights_path)

    def _load(self, path: str) -> None:
        # TODO Phase 7: load PyTorch MLP weights
        # import torch
        # self._model = MLP(input_dim=30, hidden=[64, 64], output_dim=4)
        # self._model.load_state_dict(torch.load(path, map_location="cpu"))
        # self._model.eval()
        # self._trained = True
        pass

    def predict(
        self,
        chroma_frames: list[list[float]],
        melody_frames: list[dict],
        drum_frames: list[dict],
    ) -> list[dict]:
        n = len(chroma_frames)
        zero = {"energy": 0.0, "valence": 0.0, "tension": 0.0, "density": 0.0}
        if not self._trained:
            return [zero] * n

        # TODO Phase 7: build feature vectors from rolling 2s window and run inference
        raise NotImplementedError("Phase 7 MLP not yet trained.")
