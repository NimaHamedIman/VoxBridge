"""
Speech-to-Text module using openAI Whisper.
Records audio from microphone and transcribes it to text.
"""
import whisper
import sounddevice as sd
import numpy as np
import os

_whisper_model = None
def load_model():
    global _whisper_model
    if _whisper_model is None:
        model_name = os.getenv("WHISPER_MODEL", "base")
        print(f"Loading Whisper model: {model_name}...")
        _whisper_model = whisper.load_model(model_name)
        print("Model ready.")
    return _whisper_model

def record_audio(duration_seconds: float = 5.0, sample_rate: int = 16000):
    print(f"Recording for {duration_seconds} seconds...")
    audio = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    print("Recording complete.")
    return audio.flatten()

def transcribe_audio(audio_data=None, language: str = None) -> str:
    if audio_data is None:
        audio_data = record_audio()

    model = load_model()

    if language is None:
        language = os.getenv("LANGUAGE", "de")

    try:
        result = model.transcribe(
            audio_data,
            language=language,
            fp16=False
        )
        return result.get("text", "").strip()
    except Exception as e:
        print(f"Error during transcription: {e}")
        return ""
        