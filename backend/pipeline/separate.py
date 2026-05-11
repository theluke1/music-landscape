"""
Stem separation via Demucs (htdemucs_ft — fine-tuned, best quality).

Returns:
    dict mapping stem name → (np.ndarray mono float32, sample_rate int)
    Stems: "vocals", "bass", "drums", "other"
"""

from pathlib import Path
import numpy as np

# Demucs ships its own CLI; we call it programmatically via the `demucs` Python API.
# On first run, model weights (~300 MB) are downloaded automatically.


def separate_stems(
    audio_path: Path,
    device: str = "cpu",
    model: str = "htdemucs_ft",
) -> dict[str, tuple[np.ndarray, int]]:
    import torch
    import torchaudio
    from demucs.pretrained import get_model
    from demucs.apply import apply_model

    model_obj = get_model(model)
    model_obj.to(device)
    model_obj.eval()

    wav, sr = torchaudio.load(str(audio_path))
    # Demucs expects stereo; duplicate mono if needed
    if wav.shape[0] == 1:
        wav = wav.repeat(2, 1)
    wav = wav.unsqueeze(0).to(device)  # (1, 2, samples)

    with torch.no_grad():
        sources = apply_model(model_obj, wav, device=device, progress=True)
    # sources shape: (1, n_stems, 2, samples) in model.sources order

    stem_names = model_obj.sources  # ['drums', 'bass', 'other', 'vocals']
    result: dict[str, tuple[np.ndarray, int]] = {}
    for i, name in enumerate(stem_names):
        stereo = sources[0, i].cpu().numpy()   # (2, samples)
        mono = stereo.mean(axis=0).astype(np.float32)
        result[name] = (mono, sr)

    return result
