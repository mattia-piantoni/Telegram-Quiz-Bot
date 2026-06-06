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

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")

QUIZ_FILE = os.getenv("QUIZ_FILE", "quiz_bank.json")
USED_FILE = os.getenv("USED_FILE", "used_questions.json")
QUIZ_INTERVAL_MINUTES = int(os.getenv("QUIZ_INTERVAL_MINUTES", "120"))
SEND_QUIZ_ON_STARTUP = os.getenv("SEND_QUIZ_ON_STARTUP", "false").lower() == "true"
ENABLE_POLLING = os.getenv("ENABLE_POLLING", "false").lower() == "true"

CHANNELS = {
    "harry_potter": os.getenv("CHANNEL_HARRY_POTTER", "@harry_potterquiz")
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

def validate_question(question):
    required_fields = ["id", "question", "options", "correct_index"]
    missing = [field for field in required_fields if field not in question]
    if missing:
        raise ValueError(f"Question {question!r} is missing fields: {missing}")

    options = question["options"]
    correct_index = question["correct_index"]

    if not isinstance(options, list) or not 2 <= len(options) <= 10:
        raise ValueError(f"Question {question['id']} must have between 2 and 10 options")

    if not isinstance(correct_index, int) or not 0 <= correct_index < len(options):
        raise ValueError(f"Question {question['id']} has invalid correct_index")

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
        validate_question(question)

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

        print(f"[OK] Sent {theme} quiz {question['id']} at {datetime.now()}", flush=True)

    except Exception as e:
        print(f"[ERROR] send_quiz failed: {type(e).__name__}: {e}", flush=True)

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
        raise ValueError(
            "Missing Telegram bot token. Set BOT_TOKEN in Render environment variables "
            "using the token from BotFather."
        )

    app = Application.builder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()

    # 🧪 TEST MODE: ogni 2 minuti
    scheduler.add_job(
        send_quiz,
        "interval",
        minutes=QUIZ_INTERVAL_MINUTES,
        args=[app, "harry_potter"]
    )

    scheduler.start()

    if ENABLE_POLLING:
        app.add_handler(CommandHandler("test", test))

    await app.initialize()
    await app.start()

    if ENABLE_POLLING:
        await app.updater.start_polling()
        print("Telegram polling enabled for /test command.", flush=True)
    else:
        print("Telegram polling disabled. Running as scheduled publisher only.", flush=True)

    print(
        f"Bot Harry Potter LIVE. Posting every {QUIZ_INTERVAL_MINUTES} minutes "
        f"to {CHANNELS['harry_potter']}.",
        flush=True,
    )

    if SEND_QUIZ_ON_STARTUP:
        print("[STARTUP] Sending one quiz immediately...", flush=True)
        await send_quiz(app, "harry_potter")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
