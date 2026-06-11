"""
VoxBridge _ Voice-Frist AI Assistant
main entry point _ connects all modules together.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai_engine import get_response
from text_to_speech import speak
from speech_to_text import transcribe_audio, load_model
from dotenv import load_dotenv
load_dotenv()


def greet():
    print("=" * 50)
    print(" VoxBridge - Voice-First AI Assistant")
    print(" v0.2 _ Full voice loop")
    print("=" * 50)
    print("Loding Whisper model, please wait...\n")
    load_model()
    print("Ready! Speak after the prompt.\n")
    print("Press Ctrl+C to quit.\n")


def main():
    greet()
    history = []

    try:
        while True:
            input("\nPress Enter , then speak...")

            user_text = transcribe_audio()

            if not user_text.strip():
                print("Nothing heard, try again.")
                continue
            print(f"You: {user_text}")

            response = get_response(user_text, history)
            print(f"VoxBridge: {response}\n")

            speak(response)

            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": response})
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
