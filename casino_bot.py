import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏀 Привет! Напиши баскетбол или basketball чтобы бросить мяч!"
    )

async def ball(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_dice(emoji="🏀")

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text in ["баскетбол", "basketball", "бас", "ball", "мяч"]:
        await update.message.reply_dice(emoji="🏀")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ball", ball))
app.add_handler(MessageHandler(filters.TEXT, text_handler))

print("🏀 Бот запущен!")
app.run_polling()
