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
        data[uid] = {"usd": 500.0, "btc": 0.0, "ton": 0.0}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    return data

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Привет!\n\n"
        "⚽ Напиши бас — бросить мяч\n"
        "💰 Напиши баланс — посмотреть счёт\n\n"
        "🏀 1-3 → Промах → $0\n"
        "🏀 4-5 → Попал → $300\n"
        "🏀 6 → Идеальный → $500\n\n"
        "💵 Стартовый баланс: $500"
    )

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    uid = str(update.effective_user.id)
    data = get_user(uid)

    # Баланс
    if text in ["баланс", "balance", "балланс", "бал"]:
        u = data[uid]
        await update.message.reply_text(
            "╔══════════════════╗\n"
            "       💼 МОЙ БАЛАНС\n"
            "╚══════════════════╝\n\n"
            f"💵 Доллары:  ${u['usd']:,.2f}\n"
            f"₿  Биткоин:  {u['btc']:.4f} BTC\n"
            f"💎 Тон:      {u['ton']:.2f} TON\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        return

    # Баскетбол
    if text in ["баскетбол", "basketball", "бас", "ball", "мяч"]:
        msg = await update.message.reply_dice(emoji="🏀")
        score = msg.dice.value
        if score <= 3:
            earned = 0
            result = "💨 Промах! Мяч не попал в кольцо!"
        elif score <= 5:
            earned = 300
            result = "🎯 Попал! +$300"
        else:
            earned = 500
            result = "🔥 ИДЕАЛЬНЫЙ БРОСОК! +$500"
        data[uid]["usd"] += earned
        save(data)
        await update.message.reply_text(result)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
print("🏀 Бот запущен!")
app.run_polling()
