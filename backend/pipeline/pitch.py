"""
Pitch tracking via CREPE.

melody_frames — from vocals stem, using crepe "full" model
bass_frames   — from bass stem, using crepe "medium" model (speed trade-off)

Each frame dict follows the HvizFrame.melody / HvizFrame.bass schema.

attack sharpness: derived from librosa onset_strength at the frame of each
detected note onset, normalised 0–1. High = hard attack (drives SH snap speed).
"""

from __future__ import annotations
import numpy as np
import librosa
import crepe


_UNVOICED_CONF_THRESHOLD = 0.4


def _hz_to_midi(hz: float | None) -> int | None:
    if hz is None or hz <= 0:
        return None
    return int(round(69 + 12 * np.log2(hz / 440.0)))


def _compute_onset_sharpness(audio: np.ndarray, sr: int, fps: int) -> np.ndarray:
    """Return per-frame onset strength (0–1 normalised)."""
    hop = sr // fps
    strength = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop)
    # Normalise to 0–1 robustly
    p99 = np.percentile(strength, 99) or 1.0
    return np.clip(strength / p99, 0.0, 1.0)


def _run_crepe(
    audio: np.ndarray,
    sr: int,
    fps: int,
    model_capacity: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run CREPE and return (times, frequencies_hz, confidences) at `fps`."""
    step_size_ms = int(1000 / fps)
    times, freqs, confs, _ = crepe.predict(
        audio,
        sr,
        model_capacity=model_capacity,
        step_size=step_size_ms,
        viterbi=True,
    )
    return times, freqs, confs


def track_pitch(
    stems: dict[str, tuple[np.ndarray, int]],
    fps: int = 30,
) -> tuple[list[dict], list[dict]]:
    vocals, sr_v = stems["vocals"]
    bass_audio, sr_b = stems["bass"]

    # Melody
    _, mel_hz, mel_conf = _run_crepe(vocals, sr_v, fps, "full")
    mel_vel = _compute_rms(vocals, sr_v, fps)
    mel_attack = _compute_onset_sharpness(vocals, sr_v, fps)

    # Bass
    _, bass_hz, bass_conf = _run_crepe(bass_audio, sr_b, fps, "medium")
    bass_vel = _compute_rms(bass_audio, sr_b, fps)
    bass_attack = _compute_onset_sharpness(bass_audio, sr_b, fps)

    n = min(len(mel_hz), len(bass_hz))

    melody_frames: list[dict] = []
    bass_frames: list[dict] = []

    for i in range(n):
        # Melody frame
        voiced = float(mel_conf[i]) >= _UNVOICED_CONF_THRESHOLD
        midi = _hz_to_midi(float(mel_hz[i])) if voiced else None
        melody_frames.append({
            "midi": midi,
            "pitch_hz": round(float(mel_hz[i]), 2) if voiced else None,
            "conf": round(float(mel_conf[i]), 3),
            "vel": round(float(mel_vel[i]) if i < len(mel_vel) else 0.0, 3),
            "attack": round(float(mel_attack[i]) if i < len(mel_attack) else 0.0, 3),
        })

        # Bass frame
        b_voiced = float(bass_conf[i]) >= _UNVOICED_CONF_THRESHOLD
        b_midi = _hz_to_midi(float(bass_hz[i])) if b_voiced else None
        bass_frames.append({
            "midi": b_midi,
            "pitch_hz": round(float(bass_hz[i]), 2) if b_voiced else None,
            "octave": (b_midi // 12) if b_midi is not None else None,
            "pitch_class": (b_midi % 12) if b_midi is not None else None,
            "conf": round(float(bass_conf[i]), 3),
            "vel": round(float(bass_vel[i]) if i < len(bass_vel) else 0.0, 3),
            "attack_sharpness": round(float(bass_attack[i]) if i < len(bass_attack) else 0.0, 3),
        })

    return melody_frames, bass_frames


def _compute_rms(audio: np.ndarray, sr: int, fps: int) -> np.ndarray:
    hop = sr // fps
    rms = librosa.feature.rms(y=audio, hop_length=hop)[0]
    p99 = np.percentile(rms, 99) or 1.0
    return np.clip(rms / p99, 0.0, 1.0)
