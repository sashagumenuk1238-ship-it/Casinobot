import os, json, time, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
DATA_FILE = "users.json"

# ── РЫБЫ ─────────────────────────────────────────────────────────────────────
FISH = {
    "karas":   {"name": "🐟 Карась",       "price": [20, 50],    "exp": 5,   "level": 1},
    "okun":    {"name": "🐠 Окунь",        "price": [80, 150],   "exp": 10,  "level": 1},
    "leshch":  {"name": "🐡 Лещ",          "price": [100, 200],  "exp": 15,  "level": 2},
    "shchuka": {"name": "🦈 Щука",         "price": [300, 600],  "exp": 30,  "level": 3},
    "som":     {"name": "🐬 Сом",          "price": [500, 1000], "exp": 50,  "level": 4},
    "osetr":   {"name": "🐋 Осётр",        "price": [2000, 5000],"exp": 100, "level": 6},
    "zolotaya":{"name": "👑 Золотая рыбка","price": [10000,50000],"exp": 500, "level": 8},
}

# ── УДОЧКИ ───────────────────────────────────────────────────────────────────
RODS = {
    "wood":    {"name": "🪵 Деревянная",  "price": 0,     "bonus": 0,   "level": 1},
    "steel":   {"name": "🔧 Стальная",    "price": 500,   "bonus": 10,  "level": 2},
    "carbon":  {"name": "💎 Карбоновая",  "price": 2000,  "bonus": 25,  "level": 4},
    "gold":    {"name": "🔱 Золотая",     "price": 10000, "bonus": 45,  "level": 6},
    "legend":  {"name": "👑 Легендарная", "price": 50000, "bonus": 70,  "level": 9},
}

# ── ЛЕСКА ────────────────────────────────────────────────────────────────────
LINES = {
    "basic":   {"name": "🧵 Обычная",     "price": 0,    "bonus": 0,  "level": 1},
    "nylon":   {"name": "🔵 Нейлоновая",  "price": 200,  "bonus": 5,  "level": 2},
    "fluoro":  {"name": "🟡 Флюрокарбон", "price": 800,  "bonus": 10, "level": 3},
    "braid":   {"name": "🔴 Плетёная",    "price": 2000, "bonus": 20, "level": 5},
    "titan":   {"name": "👑 Титановая",   "price": 10000,"bonus": 35, "level": 8},
}

# ── КАТУШКИ ──────────────────────────────────────────────────────────────────
REELS = {
    "basic":   {"name": "🔧 Простая",     "price": 0,    "bonus": 0,  "level": 1},
    "steel":   {"name": "⚙️ Стальная",    "price": 500,  "bonus": 5,  "level": 2},
    "pro":     {"name": "🔱 Профи",       "price": 3000, "bonus": 15, "level": 5},
    "legend":  {"name": "👑 Легендарная", "price": 15000,"bonus": 30, "level": 8},
}

# ── НАЖИВКА ──────────────────────────────────────────────────────────────────
BAITS = {
    "worm":    {"name": "🪱 Червь",       "price": 10,   "bonus": 0,  "level": 1},
    "cricket": {"name": "🦗 Кузнечик",    "price": 30,   "bonus": 5,  "level": 2},
    "maggot":  {"name": "🐛 Опарыш",      "price": 50,   "bonus": 10, "level": 3},
    "fry":     {"name": "🐟 Малёк",       "price": 150,  "bonus": 20, "level": 4},
    "shrimp":  {"name": "🦐 Креветка",    "price": 300,  "bonus": 30, "level": 5},
    "caviar":  {"name": "💎 Икра",        "price": 1000, "bonus": 50, "level": 7},
}

# ── ВОДОЁМЫ ──────────────────────────────────────────────────────────────────
WATERS = {
    "pond":    {"name": "🏞 Пруд",        "price": 0,     "level": 1, "fish": ["karas","okun"]},
    "river":   {"name": "🏔 Горная река", "price": 1000,  "level": 2, "fish": ["okun","leshch","shchuka"]},
    "sea":     {"name": "🌊 Море",        "price": 5000,  "level": 4, "fish": ["shchuka","som","osetr"]},
    "ocean":   {"name": "🏝 Океан",       "price": 20000, "level": 7, "fish": ["som","osetr","zolotaya"]},
    "secret":  {"name": "🌋 Тайный",      "price": 100000,"level": 9, "fish": ["osetr","zolotaya"]},
}

# ── ХРАНИЛИЩЕ ────────────────────────────────────────────────────────────────
STORAGES = { "box":     {"name": "📦 Ящик",            "price": 300,   "size": 15},
    "fridge":  {"name": "❄️ Холодильник",     "price": 1500,  "size": 40},
    "freezer": {"name": "🏭 Морозильник",     "price": 8000,  "size": 100},
    "ship":    {"name": "🚢 Трюм корабля",    "price": 30000, "size": 9999},
}

# ── УРОВНИ ───────────────────────────────────────────────────────────────────
LEVELS = [0,500,1500,3500,7000,15000,30000,60000,120000,250000]
LEVEL_NAMES = ["🪨 Новичок","🎣 Рыбак","🐟 Опытный","🐠 Умелый","🦈 Мастер","🐬 Эксперт","🐋 Профи","👑 Легенда","🌊 Морской волк","🏆 Великий рыбак"]

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
            "usd": 500.0,
            "exp": 0,
            "rod": "wood",
            "line": "basic",
            "reel": "basic",
            "bait": "worm",
            "water": "pond",
            "storage": "bucket",
            "fish": {},
            "casts": 0,
            "last_cast": 0,
            "quests": {},
            "last_quest": 0,
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    return data

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)

def get_catch_chance(user):
    u = user
    bonus = 0
    bonus += RODS[u["rod"]]["bonus"]
    bonus += LINES[u["line"]]["bonus"]
    bonus += REELS[u["reel"]]["bonus"]
    bonus += BAITS[u["bait"]]["bonus"]
    return min(95, 30 + bonus)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = get_user(uid)
    save(data)
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"🎣 Привет, {name}!\n\n"
        f"📖 Ты простой рыбак из маленького посёлка.\n"
        f"Начни с дешёвой удочкой и ведром.\n"
        f"Стань легендарным рыбаком и купи яхту! 🚢\n\n"
        f"📋 КОМАНДЫ:\n"
        f"рыбачить — закинуть удочку 🎣\n"
        f"баланс — мой счёт 💰\n"
        f"инвентарь — снаряжение и рыба 🎒\n"
        f"магазин — купить снаряжение 🏪\n"
        f"базар — продать рыбу 💵\n"
        f"водоёмы — выбрать место рыбалки 🌊\n"
        f"квесты — задания и награды 📜\n"
        f"профиль — уровень и статистика 👤\n\n"
        f"💵 Стартовый баланс: $500"
    )

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    uid = str(update.effective_user.id)
    data = get_user(uid)
    u = data[uid]

    # ── РЫБАЧИТЬ ──
    if text in ["рыбачить", "рыбалка", "закинуть", "удочку"]:
        now = time.time()
        # 10 забросов → 30 минут
        if u["casts"] >= 10:
            elapsed = now - u["last_cast"]
            if elapsed < 1800:
                mins = int((1800 - elapsed) / 60)
                await update.message.reply_text(f"😴 Устал! Отдохни {mins} мин.")
                return
            else:
                u["casts"] = 0

        # Проверка хранилища
        storage = STORAGES[u["storage"]]
        total_fish = sum(u["fish"].values())
        if total_fish >= storage["size"]:
            await update.message.reply_text(f"📦 {storage['name']} заполнено!\nПродай рыбу на базаре или купи большее хранилище.")
            return

        msg = await update.message.reply_dice(emoji="🎣")
        dice = msg.dice.value
        chance = get_catch_chance(u)
        water = WATERS[u["water"]]
        level = get_level(u["exp"])

        # Шанс поймать
        caught = dice <= int(chance / 16.67)

        if caught:
            available = [f for f in water["fish"] if FISH[f]["level"] <= level]
    "bucket":  {"name": "🪣 Ведро",           "price": 0,     "size": 5},if not available:
                available = ["karas"]
            fish_id = random.choice(available)
            fish = FISH[fish_id]
            price = random.randint(fish["price"][0], fish["price"][1])
            exp_gain = fish["exp"]

            if fish_id not in u["fish"]:
                u["fish"][fish_id] = 0
            u["fish"][fish_id] += 1
            u["exp"] += exp_gain

            old_level = level
            new_level = get_level(u["exp"])

            result = f"🎣 Поймал!\n{fish['name']}\n💰 Цена: ~${price}\n⭐ +{exp_gain} опыта"

            if new_level > old_level:
                result += f"\n\n🎉 НОВЫЙ УРОВЕНЬ {new_level}!\n{LEVEL_NAMES[new_level-1]}"
        else:
            result = "💨 Сорвалась... Попробуй ещё!"

        if u["casts"] == 0:
            u["last_cast"] = now
        u["casts"] += 1
        save(data)

        casts_left = 10 - u["casts"]
        await update.message.reply_text(f"{result}\n\n🎣 Забросов осталось: {casts_left}/10")
        return

    # ── БАЛАНС ──
    if text in ["баланс", "balance"]:
        level = get_level(u["exp"])
        await update.message.reply_text(
            f"💼 Баланс\n\n"
            f"💵 ${u['usd']:,.0f}\n"
            f"⭐ Уровень: {level} — {LEVEL_NAMES[level-1]}\n"
            f"📊 Опыт: {u['exp']}"
        )
        return

    # ── ПРОФИЛЬ ──
    if text in ["профиль", "профиль", "стат"]:
        level = get_level(u["exp"])
        next_exp = LEVELS[level] if level < 10 else "MAX"
        total_fish = sum(u["fish"].values())
        await update.message.reply_text(
            f"👤 ПРОФИЛЬ\n\n"
            f"🏆 {LEVEL_NAMES[level-1]}\n"
            f"⭐ Опыт: {u['exp']} / {next_exp}\n"
            f"💵 Баланс: ${u['usd']:,.0f}\n"
            f"🐟 Поймано рыб: {total_fish}\n\n"
            f"🎣 Удочка: {RODS[u['rod']]['name']}\n"
            f"🧵 Леска: {LINES[u['line']]['name']}\n"
            f"🎡 Катушка: {REELS[u['reel']]['name']}\n"
            f"🪱 Наживка: {BAITS[u['bait']]['name']}\n"
            f"🌊 Водоём: {WATERS[u['water']]['name']}\n"
            f"📦 Хранилище: {STORAGES[u['storage']]['name']}"
        )
        return

    # ── ИНВЕНТАРЬ ──
    if text in ["инвентарь", "рыба", "улов"]:
        if not u["fish"] or sum(u["fish"].values()) == 0:
            await update.message.reply_text("🎒 Инвентарь пуст!\nНапиши рыбачить чтобы поймать рыбу.")
            return
        storage = STORAGES[u["storage"]]
        total = sum(u["fish"].values())
        msg = f"🎒 ИНВЕНТАРЬ ({total}/{storage['size']})\n\n"
        total_value = 0
        for fid, count in u["fish"].items():
            if count > 0:
                fish = FISH[fid]
                avg_price = (fish["price"][0] + fish["price"][1]) // 2
                value = avg_price * count
                total_value += value
                msg += f"{fish['name']} x{count} (~${value:,})\n"
        msg += f"\n💰 Примерная стоимость: ${total_value:,}"
        await update.message.reply_text(msg)
        return

    # ── БАЗАР ──
    if text in ["базар", "продать всё", "продать все"]:
        if not u["fish"] or sum(u["fish"].values()) == 0:
            await update.message.reply_text("🏪 Нечего продавать!\nПоймай рыбу сначала.")
            return
        total = 0
        msg = "🏪 БАЗАР — Продано:\n\n"
        for fid, count in u["fish"].items():
            if count > 0:
                fish = FISH[fid]
                price = random.randint(fish["price"][0], fish["price"][1]) * count
                total += price
                msg += f"{fish['name']} x{count} = ${price:,}\n"
        u["fish"] = {}
        u["usd"] += total
        save(data)
        msg += f"\n💵 Итого: +${total:,}\n💰 Баланс: ${u['usd']:,.0f}"
        await update.message.reply_text(msg)
        return# ── ВОДОЁМЫ ──
    if text in ["водоёмы", "водоем", "место"]:
        level = get_level(u["exp"])
        rows = []
        for wid, w in WATERS.items():
            locked = "🔒 " if w["level"] > level else ""
            current = "✅ " if u["water"] == wid else ""
            rows.append([InlineKeyboardButton(
                f"{current}{locked}{w['name']} | ур.{w['level']} | ${w['price']:,}",
                callback_data=f"water_{wid}"
            )])
        await update.message.reply_text(
            f"🌊 ВОДОЁМЫ\n\nТвой уровень: {level}\nВыбери место для рыбалки:",
            reply_markup=InlineKeyboardMarkup(rows)
        )
        return

    # ── МАГАЗИН ──
    if text in ["магазин", "shop", "купить"]:
        rows = [
            [InlineKeyboardButton("🪵 Удочки", callback_data="shop_rods")],
            [InlineKeyboardButton("🧵 Леска", callback_data="shop_lines")],
            [InlineKeyboardButton("🎡 Катушки", callback_data="shop_reels")],
            [InlineKeyboardButton("🪱 Наживка", callback_data="shop_baits")],
            [InlineKeyboardButton("📦 Хранилище", callback_data="shop_storage")],
        ]
        await update.message.reply_text(
            f"🏪 МАГАЗИН\n💵 Баланс: ${u['usd']:,.0f}\n\nЧто купить?",
            reply_markup=InlineKeyboardMarkup(rows)
        )
        return

    # ── КВЕСТЫ ──
    if text in ["квесты", "задания", "quest"]:
        level = get_level(u["exp"])
        total_fish = sum(u["fish"].values())
        msg = "📜 ЕЖЕДНЕВНЫЕ КВЕСТЫ\n\n"
        quests = [
            {"name": "Поймай 5 рыб", "done": total_fish >= 5, "reward": "$200 + 50 опыта"},
            {"name": "Заработай $500", "done": u["usd"] >= 500, "reward": "$300 + 80 опыта"},
            {"name": "Сделай 10 забросов", "done": u["casts"] >= 10, "reward": "$100 + 40 опыта"},
        ]
        for q in quests:
            status = "✅" if q["done"] else "⬜"
            msg += f"{status} {q['name']}\n🎁 {q['reward']}\n\n"
        await update.message.reply_text(msg)
        return

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    data = get_user(uid)
    u = data[uid]
    d = query.data
    level = get_level(u["exp"])

    # ── ВОДОЁМ ──
    if d.startswith("water_"):
        wid = d[6:]
        water = WATERS[wid]
        if water["level"] > level:
            await query.edit_message_text(f"🔒 Нужен уровень {water['level']}!\nТвой уровень: {level}")
            return
        if u["usd"] < water["price"] and water["price"] > 0:
            await query.edit_message_text(f"❌ Нужно ${water['price']:,}\nУ тебя ${u['usd']:,.0f}")
            return
        if water["price"] > 0 and u["water"] != wid:
            u["usd"] -= water["price"]
        u["water"] = wid
        save(data)
        await query.edit_message_text(f"✅ Теперь рыбачишь в {water['name']}!")
        return

    # ── МАГАЗИН УДОЧКИ ──
    if d == "shop_rods":
        rows = []
        for rid, r in RODS.items():
            owned = "✅ " if u["rod"] == rid else ""
            locked = "🔒 " if r["level"] > level else ""
            rows.append([InlineKeyboardButton(
                f"{owned}{locked}{r['name']} | ${r['price']:,} | +{r['bonus']}%",
                callback_data=f"buy_rod_{rid}"
            )])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("🪵 УДОЧКИ:", reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("buy_rod_"):
        rid = d[8:]
        rod = RODS[rid]
        if rod["level"] > level:
            await query.answer(f"🔒 Нужен уровень {rod['level']}!", show_alert=True)
            return
        if u["usd"] < rod["price"]:
            await query.answer(f"❌ Нужно ${rod['price']:,}", show_alert=True)
            return
        u["usd"] -= rod["price"]
        u["rod"] = rid
        save(data)
        await query.answer(f"✅ Куплена {rod['name']}!", show_alert=True)
        return# ── МАГАЗИН ЛЕСКА ──
    if d == "shop_lines":
        rows = []
        for lid, l in LINES.items():
            owned = "✅ " if u["line"] == lid else ""
            locked = "🔒 " if l["level"] > level else ""
            rows.append([InlineKeyboardButton(
                f"{owned}{locked}{l['name']} | ${l['price']:,} | +{l['bonus']}%",
                callback_data=f"buy_line_{lid}"
            )])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("🧵 ЛЕСКА:", reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("buy_line_"):
        lid = d[9:]
        line = LINES[lid]
        if line["level"] > level:
            await query.answer(f"🔒 Нужен уровень {line['level']}!", show_alert=True)
            return
        if u["usd"] < line["price"]:
            await query.answer(f"❌ Нужно ${line['price']:,}", show_alert=True)
            return
        u["usd"] -= line["price"]
        u["line"] = lid
        save(data)
        await query.answer(f"✅ Куплена {line['name']}!", show_alert=True)
        return

    # ── МАГАЗИН КАТУШКИ ──
    if d == "shop_reels":
        rows = []
        for rid, r in REELS.items():
            owned = "✅ " if u["reel"] == rid else ""
            locked = "🔒 " if r["level"] > level else ""
            rows.append([InlineKeyboardButton(
                f"{owned}{locked}{r['name']} | ${r['price']:,} | +{r['bonus']}%",
                callback_data=f"buy_reel_{rid}"
            )])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("🎡 КАТУШКИ:", reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("buy_reel_"):
        rid = d[9:]
        reel = REELS[rid]
        if reel["level"] > level:
            await query.answer(f"🔒 Нужен уровень {reel['level']}!", show_alert=True)
            return
        if u["usd"] < reel["price"]:
            await query.answer(f"❌ Нужно ${reel['price']:,}", show_alert=True)
            return
        u["usd"] -= reel["price"]
        u["reel"] = rid
        save(data)
        await query.answer(f"✅ Куплена {reel['name']}!", show_alert=True)
        return

    # ── МАГАЗИН НАЖИВКА ──
    if d == "shop_baits":
        rows = []
        for bid, b in BAITS.items():
            owned = "✅ " if u["bait"] == bid else ""
            locked = "🔒 " if b["level"] > level else ""
            rows.append([InlineKeyboardButton(
                f"{owned}{locked}{b['name']} | ${b['price']:,} | +{b['bonus']}%",
                callback_data=f"buy_bait_{bid}"
            )])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("🪱 НАЖИВКА:", reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("buy_bait_"):
        bid = d[9:]
        bait = BAITS[bid]
        if bait["level"] > level:
            await query.answer(f"🔒 Нужен уровень {bait['level']}!", show_alert=True)
            return
        if u["usd"] < bait["price"]:
            await query.answer(f"❌ Нужно ${bait['price']:,}", show_alert=True)
            return
        u["usd"] -= bait["price"]
        u["bait"] = bid
        save(data)
        await query.answer(f"✅ Куплена {bait['name']}!", show_alert=True)
        return

    # ── МАГАЗИН ХРАНИЛИЩЕ ──
    if d == "shop_storage":
        rows = []
        for sid, s in STORAGES.items():
            owned = "✅ " if u["storage"] == sid else ""
            rows.append([InlineKeyboardButton(
                f"{owned}{s['name']} | ${s['price']:,} | {s['size']} рыб",
                callback_data=f"buy_storage_{sid}"
            )])
        rows.append([InlineKeyboardButton("🔙 Назад", callback_data="shop_back")])
        await query.edit_message_text("📦 ХРАНИЛИЩЕ:", reply_markup=InlineKeyboardMarkup(rows))
        returnif d.startswith("buy_storage_"):
        sid = d[12:]
        storage = STORAGES[sid]
        if u["usd"] < storage["price"]:
            await query.answer(f"❌ Нужно ${storage['price']:,}", show_alert=True)
            return
        u["usd"] -= storage["price"]
        u["storage"] = sid
        save(data)
        await query.answer(f"✅ Куплено {storage['name']}!", show_alert=True)
        return

    if d == "shop_back":
        rows = [
            [InlineKeyboardButton("🪵 Уд
