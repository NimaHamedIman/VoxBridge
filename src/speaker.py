import json
import os
import numpy as np
import torch
import sounddevice as sd
from speechbrain.inference.speaker import EncoderClassifier

SAMPLE_RATE = 16000

# مدل را یک‌بار بارگذاری کن (بار اول از HuggingFace دانلود می‌شود، ~۸۰ مگ)
encoder = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="models/spkrec",
)


def get_embedding(audio: np.ndarray) -> np.ndarray:
    """از یک نمونه‌صدا (numpy، 16kHz) یک بردار embedding می‌سازد."""
    signal = torch.tensor(audio).unsqueeze(0)      # numpy → torch، با یک بُعد batch
    embedding = encoder.encode_batch(signal)        # محاسبهٔ embedding
    return embedding.squeeze().detach().numpy()     # تبدیل به یک بردار سادهٔ numpy
VOICES_FILE = "voices.json"


def record_audio(duration: int = 5) -> np.ndarray:
    """چند ثانیه از میکروفون ضبط می‌کند و صدا را برمی‌گرداند."""
    print("🎤 Sprich jetzt...")
    rec = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                 channels=1, dtype="float32")
    sd.wait()
    return rec.flatten()


def enroll(name: str) -> None:
    """صدای یک نفر را ضبط، embedding را حساب و با اسمش ذخیره می‌کند."""
    audio = record_audio()
    embedding = get_embedding(audio)

    # صداهای ذخیره‌شده را بخوان (مثل memory.py)
    voices = {}
    if os.path.exists(VOICES_FILE):
        with open(VOICES_FILE, "r", encoding="utf-8") as f:
            voices = json.load(f)

    # embedding یک آرایهٔ numpy است؛ برای JSON باید به لیست تبدیلش کنیم
    voices[name] = embedding.tolist()

    with open(VOICES_FILE, "w", encoding="utf-8") as f:
        json.dump(voices, f)

    print(f"✅ صدای '{name}' ذخیره شد.")
    




def record_audio(duration: int = 5) -> np.ndarray:
    """چند ثانیه از میکروفون ضبط می‌کند و صدا را برمی‌گرداند."""
    print("🎤 Sprich jetzt...")
    rec = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                 channels=1, dtype="float32")
    sd.wait()
    return rec.flatten()


def enroll(name: str) -> None:
    """صدای یک نفر را ضبط، embedding را حساب و با اسمش ذخیره می‌کند."""
    audio = record_audio()
    embedding = get_embedding(audio)

    # صداهای ذخیره‌شده را بخوان (مثل memory.py)
    voices = {}
    if os.path.exists(VOICES_FILE):
        with open(VOICES_FILE, "r", encoding="utf-8") as f:
            voices = json.load(f)

    # embedding یک آرایهٔ numpy است؛ برای JSON باید به لیست تبدیلش کنیم
    voices[name] = embedding.tolist()

    with open(VOICES_FILE, "w", encoding="utf-8") as f:
        json.dump(voices, f)

    if __name__ == "__main__":
        name = input("اسمت را بنویس و Enter بزن: ")
        enroll(name) 





# --- تستِ موقت: این فایل را مستقیم اجرا کن تا embedding را ببینی ---
if __name__ == "__main__":
    print("🎤 ۳ ثانیه حرف بزن...")
    rec = sd.rec(int(3 * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                 channels=1, dtype="float32")
    sd.wait()
    emb = get_embedding(rec.flatten())
    print("طول بردار (اثر انگشت صوتی):", len(emb))
    print("چند عدد اول:", emb[:5])