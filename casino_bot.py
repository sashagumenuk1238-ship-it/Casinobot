import os, json, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
DATA_FILE = "users.json"

BIT_FARMS = {
    "bit1": {"name": "🏚 Малая BIT ферма",   "price": 20000,  "per_hour": 15},
    "bit2": {"name": "🏭 Средняя BIT ферма", "price": 60000,  "per_hour": 50},
    "bit3": {"name": "🏰 Большая BIT ферма", "price": 150000, "per_hour": 120},
}
TON_FARMS = {
    "ton1": {"name": "🏚 Малая TON ферма",   "price": 15000,  "per_hour": 10},
    "ton2": {"name": "🏭 Средняя TON ферма", "price": 45000,  "per_hour": 35},
    "ton3": {"name": "🏰 Большая TON ферма", "price": 120000, "per_hour": 90},
}

def get_user(uid):
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
    except:
        data = {}
    if uid not in data:
        data[uid] = {
            "usd": 500.0,
            "btc": 0.0,
            "ton": 0.0,
            "bit_farm": None,
            "ton_farm": None,
            "last_farm": time.time()
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    return data

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def collect(data, uid):
    u = data[uid]
    now = time.time()
    hours = (now - u["last_farm"]) / 3600
    if u["bit_farm"]:
        u["btc"] += BIT_FARMS[u["bit_farm"]]["per_hour"] * hours
    if u["ton_farm"]:
        u["ton"] += TON_FARMS[u["ton_farm"]]["per_hour"] * hours
    u["last_farm"] = now
    return data

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Добро пожаловать!\n\n"
        "🏀 бас — бросить мяч\n"
        "💰 баланс — мой счёт\n"
        "🏪 магазин ферм — купить ферму\n"
        "⛏ моя ферма бит — инфо BTC фермы\n"
        "💎 моя ферма тон — инфо TON фермы\n"
        "🎰 ставка 200 меньше — рулетка\n"
        "🎰 ставка 200 больше — рулетка\n\n"
        "💵 Стартовый баланс: $500"
    )

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    uid = str(update.effective_user.id)
    data = get_user(uid)
    data = collect(data, uid)
    u = data[uid]

    # ── БАЛАНС ──
    if text in ["баланс", "balance", "бал"]:
        await update.message.reply_text(
            f"💼 Баланс\n\n"
            f"💵 ${u['usd']:,.0f}\n"
            f"₿ {u['btc']:.4f} BTC\n"
            f"💎 {u['ton']:.2f} TON"
        )
        save(data)
        return

    # ── МЯЧ ──
    if text in ["бас", "ball", "баскетбол", "мяч"]:
        msg = await update.message.reply_dice(emoji="🏀")
        score = msg.dice.value
        if score <= 3:
            earned = 0
            result = "💨 Промах!"
        elif score <= 5:
            earned = 300
            result = "🎯 Попал! +$300"
        else:
            earned = 500
            result = "🔥 Идеальный! +$500"
        u["usd"] += earned
        save(data)
        await update.message.reply_text(result)
        return

    # ── МАГАЗИН ФЕРМ ──
    if text in ["магазин ферм", "магазин", "фермы"]:
        msg = "🏪 МАГАЗИН ФЕРМ\n\n"
        msg += "⛏ BIT ФЕРМЫ:\n"
        for fid, f in BIT_FARMS.items():
            owned = "✅" if u["bit_farm"] == fid else ""
            msg += f"{owned}{f['name']}\n💰 ${f['price']:,} | +{f['per_hour']} BIT/час\n\n"
        msg += "💎 TON ФЕРМЫ:\n"
        for fid, f in TON_FARMS.items():
            owned = "✅" if u["ton_farm"] == fid else ""
            msg += f"{owned}{f['name']}\n💰 ${f['price']:,} | +{f['per_hour']} TON/час\n\n"
        msg += "Чтобы купить напиши:\nкупить бит1 / бит2 / бит3\nкупить тон1 / тон2 / тон3"
        await update.message.reply_text(msg)
        return

    # ── КУПИТЬ ФЕРМУ ──if text.startswith("купить "):
        item = text.replace("купить ", "").strip()
        farm_map = {
            "бит1": ("bit_farm", "bit1", BIT_FARMS),
            "бит2": ("bit_farm", "bit2", BIT_FARMS),
            "бит3": ("bit_farm", "bit3", BIT_FARMS),
            "тон1": ("ton_farm", "ton1", TON_FARMS),
            "тон2": ("ton_farm", "ton2", TON_FARMS),
            "тон3": ("ton_farm", "ton3", TON_FARMS),
        }
        if item in farm_map:
            key, fid, farms = farm_map[item]
            farm = farms[fid]
            if u["usd"] < farm["price"]:
                await update.message.reply_text(f"❌ Недостаточно денег!\nНужно ${farm['price']:,}\nУ тебя ${u['usd']:,.0f}")
            else:
                u["usd"] -= farm["price"]
                u[key] = fid
                save(data)
                await update.message.reply_text(f"✅ Куплена {farm['name']}!\n+{farm['per_hour']} в час\n\n💵 Остаток: ${u['usd']:,.0f}")
        else:
            await update.message.reply_text("❌ Неверное название!\nПиши: купить бит1, бит2, бит3\nили: купить тон1, тон2, тон3")
        return

    # ── МОЯ ФЕРМА БИТ ──
    if text in ["моя ферма бит", "ферма бит", "бит ферма"]:
        if not u["bit_farm"]:
            await update.message.reply_text("⛏ У тебя нет BIT фермы!\nНапиши магазин ферм чтобы купить")
        else:
            f = BIT_FARMS[u["bit_farm"]]
            await update.message.reply_text(
                f"⛏ МОЯ BIT ФЕРМА\n\n"
                f"{f['name']}\n"
                f"💰 Стоимость: ${f['price']:,}\n"
                f"⚡ Доход: +{f['per_hour']} BIT/час\n"
                f"₿ Накоплено: {u['btc']:.4f} BTC"
            )
        return

    # ── МОЯ ФЕРМА ТОН ──
    if text in ["моя ферма тон", "ферма тон", "тон ферма"]:
        if not u["ton_farm"]:
            await update.message.reply_text("💎 У тебя нет TON фермы!\nНапиши магазин ферм чтобы купить")
        else:
            f = TON_FARMS[u["ton_farm"]]
            await update.message.reply_text(
                f"💎 МОЯ TON ФЕРМА\n\n"
                f"{f['name']}\n"
                f"💰 Стоимость: ${f['price']:,}\n"
                f"⚡ Доход: +{f['per_hour']} TON/час\n"
                f"💎 Накоплено: {u['ton']:.2f} TON"
            )
        return

    # ── РУЛЕТКА ──
    if text.startswith("ставка "):
        parts = text.split()
        if len(parts) == 3 and parts[2] in ["меньше", "больше"]:
            try:
                bet = float(parts[1])
            except:
                await update.message.reply_text("❌ Неверная ставка!\nПример: ставка 200 меньше")
                return

            if bet <= 0:
                await update.message.reply_text("❌ Ставка должна быть больше 0!")
                return
            if bet > 100000:
                await update.message.reply_text("❌ Максимальная ставка $100,000!")
                return
            if u["usd"] < bet:
                await update.message.reply_text(f"❌ Недостаточно денег!\nСтавка: ${bet:,.0f}\nБаланс: ${u['usd']:,.0f}")
                return

            guess = parts[2]
            msg = await update.message.reply_dice(emoji="🎰")
            result = msg.dice.value
            # 1-3 меньше, 4-6 больше
            actual = "меньше" if result <= 3 else "больше"
            win = guess == actual

            if win:
                u["usd"] += bet
                await update.message.reply_text(
                    f"🎰 Выпало: {result}\n"
                    f"✅ Ты угадал — {actual}!\n\n"
                    f"🎉 Выиграл +${bet:,.0f}\n"
                    f"💵 Баланс: ${u['usd']:,.0f}"
                )
            else:
                u["usd"] -= bet
                u["usd"] = max(0, u["usd"])
                await update.message.reply_text(
                    f"🎰 Выпало: {result}\n"f"❌ Выпало {actual}, ты ставил {guess}\n\n"
                    f"💸 Проиграл -${bet:,.0f}\n"
                    f"💵 Баланс: ${u['usd']:,.0f}"
                )
            save(data)
        else:
            await update.message.reply_text("❌ Формат: ставка 200 меньше\nили: ставка 200 больше")
        return

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
print("🎮 Бот запущен!")
app.run_polling()
