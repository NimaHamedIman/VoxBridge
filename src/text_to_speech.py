"""
Text-to-Speech module.
Uses pyttsx3 for offline TTS _ no internet needed.
"""

import pyttsx3
import os



def speak(text: str, rate: int = 170, volume: float = 1.0) -> None:
    if not text or not text.strip():
        return
    try:
        engine = pyttsx3.init()

        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        voices = engine.getProperty("voices")
        language = os.getenv("LANGUAGE", "de")
        if language == "de":
              for voice in voices:
                if "german" in voice.name.lower() or "de" in voice.id.lower():
                    engine.setProperty("voice", voice.id)
                    break

        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in TTS: {str(e)}")
        