"""
Speaker recognition module (EXPERIMENTAL — not part of the main pipeline yet).

Records a voice sample, computes a speaker embedding via SpeechBrain
(ECAPA-TDNN, trained on VoxCeleb) and stores it under a name in voices.json.
Later this will be used to identify who is speaking.

Extra dependencies (NOT in requirements.txt on purpose, since this module
is experimental): pip install speechbrain torch
"""

import json
import os

import numpy as np
import sounddevice as sd
import torch
from speechbrain.inference.speaker import EncoderClassifier

SAMPLE_RATE = 16000
VOICES_FILE = "voices.json"

# Lazy-loaded model (first call downloads ~80 MB from HuggingFace).
_encoder = None


def _get_encoder() -> EncoderClassifier:
    global _encoder
    if _encoder is None:
        _encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="models/spkrec",
        )
    return _encoder


def record_audio(duration: int = 5) -> np.ndarray:
    """Record a few seconds from the microphone and return the audio (16 kHz mono)."""
    print("🎤 Speak now...")
    rec = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    return rec.flatten()


def get_embedding(audio: np.ndarray) -> np.ndarray:
    """Compute a speaker embedding vector from a raw audio sample."""
    signal = torch.tensor(audio).unsqueeze(0)  # add batch dimension
    embedding = _get_encoder().encode_batch(signal)
    return embedding.squeeze().detach().numpy()


def _load_voices() -> dict:
    if os.path.exists(VOICES_FILE):
        with open(VOICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def enroll(name: str) -> None:
    """Record a person's voice, compute the embedding and store it under their name."""
    audio = record_audio()
    embedding = get_embedding(audio)

    voices = _load_voices()
    # numpy arrays are not JSON-serializable — convert to a plain list.
    voices[name] = embedding.tolist()

    with open(VOICES_FILE, "w", encoding="utf-8") as f:
        json.dump(voices, f)

    print(f"✅ Voice profile for '{name}' saved.")


def identify(audio: np.ndarray, threshold: float = 0.6) -> str | None:
    """
    Compare an audio sample against all enrolled voices.
    Returns the best-matching name if cosine similarity exceeds the
    threshold, otherwise None.
    """
    voices = _load_voices()
    if not voices:
        return None

    emb = get_embedding(audio)
    best_name, best_score = None, -1.0

    for name, stored in voices.items():
        stored_emb = np.array(stored)
        score = float(
            np.dot(emb, stored_emb)
            / (np.linalg.norm(emb) * np.linalg.norm(stored_emb))
        )
        if score > best_score:
            best_name, best_score = name, score

    return best_name if best_score >= threshold else None


if __name__ == "__main__":
    name = input("Enter a name for enrollment and press Enter: ").strip()
    if name:
        enroll(name)