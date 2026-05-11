"""
Stem separation via Demucs (htdemucs_ft — fine-tuned, best quality).

Returns:
    dict mapping stem name → (np.ndarray mono float32, sample_rate int)
    Stems: "vocals", "bass", "drums", "other"
    All stems are returned at model.samplerate (44100 Hz).

Bug fixed vs scaffold: torchaudio loads at the file's native SR; Demucs's
apply_model expects audio at model.samplerate (44100).  Without resampling,
files recorded at 48000 Hz (very common) produce pitch-shifted stems.
"""

from pathlib import Path
import numpy as np


def separate_stems(
    audio_path: Path,
    device: str = "cpu",
    model: str = "htdemucs_ft",
) -> dict[str, tuple[np.ndarray, int]]:
    import torch
    import torchaudio
    import torchaudio.transforms as T
    from demucs.pretrained import get_model
    from demucs.apply import apply_model

    model_obj = get_model(model)
    model_obj.to(device)
    model_obj.eval()

    model_sr: int = model_obj.samplerate   # 44100 for all htdemucs variants

    wav, file_sr = torchaudio.load(str(audio_path))  # (channels, samples), float32

    # Resample to model SR if the file is at a different rate (e.g. 48000 Hz)
    if file_sr != model_sr:
        resampler = T.Resample(orig_freq=file_sr, new_freq=model_sr)
        wav = resampler(wav)

    # Demucs expects stereo (2, samples); duplicate mono channels
    if wav.shape[0] == 1:
        wav = wav.repeat(2, 1)
    elif wav.shape[0] > 2:
        wav = wav[:2]   # take first two channels if > stereo

    wav = wav.unsqueeze(0).to(device)   # (1, 2, samples)

    with torch.no_grad():
        sources = apply_model(model_obj, wav, device=device, progress=True)
    # sources: (1, n_stems, 2, samples) in model.sources order

    result: dict[str, tuple[np.ndarray, int]] = {}
    for i, name in enumerate(model_obj.sources):   # ['drums', 'bass', 'other', 'vocals']
        stereo = sources[0, i].cpu().numpy()        # (2, samples)
        mono = stereo.mean(axis=0).astype(np.float32)
        result[name] = (mono, model_sr)

    return result
