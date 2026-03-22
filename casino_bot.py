import os,json,time,random,asyncio
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder,CommandHandler,CallbackQueryHandler,MessageHandler,filters,ContextTypes

TOKEN=os.environ.get("TOKEN")
DATA="users.json"

FISH={
    "karas":  {"name":"Карась",   "weight":0.5, "price":[20,50],    "exp":5,  "rare":40},
    "okun":   {"name":"Окунь",    "weight":0.8, "price":[80,150],   "exp":10, "rare":30},
    "leshch": {"name":"Лещ",      "weight":1.5, "price":[100,200],  "exp":15, "rare":20},
    "shchuka":{"name":"Щука",     "weight":3.0, "price":[300,600],  "exp":30, "rare":7},
    "som":    {"name":"Сом",      "weight":8.0, "price":[500,1000], "exp":50, "rare":2},
    "osetr":  {"name":"Осётр",    "weight":15.0,"price":[2000,5000],"exp":100,"rare":1},
}

RODS={"wood":["Деревянная",0,0],"steel":["Стальная",500,15],"carbon":["Карбоновая",2000,30],"gold":["Золотая",10000,50]}
LINES={"basic":["Обычная",0,0],"nylon":["Нейлоновая",200,10],"braid":["Плетёная",2000,25]}
BAITS={"worm":["Червь",10,0],"maggot":["Опарыш",50,10],"shrimp":["Креветка",300,25],"caviar":["Икра",1000,45]}
STORAGE={"bucket":["Ведро",0,5],"box":["Ящик",300,20],"fridge":["Холодильник",1500,50],"freezer":["Морозильник",8000,150]}

VEHICLES={
    "none":  ["Пешком",    0,     {"pond":0,"river":1800,"sea":-1,"ocean":-1}],
    "bike":  ["Велосипед", 200,   {"pond":0,"river":900, "sea":-1,"ocean":-1}],
    "vaz":   ["Жигули",    3000,  {"pond":0,"river":300, "sea":-1,"ocean":-1}],
    "suv":   ["Внедорожник",15000,{"pond":0,"river":0,   "sea":-1,"ocean":-1}],
    "barge": ["Баржа",     40000, {"pond":0,"river":0,   "sea":1200,"ocean":-1}],
    "yacht": ["Яхта",      120000,{"pond":0,"river":0,   "sea":0,  "ocean":1800}],
}

WATERS={
    "pond":  ["Пруд",  0,  ["karas","okun","leshch"]],
    "river": ["Река",  0,  ["okun","leshch","shchuka"]],
    "sea":   ["Море",  0,  ["shchuka","som","osetr"]],
    "ocean": ["Океан", 0,  ["som","osetr"]],
}

LEVELS=[0,500,1500,3500,7000,15000,30000,60000,120000,250000]
LNAMES=["Новичок","Рыбак","Опытный","Умелый","Мастер","Эксперт","Профи","Легенда","Морской волк","Великий рыбак"]

def db():
    try:
        with open(DATA) as f: return json.load(f)
    except: return {}

def save(d):
    with open(DATA,"w") as f: json.dump(d,f,ensure_ascii=False)

def gu(uid):
    d=db()
    if uid not in d:
        d[uid]={"usd":500.0,"exp":0,"fish":{},"casts":0,"last":0,"rod":"wood","line":"basic","bait":"worm","water":"pond","storage":"bucket","vehicle":"none","fishing":False}
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
    v=VEHICLES[u["vehicle"]]
    t=v[2].get(water,-1)
    return t

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
        "Команды:\n"
        "/fish или рыбачить\n"
        "/inv или инвентарь\n"
        "/sell или продать\n"
        "/bal или баланс\n"
        "/profile или профиль\n"
        "/shop или магазин\n"
        "/water или водоемы\n"
        "/garage или гараж\n"
        "/rates или курс рыб\n"
        "/quest или квесты\n\n"
        "Старт: $500 Удачи!"
    )

async def do_fish(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]

    if u.get("fishing"):
        await update.message.reply_text("Ты уже рыбачишь! Подожди результата")
        return

    now=time.time()
    if u["casts"]>=10:
        el=now-u["last"]
        if el<1800:
            mins=int((1800-el)/60)
            await update.message.reply_text("Устал! Отдохни "+str(mins)+" мин")
            return
        u["casts"]=0

    st=STORAGE[u["storage"]]
    total=sum(u["fish"].values())
    if total>=st[2]:
        await update.message.reply_text("Хранилище полное! /sell рыбу")
        return

    water=u["water"]
    travel=can_go(u,water)
    if travel==-1:
        vname=VEHICLES[u["vehicle"]][0]
        await update.message.reply_text(
            "Не можешь добраться до "+WATERS[water][0]+"!\n"
            "Текущий транспорт: "+vname+"\n"
            "Для моря нужна Баржа\n"
            "Для океана нужна Яхта"
        )
        return

    u["fishing"]=True
    save(d)

    if travel>0:
        mins=travel//60
        await update.message.reply_text(
            "🚗 Едешь к "+WATERS[water][0]+"...\n"
            "Время в пути: "+str(mins)+" мин\n"
            "Подожди!"
        )
        await asyncio.sleep(travel)

    wait=random.randint(10,60)
    msg=await update.message.reply_text(
        "🎣 Закидываешь удочку...\n"
        "〰〰〰〰〰〰〰\n"
        "Ждёшь поклёва..."
    )

    await asyncio.sleep(wait)

    d=gu(uid)
    u=d[uid]
    bn=get_bonus(u)
    caught=random.randint(1,100)<=50+bn//2

    if caught:
        fw=WATERS[water][2]
        pool=[]
        for fid in fw:
            pool+=[fid]*FISH[fid]["rare"]
        fid=random.choice(pool)
        fish=FISH[fid]
        weight=round(fish["weight"]*random.uniform(0.8,1.3),1)
        price=fish_price(fid,weight)
        u["fish"][fid]=u["fish"].get(fid,0)+1
        oldlv=lvl(u["exp"])
        u["exp"]+=fish["exp"]
        newlv=lvl(u["exp"])
        result=(
            "ПОКЛЁВ! Тянешь...\n\n"
            "Поймал "+fish["name"]+"!\n"
            "Вес: "+str(weight)+" кг\n"
            "Цена: ~$"+str(price)+"\n"
            "Опыт: +"+str(fish["exp"])
        )
        if newlv>oldlv:
            result+="\n\nУРОВЕНЬ "+str(newlv)+"! "+LNAMES[newlv-1]
    else:
        result="Сорвалась! Не повезло..."

    if u["casts"]==0: u["last"]=now
    u["casts"]+=1
    u["fishing"]=False
    save(d)

    try:
        await msg.edit_text(
            "🎣 Закидываешь удочку...\n"
            "〰〰〰〰〰〰〰\n\n"
            +result+"\n\n"
            "Забросов: "+str(10-u["casts"])+"/10"
        )
    except:
        await update.message.reply_text(result+"\n\nЗабросов: "+str(10-u["casts"])+"/10")

async def do_inv(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    if not u["fish"]:
        await update.message.reply_text("Пусто! /fish")
        return
    st=STORAGE[u["storage"]]
    total=sum(u["fish"].values())
    t="Рыба ("+str(total)+"/"+str(st[2])+"):\n\n"
    for fid,cnt in u["fish"].items():
        if fid in FISH:
            f=FISH[fid]
            t+=f["name"]+" x"+str(cnt)+" ("+str(f["weight"])+"кг)\n"
    await update.message.reply_text(t)

async def do_sell(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    if not u["fish"]:
        await update.message.reply_text("Нечего продавать!")
        return
    total=0
    t="Продано:\n\n"
    for fid,cnt in u["fish"].items():
        if fid in FISH:
            f=FISH[fid]
            price=fish_price(fid,f["weight"])*cnt
            total+=price
            t+=f["name"]+" x"+str(cnt)+" = $"+str(price)+"\n"
    u["fish"]={}
    u["usd"]+=total
    save(d)
    await update.message.reply_text(t+"\n+$"+str(total)+"\nБаланс: $"+str(int(u["usd"])))

async def do_bal(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    lv=lvl(u["exp"])
    await update.message.reply_text(
        "Баланс\n\n"
        "💵 $"+str(int(u["usd"]))+"\n"
        "Уровень: "+str(lv)+" "+LNAMES[lv-1]+"\n"
        "Водоем: "+WATERS[u["water"]][0]+"\n"
        "Транспорт: "+VEHICLES[u["vehicle"]][0]+"\n"
        "Удочка: "+RODS[u["rod"]][0]+"\n"
        "Наживка: "+BAITS[u["bait"]][0]
    )

async def do_profile(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    lv=lvl(u["exp"])
    total=sum(u["fish"].values())
    ne=LEVELS[min(lv,9)]
    await update.message.reply_text(
        "Профиль\n\n"
        "Уровень "+str(lv)+" - "+LNAMES[lv-1]+"\n"
        "Опыт: "+str(u["exp"])+"/"+str(ne)+"\n"
        "💵 $"+str(int(u["usd"]))+"\n"
        "Рыб поймано: "+str(total)+"\n"
        "Водоем: "+WATERS[u["water"]][0]+"\n"
        "Транспорт: "+VEHICLES[u["vehicle"]][0]
    )

async def do_rates(update,ctx):
    t="Курс рыб сейчас:\n\n"
    for fid,f in FISH.items():
        price=random.randint(f["price"][0],f["price"][1])
        t+=f["name"]+" ("+str(f["weight"])+"кг) - $"+str(price)+"\n"
    await update.message.reply_text(t)

async def do_water(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    rows=[]
    for wid,wdata in WATERS.items():
        cur="✅ " if u["water"]==wid else ""
        travel=can_go(u,wid)
        if travel==-1:
            lock="🔒 "
        elif travel==0:
            lock=""
        else:
            lock="⏱"+str(travel//60)+"мин "
        rows.append([InlineKeyboardButton(cur+lock+wdata[0],callback_data="w_"+wid)])
    await update.message.reply_text(
        "Водоемы:\n"
        "Транспорт: "+VEHICLES[u["vehicle"]][0],
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def do_shop(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    rows=[
        [InlineKeyboardButton("Удочки",callback_data="s_rod")],
        [InlineKeyboardButton("Леска",callback_data="s_line")],
        [InlineKeyboardButton("Наживка",callback_data="s_bait")],
        [InlineKeyboardButton("Хранилище",callback_data="s_storage")],
    ]
    await update.message.reply_text("Магазин\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))

async def do_garage(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    rows=[]
    for vid,vdata in VEHICLES.items():
        if vid=="none": continue
        cur="✅ " if u["vehicle"]==vid else ""
        rows.append([InlineKeyboardButton(cur+vdata[0]+" | $"+str(vdata[1]),callback_data="v_"+vid)])
    cur_v=VEHICLES[u["vehicle"]][0]
    await update.message.reply_text(
        "Гараж\n"
        "Сейчас: "+cur_v+"\n"
        "💵 $"+str(int(u["usd"]))+"\n\n"
        "Купи технику:",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def do_quest(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    total=sum(u["fish"].values())
    q1="✅" if total>=5 else "⬜"
    q2="✅" if u["usd"]>=1000 else "⬜"
    q3="✅" if u["exp"]>=500 else "⬜"
    q4="✅" if u["vehicle"]!="none" else "⬜"
    await update.message.reply_text(
        "Квесты\n\n"
        +q1+" Поймай 5 рыб - +$200\n"
        +q2+" Накопи $1000 - +$300\n"
        +q3+" 500 опыта - +$500\n"
        +q4+" Купи транспорт - +$400"
    )

async def txt(update,ctx):
    text=update.message.text.lower().strip()
    cmds={
        "рыбачить":do_fish,"рыбалка":do_fish,
        "инвентарь":do_inv,"рыба":do_inv,
        "продать":do_sell,"базар":do_sell,
        "баланс":do_bal,"balance":do_bal,
        "профиль":do_profile,
        "магазин":do_shop,"shop":do_shop,
        "водоемы":do_water,"водоём":do_water,
        "гараж":do_garage,"garage":do_garage,
        "курс":do_rates,"rates":do_rates,
        "квесты":do_quest,"quest":do_quest,
    }
    if text in cmds:
        await cmds[text](update,ctx)

async def btn(update,ctx):
    q=update.callback_query
    await q.answer()
    uid=str(q.from_user.id)
    d=gu(uid)
    u=d[uid]
    cb=q.data

    if cb.startswith("w_"):
        wid=cb[2:]
        travel=can_go(u,wid)
        if travel==-1:
            await q.answer("Нужен другой транспорт!",show_alert=True)
            return
        u["water"]=wid
        save(d)
        await q.edit_message_text("Теперь рыбачишь: "+WATERS[wid][0])
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
        await q.answer(v[0]+" куплен!",show_alert=True)
        await q.edit_message_text("Куплен: "+v[0]+"\n💵 Остаток: $"+str(int(u["usd"])))
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
        if u["usd"]<item[1]: await q.answer("Нужно $"+str(item[1])+"!",show_alert=True); return
        u["usd"]-=item[1]
        u[cat]=iid
        save(d)
        await q.answer(item[0]+" куплено!",show_alert=True)
        return

    if cb=="back":
        rows=[
            [InlineKeyboardButton("Удочки",callback_data="s_rod")],
            [InlineKeyboardButton("Леска",callback_data="s_line")],
            [InlineKeyboardButton("Наживка",callback_data="s_bait")],
            [InlineKeyboardButton("Хранилище",callback_data="s_storage")],
        ]
        await q.edit_message_text("Магазин\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))

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
