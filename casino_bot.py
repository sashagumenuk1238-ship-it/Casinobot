import os, json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
DATA_FILE = "users.json"

def get_user(uid):
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
    except:
        data = {}
    if uid not in data:
        data[uid] = {"usd": 500.0}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    return data

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏀 Привет!\n\nНапиши баскетбол или ball чтобы бросить мяч!\n\n🏀 1-3 → Промах → $0\n🏀 4-5 → Попал → $300\n🏀 6 → Идеальный бросок → $500\n\n💵 Стартовый баланс: $500"
    )

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text not in ["баскетбол", "basketball", "бас", "ball", "мяч"]:
        return
    uid = str(update.effective_user.id)
    data = get_user(uid)
    msg = await update.message.reply_dice(emoji="🏀")
    score = msg.dice.value
    if score <= 3:
        earned = 0
        result = "💨 Промах! Мяч не попал в кольцо!"
    elif score <= 5:
        earned = 300
        result = "🎯 Попал! Отличный бросок!"
    else:
        earned = 500
        result = "🔥 ИДЕАЛЬНЫЙ БРОСОК!"
    data[uid]["usd"] += earned
    save(data)
    await update.message.reply_text(f"{result}\n\n💵 Заработал: +${earned}\n💰 Баланс: ${data[uid]['usd']:,.2f}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
print("🏀 Бот запущен!")
app.run_polling()
