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

CHANNELS = {
    "auto": "@your_channel_1",
    "tech": "@your_channel_2"
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
# QUIZ LOGIC
# =========================

def get_next_question(theme, used, quiz_data):
    questions = quiz_data.get(theme, [])

    used_ids = used.get(theme, [])

    for q in questions:
        if q["id"] not in used_ids:
            return q

    return None  # reset or exhausted


async def send_quiz(app, theme="auto"):
    quiz_data = load_quiz()
    used = load_used()

    channel = CHANNELS.get(theme)
    if not channel:
        print(f"No channel for theme {theme}")
        return

    question = get_next_question(theme, used, quiz_data)

    if not question:
        print(f"No questions left for {theme}")
        return

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

    print(f"Sent quiz to {theme} - {datetime.now()}")

# =========================
# COMMANDS (TEST)
# =========================

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sending test quiz...")
    await send_quiz(context.application, "auto")

# =========================
# MAIN
# =========================

async def main():
    app = Application.builder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()

    # 🔥 production schedule
    scheduler.add_job(send_quiz, "cron", hour=9, minute=0, args=[app, "auto"])
    scheduler.add_job(send_quiz, "cron", hour=18, minute=0, args=[app, "auto"])

    # 🧪 TEST MODE (disattiva in produzione se vuoi)
    scheduler.add_job(send_quiz, "interval", minutes=60, args=[app, "auto"])

    scheduler.start()

    app.add_handler(CommandHandler("test", test))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("Bot started...")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
