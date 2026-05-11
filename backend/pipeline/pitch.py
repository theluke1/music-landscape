"""
Pitch tracking via CREPE.

melody_frames — from vocals stem, using crepe "full" model
bass_frames   — from bass stem, using crepe "medium" model (speed trade-off)

Each frame dict follows the HvizFrame.melody / HvizFrame.bass schema.

attack: per-frame onset strength from librosa, normalised 0–1.
        High value = hard transient attack (drives helix/SH snap speed).

Frame count alignment (bug fixed vs scaffold):
    CREPE at step_size_ms=33 produces slightly more frames than librosa at
    hop=sr//30 (e.g. 7272 vs 7200 for a 4-min song).  All arrays are trimmed
    to the minimum length across CREPE and librosa outputs before zipping.
"""

from __future__ import annotations
import numpy as np
import librosa
import crepe


_UNVOICED_CONF_THRESHOLD = 0.4


def _hz_to_midi(hz: float) -> int | None:
    if hz <= 0:
        return None
    return int(round(69 + 12 * np.log2(hz / 440.0)))


def _compute_rms(audio: np.ndarray, sr: int, fps: int) -> np.ndarray:
    hop = sr // fps
    rms = librosa.feature.rms(y=audio, hop_length=hop)[0]
    p99 = float(np.percentile(rms, 99)) or 1.0
    return np.clip(rms / p99, 0.0, 1.0).astype(np.float32)


def _compute_onset_sharpness(audio: np.ndarray, sr: int, fps: int) -> np.ndarray:
    """Per-frame onset strength, normalised 0–1."""
    hop = sr // fps
    strength = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop)
    p99 = float(np.percentile(strength, 99)) or 1.0
    return np.clip(strength / p99, 0.0, 1.0).astype(np.float32)


def _run_crepe(
    audio: np.ndarray,
    sr: int,
    fps: int,
    model_capacity: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (frequencies_hz, confidences) at approximately `fps` per second."""
    step_size_ms = int(1000 / fps)   # 33 ms for fps=30
    _, freqs, confs, _ = crepe.predict(
        audio,
        sr,
        model_capacity=model_capacity,
        step_size=step_size_ms,
        viterbi=True,
    )
    return freqs, confs


def _trim(*arrays: np.ndarray) -> tuple[np.ndarray, ...]:
    """Trim all arrays to the length of the shortest one."""
    n = min(len(a) for a in arrays)
    return tuple(a[:n] for a in arrays)


def track_pitch(
    stems: dict[str, tuple[np.ndarray, int]],
    fps: int = 30,
) -> tuple[list[dict], list[dict]]:
    vocals, sr_v = stems["vocals"]
    bass_audio, sr_b = stems["bass"]

    # Melody (CREPE full for accuracy)
    mel_hz, mel_conf = _run_crepe(vocals, sr_v, fps, "full")
    mel_vel = _compute_rms(vocals, sr_v, fps)
    mel_attack = _compute_onset_sharpness(vocals, sr_v, fps)

    # Bass (CREPE medium — speed/accuracy tradeoff)
    bass_hz, bass_conf = _run_crepe(bass_audio, sr_b, fps, "medium")
    bass_vel = _compute_rms(bass_audio, sr_b, fps)
    bass_attack = _compute_onset_sharpness(bass_audio, sr_b, fps)

    # Align all arrays to the same length before zipping
    mel_hz, mel_conf, mel_vel, mel_attack = _trim(mel_hz, mel_conf, mel_vel, mel_attack)
    bass_hz, bass_conf, bass_vel, bass_attack = _trim(bass_hz, bass_conf, bass_vel, bass_attack)
    n = min(len(mel_hz), len(bass_hz))

    melody_frames: list[dict] = []
    bass_frames: list[dict] = []

    for i in range(n):
        # Melody
        voiced = float(mel_conf[i]) >= _UNVOICED_CONF_THRESHOLD
        hz_m = float(mel_hz[i])
        midi_m = _hz_to_midi(hz_m) if voiced else None
        melody_frames.append({
            "midi":     midi_m,
            "pitch_hz": round(hz_m, 2) if voiced else None,
            "conf":     round(float(mel_conf[i]), 3),
            "vel":      round(float(mel_vel[i]), 3),
            "attack":   round(float(mel_attack[i]), 3),
        })

        # Bass
        b_voiced = float(bass_conf[i]) >= _UNVOICED_CONF_THRESHOLD
        hz_b = float(bass_hz[i])
        midi_b = _hz_to_midi(hz_b) if b_voiced else None
        bass_frames.append({
            "midi":             midi_b,
            "pitch_hz":         round(hz_b, 2) if b_voiced else None,
            "octave":           (midi_b // 12) if midi_b is not None else None,
            "pitch_class":      (midi_b % 12)  if midi_b is not None else None,
            "conf":             round(float(bass_conf[i]), 3),
            "vel":              round(float(bass_vel[i]), 3),
            "attack_sharpness": round(float(bass_attack[i]), 3),
        })

    return melody_frames, bass_frames
