import os, json, time, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ContextTypes,
    MessageHandler, filters
)

TOKEN = os.environ.get("TOKEN")
DATA = "users.json"

FISH = {
    "pond": {"Карась":[20,50,40],"Окунь":[80,150,35],"Лещ":[100,200,25]},
    "river": {"Окунь":[80,150,30],"Лещ":[100,200,30],"Щука":[300,600,40]},
    "sea": {"Щука":[300,600,30],"Сом":[500,1000,40],"Осетр":[2000,5000,30]},
    "ocean": {"Сом":[500,1000,20],"Осетр":[2000,5000,40],"Золотая":[10000,50000,40]}
}

RODS = {
    "wood":["Деревянная",0,0],
    "steel":["Стальная",500,15],
    "carbon":["Карбоновая",2000,30],
    "gold":["Золотая",10000,50]
}

LINES = {
    "basic":["Обычная",0,0],
    "nylon":["Нейлоновая",200,10],
    "braid":["Плетеная",2000,25]
}

BAITS = {
    "worm":["Червь",10,0],
    "maggot":["Опарыш",50,10],
    "shrimp":["Креветка",300,25],
    "caviar":["Икра",1000,45]
}

WATERS = {
    "pond":["Пруд",0],
    "river":["Река",1000],
    "sea":["Море",5000],
    "ocean":["Океан",20000]
}

STORAGE = {
    "bucket":["Ведро",0,5],
    "box":["Ящик",300,20],
    "fridge":["Холодильник",1500,50],
    "freezer":["Морозильник",8000,150]
}

def db():
    try:
        with open(DATA) as f:
            return json.load(f)
    except:
        return {}

def save(d):
    with open(DATA, "w") as f:
        json.dump(d, f, ensure_ascii=False)

def gu(uid):
    d = db()
    if uid not in d:
        d[uid] = {
            "usd":500.0,"exp":0,"fish":{},
            "casts":0,"last":0,
            "rod":"wood","line":"basic",
            "bait":"worm","water":"pond",
            "storage":"bucket"
        }
        save(d)
    return d

def lvl(exp):
    levels=[0,500,1500,3500,7000,15000,30000,60000,120000,250000]
    names=["Новичок","Рыбак","Опытный","Умелый","Мастер","Эксперт","Профи","Легенда","Морской волк","Великий рыбак"]
    lv=1
    for i,r in enumerate(levels):
        if exp>=r: lv=i+1
    return min(lv,10), names[min(lv,10)-1]

def bonus(u):
    return RODS[u["rod"]][2] + LINES[u["line"]][2] + BAITS[u["bait"]][2]

# ===== КОМАНДЫ =====

async def start(update, ctx):
    uid = str(update.effective_user.id)
    gu(uid)
    await update.message.reply_text(
        "🎣 Привет!\n\n"
        "/fish или напиши 'рыбачить'\n"
        "/shop или 'магазин'\n"
        "/inv или 'инв'\n"
    )

async def fish(update, ctx):
    uid = str(update.effective_user.id)
    d = gu(uid)
    u = d[uid]

    now = time.time()

    if u["casts"] >= 10:
        el = now - u["last"]
        if el < 1800:
            await update.message.reply_text(f"😴 Подожди {int((1800-el)/60)} мин")
            return
        u["casts"] = 0

    st = STORAGE[u["storage"]]
    if sum(u["fish"].values()) >= st[2]:
        await update.message.reply_text("📦 Хранилище заполнено!")
        return

    m = await update.message.reply_dice("🎲")
    caught = m.dice.value >= 4 or random.randint(1,100) <= bonus(u)//2

    if caught:
        fw = FISH[u["water"]]
        pool = []
        for n,dta in fw.items():
            pool += [n]*dta[2]

        name = random.choice(pool)
        price = random.randint(*fw[name][:2])

        u["fish"][name] = u["fish"].get(name,0)+1
        u["exp"] += 10

        result = f"🎣 Поймал {name}!\n~${price}"
    else:
        result = "💨 Сорвалась!"

    if u["casts"] == 0:
        u["last"] = now

    u["casts"] += 1
    save(d)

    await update.message.reply_text(result)

async def shop(update, ctx):
    rows = [
        [InlineKeyboardButton("🎣 Удочки", callback_data="s_rod")],
        [InlineKeyboardButton("🧵 Леска", callback_data="s_line")]
    ]
    await update.message.reply_text("🏪 Магазин", reply_markup=InlineKeyboardMarkup(rows))

# ===== КНОПКИ =====

async def btn(update, ctx):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Открыто меню")

# ===== ЗАПУСК =====

app = ApplicationBuilder().token(TOKEN).build()

# команды
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("fish", fish))
app.add_handler(CommandHandler("shop", shop))

# русский текст
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^рыбачить$"), fish))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^магазин$"), shop))

# кнопки
app.add_handler(CallbackQueryHandler(btn))

print("Bot started!")
app.run_polling()
