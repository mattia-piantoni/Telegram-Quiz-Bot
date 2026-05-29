import os
import json
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

QUIZ_FILE = "quiz_bank.json"
USED_FILE = "used_questions.json"

# SOLO HARRY POTTER (come richiesto)
CHANNELS = {
    "harry_potter": "@harry_potterquiz"
}

# =========================
# LOAD DATA
# =========================

def load_quiz():
    with open(QUIZ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_used():
    if not os.path.exists(USED_FILE):
        return {}
    with open(USED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_used(data):
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# =========================
# LOGIC
# =========================

def get_next_question(theme, used, quiz_data):
    questions = quiz_data.get(theme, [])
    used_ids = used.get(theme, [])

    for q in questions:
        if q["id"] not in used_ids:
            return q

    # reset se finite (loop infinito contenuti)
    used[theme] = []
    return questions[0] if questions else None


async def send_quiz(app, theme="harry_potter"):
    quiz_data = load_quiz()
    used = load_used()

    channel = CHANNELS.get(theme)
    if not channel:
        print(f"[ERROR] Channel missing for {theme}")
        return

    question = get_next_question(theme, used, quiz_data)

    if not question:
        print(f"[ERROR] No questions for {theme}")
        return

    try:
        await app.bot.send_poll(
            chat_id=channel,
            question=question["question"],
            options=question["options"],
            type="quiz",
            correct_option_id=question["correct_index"],
            is_anonymous=False
        )

        used.setdefault(theme, []).append(question["id"])
        save_used(used)

        print(f"[OK] Sent HP quiz at {datetime.now()}")

    except Exception as e:
        print(f"[ERROR] send_quiz failed: {e}")

# =========================
# MANUAL TEST COMMAND
# =========================

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Invio quiz Harry Potter...")
    await send_quiz(context.application, "harry_potter")

# =========================
# MAIN
# =========================

async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN mancante su environment variables")

    app = Application.builder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()

    # 🧪 TEST MODE: ogni 2 minuti
    scheduler.add_job(
        send_quiz,
        "interval",
        minutes=2,
        args=[app, "harry_potter"]
    )

    scheduler.start()

    app.add_handler(CommandHandler("test", test))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("Bot Harry Potter LIVE...")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
