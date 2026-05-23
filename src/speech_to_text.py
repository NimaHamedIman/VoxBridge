import os
import whisper
import sounddevice as sd
from dotenv import load_dotenv

load_dotenv()

sample_rate = 16000
whisper_model = os.getenv("WHISPER_MODEL", "base")
model = whisper.load_model(whisper_model)

def listen(duration: int = 5) -> str:
    print(" Spreche jetzt...Sag Doch was...")
    recording = sd.rec(
        int(duration*sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    audio = recording.flatten()

    result = model.transcribe(audio, fp16=False)
    return result["text"].strip()

