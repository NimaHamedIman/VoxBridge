
import pyttsx3


def speak(text: str) -> None:
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)

   
    for voice in engine.getProperty("voices"):
        name = voice.name.lower()
        if "german" in name or "deutsch" in name or "de-de" in voice.id.lower():
            engine.setProperty("voice", voice.id)
            break

    engine.say(text)
    engine.runAndWait()
    engine.stop()