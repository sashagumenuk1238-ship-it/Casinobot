import os, json, time, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
DATA_FILE = "users.json"

FISH = {
    "karas":    {"name": "Карась",  "emoji": "🐟", "price_min": 20,   "price_max": 50,    "exp": 5,   "rare": 40},
    "okun":     {"name": "Окунь",   "emoji": "🐠", "price_min": 80,   "price_max": 150,   "exp": 10,  "rare": 30},
    "leshch":   {"name": "Лещ",     "emoji": "🐡", "price_min": 100,  "price_max": 200,   "exp": 15,  "rare": 20},
    "shchuka":  {"name": "Щука",    "emoji": "🦈", "price_min": 300,  "price_max": 600,   "exp": 30,  "rare": 7},
    "som":      {"name": "Сом",     "emoji": "🐬", "price_min": 500,  "price_max": 1000,  "exp": 50,  "rare": 2},
    "zolotaya": {"name": "Золотая", "emoji": "👑", "price_min": 10000,"price_max": 50000, "exp": 500, "rare": 1},
}

RODS = {
    "wood":   {"name": "Деревянная", "emoji": "🪵", "price": 0,     "bonus": 0},
    "steel":  {"name": "Стальная",   "emoji": "🔧", "price": 500,   "bonus": 15},
    "carbon": {"name": "Карбоновая", "emoji": "💎", "price": 2000,  "bonus": 30},
    "gold":   {"name": "Золотая",    "emoji": "✨", "price": 10000, "bonus": 50},
}

LINES = {
    "basic":  {"name": "Обычная",    "emoji": "🧵", "price": 0,    "bonus": 0},
    "nylon":  {"name": "Нейлоновая", "emoji": "🔵", "price": 200,  "bonus": 10},
    "braid":  {"name": "Плетёная",   "emoji": "🔴", "price": 2000, "bonus": 25},
}

BAITS = {
    "worm":   {"name": "Червь",    "emoji": "🪱", "price": 10,   "bonus": 0},
    "maggot": {"name": "Опарыш",   "emoji": "🐛", "price": 50,   "bonus": 10},
    "shrimp": {"name": "Креветка", "emoji": "🦐", "price": 300,  "bonus": 25},
    "caviar": {"name": "Икра",     "emoji": "🟡", "price": 1000, "bonus": 45},
}

WATERS = {
    "pond":  {"name": "Пруд",  "emoji": "🏞", "price": 0,     "minlevel": 1, "fish": ["karas","okun","leshch"]},
    "river": {"name": "Река",  "emoji": "🏔", "price": 1000,  "minlevel": 2, "fish": ["okun","leshch","shchuka"]},
    "sea":   {"name": "Море",  "emoji": "🌊", "price": 5000,  "minlevel": 4, "fish": ["shchuka","som"]},
    "ocean": {"name": "Океан", "emoji": "🏝", "price": 20000, "minlevel": 7, "fish": ["som","zolotaya"]},
}

STORAGES = {
    "bucket":  {"name": "Ведро",       "emoji": "🪣", "price": 0,    "size": 5},
    "box":     {"name": "Ящик",        "emoji": "📦", "price": 300,  "size": 20},
    "fridge":  {"name": "Холодильник", "emoji": "❄",  "price": 1500, "size": 50},
    "freezer": {"name": "Морозильник", "emoji": "🏭", "price": 8000, "size": 150},
}

LEVELS = [0,500,1500,3500,7000,15000,30000,60000,120000,250000]
LEVEL_NAMES = ["Новичок","Рыбак","Опытный","Умелый","Мастер","Эксперт","Профи","Легенда","Морской волк","Великий рыбак"]
LEVEL_EMOJI = ["🪨","🎣","🐟","🐠","🦈","🐬","🐋","👑","🌊","🏆"]

def get_level(exp):
    level = 1
    for i, req in enumerate(LEVELS):
        if exp >= req:
            level = i + 1
    return min(level, 10)

def get_user(uid):
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
    except:
        data = {}
    if uid not in data:
        data[uid] = {
            "usd": 500.0, "exp": 0, "fish": {},
            "casts": 0, "last_cast": 0,
            "rod": "wood", "line": "basic",
            "bait": "worm", "water": "pond", "storage": "bucket",
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    return data

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)

def catch_fish(u):
    bonus = RODS[u["rod"]]["bonus"] + LINES[u["line"]]["bonus"] + BAITS[u["bait"]]["bonus"]
    roll = random.randint(1, 100)
    if roll > 45 + bonus // 2:
        return None
    water = WATERS[u["water"]]
    pool = []
    for fid in water["fish"]:
        for _ in range(FISH[fid]["rare"]):
            pool.append(fid)
    if not pool:
        return "karas"
    return random.choice(pool)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    get_user(uid)
    name = update.effective_user.first_name
    await update.message.reply_text(
        "🎣 Привет, " + name + "!\n\n"
        "Ты начинающий рыбак!\nСтань легендой рыбалки!\n\n"
        "рыбачить — закинуть удочку\n"
        "баланс — мой счёт\n"
        "профиль — уровень\n"
        "инвентарь — моя рыба\n"
        "базар — продать рыбу\n"
        "магазин — снаряжение\n"
        "водоёмы — выбрать место\n"
        "квесты — задания\n\n"
        "💵 Стартовый баланс: $500"
    )

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    uid = str(update.effective_user.id)
    data = get_user(uid)
    u = data[uid]
    level = get_level(u["exp"])

    if text in ["рыбачить", "рыбалка", "удочку"]:
        now = time.time()
        if u["casts"] >= 10:
            elapsed = now - u["last_cast"]
            if elapsed < 1800:
                mins = int((1800 - elapsed) / 60)
                await update.message.reply_text("😴 Устал! Отдохни " + str(mins) + " мин.")
                return
            else:
                u["casts"] = 0
        storage = STORAGES[u["storage"]]
        total_fish = sum(v.get("count", 0) for v in u["fish"].values())
        if total_fish >= storage["size"]:
            await update.message.reply_text("📦 Хранилище полное!\nПродай рыбу на базаре!")
            return
        msg = await update.message.reply_dice(emoji="🎣")
        fid = catch_fish(u)
        if fid:
            fish = FISH[fid]
            price = random.randint(fish["price_min"], fish["price_max"])
            old_level = level
            u["exp"] += fish["exp"]
            new_level = get_level(u["exp"])
            if fid not in u["fish"]:
                u["fish"][fid] = {"count": 0}
            u["fish"][fid]["count"] += 1
            result = "🎣 Поймал!\n" + fish["emoji"] + " " + fish["name"] + "\n💰 ~$" + str(price) + "\n⭐ +" + str(fish["exp"]) + " опыта"
            if new_level > old_level:
                result += "\n\n🎉 УРОВЕНЬ " + str(new_level) + "! " + LEVEL_EMOJI[new_level-1] + " " + LEVEL_NAMES[new_level-1]
        else:
            result = "💨 Сорвалась!"
        if u["casts"] == 0:
            u["last_cast"] = now
        u["casts"] += 1
        save(data)
        await update.message.reply_text(result + "\n\n🎣 Забросов: " + str(10 - u["casts"]) + "/10")
        return

    if text in ["баланс", "balance"]:
        await update.message.reply_text(
            "💼 Баланс\n\n"
            "💵 $" + str(int(u["usd"])) + "\n"
            "🎣 " + RODS[u["rod"]]["name"] + "\n"
            "🧵 " + LINES[u["line"]]["name"] + "\n"
            "🪱 " + BAITS[u["bait"]]["name"]
        )
        return

    if text in ["профиль", "уровень"]:
        total = sum(v.get("count", 0) for v in u["fish"].values())
        next_exp = LEVELS[level] if level < 10 else 999999
        await update.message.reply_text(
            LEVEL_EMOJI[level-1] + " " + LEVEL_NAMES[level-1] + "\n\n"
            "⭐ Опыт: " + str(u["exp"]) + " / " + str(next_exp) + "\n"
            "💵 Баланс: $" + str(int(u["usd"])) + "\n"
            "🐟 Поймано: " + str(total) + " рыб\n"
            "🌊 Водоём: " + WATERS[u["water"]]["name"] + "\n"
            "📦 Хранилище: " + STORAGES[u["storage"]]["name"]
        )
        return

    if text in ["инвентарь", "рыба", "улов"]:
        total = sum(v.get("count", 0) for v in u["fish"].values())
        storage = STORAGES[u["storage"]]
        if total == 0:
            await update.message.reply_text("🎒 Пусто! Напиши рыбачить")
            return
        msg = "🎒 РЫБА (" + str(total) + "/" + str(storage["size"]) + "):\n\n"

val = 0
        for fid, info in u["fish"].items():
            if info.get("count", 0) > 0:
                fish = FISH[fid]
                avg = (fish["price_min"] + fish["price_max"]) // 2 * info["count"]
                val += avg
                msg += fish["emoji"] + " " + fish["name"] + " x" + str(info["count"]) + " (~$" + str(avg) + ")\n"
        msg += "\n💰 Примерно: $" + str(val)
        await update.message.reply_text(msg)
        return

    if text in ["базар", "продать", "продать всё"]:
        total = sum(v.get("count", 0) for v in u["fish"].values())
        if total == 0:
            await update.message.reply_text("Нечего продавать!")
            return
        earned = 0
        msg = "🏪 Продано:\n\n"
        for fid, info in u["fish"].items():
            if info.get("count", 0) > 0:
                fish = FISH[fid]
                price = random.randint(fish["price_min"], fish["price_max"]) * info["count"]
                earned += price
                msg += fish["emoji"] + " " + fish["name"] + " x" + str(info["count"]) + " = $" + str(price) + "\n"
        u["fish"] = {}
        u["usd"] += earned
        save(data)
        msg += "\n💵 +" + str(earned) + "\n💰 Баланс: $" + str(int(u["usd"]))
        await update.message.reply_text(msg)
        return

    if text in ["водоёмы", "водоем", "место"]:
        rows = []
        for wid, w in WATERS.items():
            locked = level < w["minlevel"]
            cur = "✅ " if u["water"] == wid else ""
            lock = "🔒 " if locked else ""
            rows.append([InlineKeyboardButton(
                cur + lock + w["emoji"] + " " + w["name"] + " | ур." + str(w["minlevel"]) + " | $" + str(w["price"]),
                callback_data="water_" + wid
            )])
        await update.message.reply_text("🌊 ВОДОЁМЫ\nУровень: " + str(level), reply_markup=InlineKeyboardMarkup(rows))
        return

    if text in ["магазин", "shop"]:
        rows = [
            [InlineKeyboardButton("🪵 Удочки", callback_data="shop_rods")],
            [InlineKeyboardButton("🧵 Леска", callback_data="shop_lines")],
            [InlineKeyboardButton("🪱 Наживка", callback_data="shop_baits")],
            [InlineKeyboardButton("📦 Хранилище", callback_data="shop_storage")],
        ]
        await update.message.reply_text("🏪 МАГАЗИН\n💵 $" + str(int(u["usd"])), reply_markup=InlineKeyboardMarkup(rows))
        return

    if text in ["квесты", "задания"]:
        total = sum(v.get("count", 0) for v in u["fish"].values())
        q1 = "✅" if total >= 5 else "⬜"
        q2 = "✅" if u["usd"] >= 1000 else "⬜"
        q3 = "✅" if u["casts"] >= 5 else "⬜"
        await update.message.reply_text(
            "📜 КВЕСТЫ\n\n" +
            q1 + " Поймай 5 рыб — 🎁 +$200\n\n" +
            q2 + " Накопи $1000 — 🎁 +$300\n\n" +
            q3 + " Сделай 5 забросов — 🎁 +$100"
        )
        return

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    data = get_user(uid)
    u = data[uid]
    d = query.data
    level = get_level(u["exp"])

    if d.startswith("water_"):
        wid = d[6:]
        w = WATERS[wid]
        if level < w["minlevel"]:
            await query.answer("Нужен уровень " + str(w["minlevel"]) + "!", show_alert=True)
            return
        if u["usd"] < w["price"] and u["water"] != wid:
            await query.answer("Нужно $" + str(w["price"]) + "!", show_alert=True)
            return
        if u["water"] != wid and w["price"] > 0:
            u["usd"] -= w["price"]
        u["water"] = wid
        save(data)
        await query.edit_message_text("✅ Теперь рыбачишь в " + w["emoji"] + " " + w["name"] + "!")
        return

    if d == "shop_rods":

rows = []
        for rid, r in RODS.items():
            cur = "✅ " if u["rod"] == rid else ""
            rows.append([InlineKeyboardButton(cur + r["emoji"] + " " + r["name"] + " | $" + str(r["price"]) + " | +" + str(r["bonus"]) + "%", callback_data="buy_rod_" + rid)])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("🪵 УДОЧКИ\n💵 $" + str(int(u["usd"])), reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("buy_rod_"):
        rid = d[8:]
        r = RODS[rid]
        if u["rod"] == rid:
            await query.answer("Уже есть!", show_alert=True)
            return
        if u["usd"] < r["price"]:
            await query.answer("Нужно $" + str(r["price"]) + "!", show_alert=True)
            return
        u["usd"] -= r["price"]
        u["rod"] = rid
        save(data)
        await query.answer(r["name"] + " куплена!", show_alert=True)
        return

    if d == "shop_lines":
        rows = []
        for lid, l in LINES.items():
            cur = "✅ " if u["line"] == lid else ""
            rows.append([InlineKeyboardButton(cur + l["emoji"] + " " + l["name"] + " | $" + str(l["price"]) + " | +" + str(l["bonus"]) + "%", callback_data="buy_line_" + lid)])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("🧵 ЛЕСКА\n💵 $" + str(int(u["usd"])), reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("buy_line_"):
        lid = d[9:]
        l = LINES[lid]
        if u["line"] == lid:
            await query.answer("Уже есть!", show_alert=True)
            return
        if u["usd"] < l["price"]:
            await query.answer("Нужно $" + str(l["price"]) + "!", show_alert=True)
            return
        u["usd"] -= l["price"]
        u["line"] = lid
        save(data)
        await query.answer(l["name"] + " куплена!", show_alert=True)
        return

    if d == "shop_baits":
        rows = []
        for bid, b in BAITS.items():
            cur = "✅ " if u["bait"] == bid else ""
            rows.append([InlineKeyboardButton(cur + b["emoji"] + " " + b["name"] + " | $" + str(b["price"]) + " | +" + str(b["bonus"]) + "%", callback_data="buy_bait_" + bid)])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("🪱 НАЖИВКА\n💵 $" + str(int(u["usd"])), reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("buy_bait_"):
        bid = d[9:]
        b = BAITS[bid]
        if u["bait"] == bid:
            await query.answer("Уже есть!", show_alert=True)
            return
        if u["usd"] < b["price"]:
            await query.answer("Нужно $" + str(b["price"]) + "!", show_alert=True)
            return
        u["usd"] -= b["price"]
        u["bait"] = bid
        save(data)
        await query.answer(b["name"] + " куплена!", show_alert=True)
        return

    if d == "shop_storage":
        rows = []
        for sid, s in STORAGES.items():
            cur = "✅ " if u["storage"] == sid else ""
            rows.append([InlineKeyboardButton(cur + s["emoji"] + " " + s["name"] + " | $" + str(s["price"]) + " | " + str(s["size"]) + " рыб", callback_data="buy_storage_" + sid)])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("📦 ХРАНИЛИЩЕ\n💵 $" + str(int(u["usd"])), reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("buy_storage_"):
        sid = d[12:]
        s = STORAGES[sid]
        if u["storage"] == sid:
            await query.answer("Уже есть!", show_alert=True)
            return
        if u["usd"] < s["price"]:
            await query.answer("Нужно $" + str(s["price"]) + "!", show_alert=True)
            return
        u["usd"] -= s["price"]
        u["storage"] = sid
        save(data)
        await query.answer(s["name"] + " куплено!", show_alert=True)
        return

if d == "shop_back":
        rows = [
            [InlineKeyboardButton("🪵 Удочки", callback_data="shop_rods")],
            [InlineKeyboardButton("🧵 Леска", callback_data="shop_lines")],
            [InlineKeyboardButton("🪱 Наживка", callback_data="shop_baits")],
            [InlineKeyboardButton("📦 Хранилище", callback_data="shop_storage")],
        ]
        await query.edit_message_text("🏪 МАГАЗИН\n💵 $" + str(int(u["usd"])), reply_markup=InlineKeyboardMarkup(rows))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
print("🎣 Бот запущен!")
app.run_polling()
