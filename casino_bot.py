import os,json,time,random,asyncio
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup,ReplyKeyboardMarkup,KeyboardButton
from telegram.ext import ApplicationBuilder,CommandHandler,CallbackQueryHandler,MessageHandler,filters,ContextTypes

TOKEN=os.environ.get("TOKEN")
DATA="users.json"

FISH={
    "karas":  {"name":"Карась",   "weight":0.5,  "price":[20,50],    "exp":5,  "rare":40},
    "okun":   {"name":"Окунь",    "weight":0.8,  "price":[80,150],   "exp":10, "rare":30},
    "leshch": {"name":"Лещ",      "weight":1.5,  "price":[100,200],  "exp":15, "rare":20},
    "shchuka":{"name":"Щука",     "weight":3.0,  "price":[300,600],  "exp":30, "rare":7},
    "som":    {"name":"Сом",      "weight":8.0,  "price":[500,1000], "exp":50, "rare":2},
    "osetr":  {"name":"Осётр",    "weight":15.0, "price":[2000,5000],"exp":100,"rare":1},
}

RODS={"wood":["Деревянная",0,0],"steel":["Стальная",500,15],"carbon":["Карбоновая",2000,30],"gold":["Золотая",10000,50]}
LINES={"basic":["Обычная",0,0],"nylon":["Нейлоновая",200,10],"braid":["Плетёная",2000,25]}
BAITS={"worm":["Червь",10,0],"maggot":["Опарыш",50,10],"shrimp":["Креветка",300,25],"caviar":["Икра",1000,45]}
STORAGE={"bucket":["Ведро",0,5],"box":["Ящик",300,20],"fridge":["Холодильник",1500,50],"freezer":["Морозильник",8000,150]}
VEHICLES={
    "none": ["Пешком",0,{"pond":0,"river":1800,"sea":-1,"ocean":-1}],
    "bike": ["Велосипед",200,{"pond":0,"river":900,"sea":-1,"ocean":-1}],
    "vaz":  ["Жигули",3000,{"pond":0,"river":300,"sea":-1,"ocean":-1}],
    "suv":  ["Внедорожник",15000,{"pond":0,"river":0,"sea":-1,"ocean":-1}],
    "barge":["Баржа",40000,{"pond":0,"river":0,"sea":1200,"ocean":-1}],
    "yacht":["Яхта",120000,{"pond":0,"river":0,"sea":0,"ocean":1800}],
}
WATERS={
    "pond":  ["Пруд", ["karas","okun","leshch"],1],
    "river": ["Река", ["okun","leshch","shchuka"],3],
    "sea":   ["Море", ["shchuka","som","osetr"],5],
    "ocean": ["Океан",["som","osetr"],8],
}
LEVELS=[0,500,1500,3500,7000,15000,30000,60000,120000,250000]
LNAMES=["Новичок","Рыбак","Опытный","Умелый","Мастер","Эксперт","Профи","Легенда","Морской волк","Великий рыбак"]

MENU=ReplyKeyboardMarkup([
    [KeyboardButton("🎣 Рыбачить"), KeyboardButton("🎒 Инвентарь")],
    [KeyboardButton("🏪 Продать"),  KeyboardButton("💰 Баланс")],
    [KeyboardButton("🛒 Магазин"),  KeyboardButton("🌊 Водоемы")],
    [KeyboardButton("🚗 Гараж"),    KeyboardButton("📜 Квесты")],
    [KeyboardButton("📊 Профиль"),  KeyboardButton("💹 Курс рыб")],
],resize_keyboard=True)

def db():
    try:
        with open(DATA) as f: return json.load(f)
    except: return {}

def save(d):
    with open(DATA,"w") as f: json.dump(d,f,ensure_ascii=False)

def gu(uid):
    d=db()
    if uid not in d:
        d[uid]={"usd":200.0,"exp":0,"fish":{},"total_caught":0,"casts":0,"last":0,"rod":"wood","line":"basic","bait":"worm","water":"pond","storage":"bucket","vehicle":"none","fishing":False}
        save(d)
    return d

def lvl(exp):
    lv=1
    for i,r in enumerate(LEVELS):
        if exp>=r: lv=i+1
    return min(lv,10)

def get_bonus(u):
    return RODS[u["rod"]][2]+LINES[u["line"]][2]+BAITS[u["bait"]][2]

def can_go(u,water):
    return VEHICLES[u["vehicle"]][2].get(water,-1)

def fish_price(fid,weight):
    f=FISH[fid]
    base=random.randint(f["price"][0],f["price"][1])
    return int(base*weight)

async def start(update,ctx):
    uid=str(update.effective_user.id)
    gu(uid)
    name=update.effective_user.first_name
    await update.message.reply_text(
        "🎣 Привет "+name+"!\n\n"
        "Ты начинающий рыбак!\n"
        "Стань легендой!\n\n"
        "💵 Старт: $200\n\n"
        "Используй кнопки меню внизу!",
        reply_markup=MENU
    )

async def do_fish(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]

    if u.get("fishing"):
        await update.message.reply_text("Уже рыбачишь! Жди результата",reply_markup=MENU)
        return

    now=time.time()
    if u["casts"]>=10:
        el=now-u["last"]
        if el<1800:
            mins=int((1800-el)/60)
            await update.message.reply_text("😴 Устал! Отдохни "+str(mins)+" мин",reply_markup=MENU)
            return
        u["casts"]=0

    st=STORAGE[u["storage"]]
    total=sum(u["fish"].values())
    if total>=st[2]:
        await update.message.reply_text("📦 Хранилище полное!\nНажми Продать",reply_markup=MENU)
        return

    water=u["water"]
    travel=can_go(u,water)
    lv=lvl(u["exp"])
    wdata=WATERS[water]
    if lv<wdata[2]:
        await update.message.reply_text("Нужен уровень "+str(wdata[2])+" для "+wdata[0]+"!\nТвой уровень: "+str(lv),reply_markup=MENU)
        return
    if travel==-1:
        await update.message.reply_text("Нужен другой транспорт для "+wdata[0]+"!\nКупи в Гараже",reply_markup=MENU)
        return

    u["fishing"]=True
    save(d)

    if travel>0:
        mins=travel//60
        await update.message.reply_text("🚗 Едешь к "+wdata[0]+"...\nВремя: "+str(mins)+" мин",reply_markup=MENU)
        await asyncio.sleep(travel)

    wait=random.randint(10,60)
    msg=await update.message.reply_text(
        "🎣 Закидываешь удочку...\n"
        "〰〰〰〰〰〰〰\n"
        "Ждешь поклева...",
        reply_markup=MENU
    )
    await asyncio.sleep(wait)

    d=gu(uid)
    u=d[uid]
    bn=get_bonus(u)
    caught=random.randint(1,100)<=50+bn//2

    if caught:
        pool=[]
        for fid in wdata[1]:
            pool+=[fid]*FISH[fid]["rare"]
        fid=random.choice(pool)
        fish=FISH[fid]
        weight=round(fish["weight"]*random.uniform(0.8,1.3),1)
        price=fish_price(fid,weight)
        u["fish"][fid]=u["fish"].get(fid,0)+1
        u["total_caught"]=u.get("total_caught",0)+1
        oldlv=lvl(u["exp"])
        u["exp"]+=fish["exp"]
        newlv=lvl(u["exp"])
        result=(
            "ПОКЛЕВ!\n\n"
            "Поймал "+fish["name"]+"!\n"
            "Вес: "+str(weight)+" кг\n"
            "Цена: ~$"+str(price)+"\n"
            "+"+str(fish["exp"])+" опыта"
        )
        if newlv>oldlv:
            result+="\n\nУРОВЕНЬ "+str(newlv)+"! "+LNAMES[newlv-1]
    else:
        result="💨 Сорвалась..."

    if u["casts"]==0: u["last"]=now
    u["casts"]+=1
    u["fishing"]=False
    save(d)
    try:
        await msg.edit_text(
            "🎣 Удочка заброшена\n"
            "〰〰〰〰〰〰〰\n\n"
            +result+"\n\n"
            "Забросов: "+str(10-u["casts"])+"/10"
        )
    except:
        await update.message.reply_text(result,reply_markup=MENU)

async def do_inv(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    if not u["fish"] or sum(u["fish"].values())==0:
        await update.message.reply_text("🎒 Пусто! Нажми Рыбачить",reply_markup=MENU)
        return
    st=STORAGE[u["storage"]]
    total=sum(u["fish"].values())
    t="🎒 Рыба ("+str(total)+"/"+str(st[2])+"):\n\n"
    for fid,cnt in u["fish"].items():
        if cnt>0 and fid in FISH:
            f=FISH[fid]
            t+=f["name"]+" x"+str(cnt)+" ("+str(f["weight"])+"кг)\n"
    await update.message.reply_text(t,reply_markup=MENU)

async def do_sell(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    if not u["fish"] or sum(u["fish"].values())==0:
        await update.message.reply_text("Нечего продавать!",reply_markup=MENU)
        return
    total=0
    t="🏪 Продано:\n\n"
    for fid,cnt in u["fish"].items():
        if cnt>0 and fid in FISH:
            f=FISH[fid]
            price=fish_price(fid,f["weight"])*cnt
            total+=price
            t+=f["name"]+" x"+str(cnt)+" = $"+str(price)+"\n"
    u["fish"]={}
    u["usd"]+=total
    save(d)
    await update.message.reply_text(t+"\n+$"+str(total),reply_markup=MENU)

async def do_bal(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    lv=lvl(u["exp"])
    await update.message.reply_text(
        "💰 Баланс\n\n"
        "💵 $"+str(int(u["usd"]))+"\n"
        "Уровень: "+str(lv)+" - "+LNAMES[lv-1]+"\n"
        "Водоем: "+WATERS[u["water"]][0]+"\n"
        "Транспорт: "+VEHICLES[u["vehicle"]][0],
        reply_markup=MENU
    )

async def do_profile(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    lv=lvl(u["exp"])
    ne=LEVELS[min(lv,9)]
    total=u.get("total_caught",0)
    await update.message.reply_text(
        "📊 Профиль\n\n"
        "Уровень "+str(lv)+" - "+LNAMES[lv-1]+"\n"
        "Опыт: "+str(u["exp"])+"/"+str(ne)+"\n"
        "💵 $"+str(int(u["usd"]))+"\n"
        "Рыб поймано: "+str(total)+"\n"
        "Водоем: "+WATERS[u["water"]][0]+"\n"
        "Транспорт: "+VEHICLES[u["vehicle"]][0],
        reply_markup=MENU
    )

async def do_rates(update,ctx):
    t="💹 Курс рыб:\n\n"
    for fid,f in FISH.items():
        price=random.randint(f["price"][0],f["price"][1])
        t+=f["name"]+" "+str(f["weight"])+"кг = $"+str(price)+"\n"
    await update.message.reply_text(t,reply_markup=MENU)

async def do_water(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    lv=lvl(u["exp"])
    rows=[]
    for wid,wdata in WATERS.items():
        cur="✅ " if u["water"]==wid else ""
        travel=can_go(u,wid)
        if lv<wdata[2]:
            lock="🔒 Ур."+str(wdata[2])+" "
        elif travel==-1:
            lock="🔒 Нужен транспорт "
        elif travel==0:
            lock=""
        else:
            lock="⏱"+str(travel//60)+"мин "
        rows.append([InlineKeyboardButton(cur+lock+wdata[0],callback_data="w_"+wid)])
    await update.message.reply_text(
        "🌊 Водоемы\nУровень: "+str(lv)+"\nТранспорт: "+VEHICLES[u["vehicle"]][0],
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def do_shop(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    rows=[
        [InlineKeyboardButton("🎣 Удочки",callback_data="s_rod")],
        [InlineKeyboardButton("🧵 Леска",callback_data="s_line")],
        [InlineKeyboardButton("🪱 Наживка",callback_data="s_bait")],
        [InlineKeyboardButton("📦 Хранилище",callback_data="s_storage")],
    ]
    await update.message.reply_text("🛒 Магазин\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))

async def do_garage(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    rows=[]
    for vid,vdata in VEHICLES.items():
        if vid=="none": continue
        cur="✅ " if u["vehicle"]==vid else ""
        rows.append([InlineKeyboardButton(cur+vdata[0]+" | $"+str(vdata[1]),callback_data="v_"+vid)])
    await update.message.reply_text(
        "🚗 Гараж\nСейчас: "+VEHICLES[u["vehicle"]][0]+"\n💵 $"+str(int(u["usd"])),
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def do_quest(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    total=u.get("total_caught",0)
    t="📜 Квесты\n\n"
    t+="🐟 Поймай 10 рыб: "+str(min(total,10))+"/10"
    t+=" ✅\n" if total>=10 else "\n"
    t+="💵 Накопи $500: "+str(min(int(u["usd"]),500))+"/500"
    t+=" ✅\n" if u["usd"]>=500 else "\n"
    t+="⭐ Набери 500 опыта: "+str(min(u["exp"],500))+"/500"
    t+=" ✅\n" if u["exp"]>=500 else "\n"
    t+="🚗 Купи транспорт: "
    t+="1/1 ✅\n" if u["vehicle"]!="none" else "0/1\n"
    t+="🌊 Доберись до реки: "
    t+="1/1 ✅\n" if u["water"] in ["river","sea","ocean"] else "0/1\n"
    await update.message.reply_text(t,reply_markup=MENU)

async def txt(update,ctx):
    text=update.message.text
    if text=="🎣 Рыбачить": await do_fish(update,ctx)
    elif text=="🎒 Инвентарь": await do_inv(update,ctx)
    elif text=="🏪 Продать": await do_sell(update,ctx)
    elif text=="💰 Баланс": await do_bal(update,ctx)
    elif text=="🛒 Магазин": await do_shop(update,ctx)
    elif text=="🌊 Водоемы": await do_water(update,ctx)
    elif text=="🚗 Гараж": await do_garage(update,ctx)
    elif text=="📜 Квесты": await do_quest(update,ctx)
    elif text=="📊 Профиль": await do_profile(update,ctx)
    elif text=="💹 Курс рыб": await do_rates(update,ctx)

async def btn(update,ctx):
    q=update.callback_query
    await q.answer()
    uid=str(q.from_user.id)
    d=gu(uid)
    u=d[uid]
    cb=q.data

    if cb.startswith("w_"):
        wid=cb[2:]
        wdata=WATERS[wid]
        lv=lvl(u["exp"])
        if lv<wdata[2]:
            await q.answer("Нужен уровень "+str(wdata[2])+"!",show_alert=True); return
        travel=can_go(u,wid)
        if travel==-1:
            await q.answer("Нужен другой транспорт!",show_alert=True); return
        u["water"]=wid
        save(d)
        await q.edit_message_text("✅ Водоем: "+wdata[0])
        return

    if cb.startswith("v_"):
        vid=cb[2:]
        v=VEHICLES[vid]
        if u["vehicle"]==vid:
            await q.answer("Уже есть!",show_alert=True); return
        if u["usd"]<v[1]:
            await q.answer("Нужно $"+str(v[1]),show_alert=True); return
        u["usd"]-=v[1]
        u["vehicle"]=vid
        save(d)
        await q.edit_message_text("✅ Куплен: "+v[0]+"\n💵 Остаток: $"+str(int(u["usd"])))
        return

    if cb in ["s_rod","s_line","s_bait","s_storage"]:
        cat=cb[2:]
        items={"rod":RODS,"line":LINES,"bait":BAITS,"storage":STORAGE}[cat]
        rows=[]
        for iid,idata in items.items():
            cur="✅ " if u[cat]==iid else ""
            extra=" +"+str(idata[2])+"%" if cat!="storage" else " "+str(idata[2])+"рыб"
            rows.append([InlineKeyboardButton(cur+idata[0]+" $"+str(idata[1])+extra,callback_data="b_"+cat+"_"+iid)])
        rows.append([InlineKeyboardButton("Назад",callback_data="back")])
        await q.edit_message_text("Выбери:\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))
        return

    if cb.startswith("b_"):
        parts=cb.split("_")
        cat=parts[1]
        iid=parts[2]
        items={"rod":RODS,"line":LINES,"bait":BAITS,"storage":STORAGE}[cat]
        item=items[iid]
        if u[cat]==iid: await q.answer("Уже есть!",show_alert=True); return
        if u["usd"]<item[1]: await q.answer("Нужно $"+str(item[1]),show_alert=True); return
        u["usd"]-=item[1]
        u[cat]=iid
        save(d)
        await q.answer(item[0]+" куплено!",show_alert=True)
        return

    if cb=="back":
        rows=[
            [InlineKeyboardButton("🎣 Удочки",callback_data="s_rod")],
            [InlineKeyboardButton("🧵 Леска",callback_data="s_line")],
            [InlineKeyboardButton("🪱 Наживка",callback_data="s_bait")],
            [InlineKeyboardButton("📦 Хранилище",callback_data="s_storage")],
        ]
        await q.edit_message_text("🛒 Магазин\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))

app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("fish",do_fish))
app.add_handler(CommandHandler("inv",do_inv))
app.add_handler(CommandHandler("sell",do_sell))
app.add_handler(CommandHandler("bal",do_bal))
app.add_handler(CommandHandler("profile",do_profile))
app.add_handler(CommandHandler("shop",do_shop))
app.add_handler(CommandHandler("water",do_water))
app.add_handler(CommandHandler("garage",do_garage))
app.add_handler(CommandHandler("rates",do_rates))
app.add_handler(CommandHandler("quest",do_quest))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,txt))
print("Bot started!")
app.run_polling()
