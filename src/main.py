"""
main.py — نقطهٔ شروع VoxBridge (فعلاً حالت متنی)
در قدم‌های بعد، ورودی و خروجیِ صدا اضافه می‌شود.
"""

from ai_engine import get_response   # مغز AI را وارد کن


def main():
    print("VoxBridge — Voice-First AI Assistant")
    print("برای خروج بنویس: exit\n")

    while True:                          # حلقهٔ اصلی، تا وقتی exit نزدی
        user_input = input("تو: ")       # ۱) ورودی بگیر

        if user_input.lower() == "exit": # ۲) شرط خروج
            print("خداحافظ! 👋")
            break

        response = get_response(user_input)   # ۳) به مغز بده، جواب بگیر
        print(f"VoxBridge: {response}\n")     # ۴) جواب را چاپ کن


if __name__ == "__main__":
    main()