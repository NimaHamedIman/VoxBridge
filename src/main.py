from ai_engine import get_response
from text_to_speech import speak
from speech_to_text import listen

def main():
    print("VoxBridge - Voice-First AI Assistant")
    print("Drück Enter zum Sprechen, `exit` zum Beenden.\n")

    while True:
        command = input("[Enter] zum Sprechen: ")
        if command.lower() == "exit":
            print("Bye Baby!")
            break
        user_input = listen()
        print(f"Du sagtest: {user_input}")

        response = get_response(user_input)
        print(f"VoxBridge antwortet: {response}\n")
        speak(response)

if __name__ == "__main__":
    main()
