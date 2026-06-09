from ai_engine import get_response
from text_to_speech import speak
from speech_to_text import listen
from memory import load_history, save_history


def main():
    print("VoxBridge - Voice-First AI Assistant")
    print("Drück Enter zum Sprechen, `exit` zum Beenden.\n")

    history = load_history()

    while True:
        command = input("[Enter] zum Sprechen: ")
        if command.lower() == "exit":
            print("Goodbye!")
            break

        user_input = listen()
        print(f"Du sagtest: {user_input}")

        history.append({"role": "user", "content": user_input})
        response = get_response(history)
        history.append({"role": "assistant", "content": response})
        save_history(history)

        print(f"VoxBridge antwortet: {response}\n")
        speak(response)


if __name__ == "__main__":
    main()
