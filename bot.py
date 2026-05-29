import os
import json
import random
import asyncio
from telegram import Bot
from telegram.constants import PollType
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = os.environ["8710648004:AAHwK3ppnY6_H-iYrXtRwf9lP7hrHzCnex4"]
bot = Bot(token=TOKEN)

CHANNELS = ["@harry_potterquiz"]

BANK_FILE = "quiz_bank.json"
USED_FILE = "used_questions.json"


def load_bank():
    with open(BANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_used():
    try:
        with open(USED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_used(data):
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_next_question():
    bank = load_bank()
    used = load_used()

    available = [q for q in bank if q["id"] not in used]

    if not available:
        used = []
        save_used(used)
        available = bank

    q = random.choice(available)
    used.append(q["id"])
    save_used(used)

    return q


async def send_quiz():
    q = get_next_question()

    for channel in CHANNELS:
        await bot.send_poll(
            chat_id=channel,
            question=q["question"],
            options=q["options"],
            type=PollType.QUIZ,
            correct_option_id=q["correct"],
            explanation=q["explanation"],
            is_anonymous=True
        )

        print(f"Inviato su {channel}: {q['id']}")


async def main():
    print("Bot avviato...")

    await send_quiz()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_quiz, "cron", hour=10)
    scheduler.add_job(send_quiz, "cron", hour=18)
    scheduler.start()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())