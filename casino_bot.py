import os,json,time,random
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder,CommandHandler,CallbackQueryHandler,ContextTypes

TOKEN=os.environ.get("TOKEN")
DATA="users.json"

FISH={"pond":{"Карась":[20,50,40],"Окунь":[80,150,35],"Лещ":[100,200,25]},"river":{"Окунь":[80,150,30],"Лещ":[100,200,30],"Щука":[300,600,40]},"sea":{"Щука":[300,600,30],"Сом":[500,1000,40],"Осетр":[2000,5000,30]},"ocean":{"Сом":[500,1000,20],"Осетр":[2000,5000,40],"Золотая":[10000,50000,40]}}
RODS={"wood":["Деревянная",0,0],"steel":["Стальная",500,15],"carbon":["Карбоновая",2000,30],"gold":["Золотая",10000,50]}
LINES={"basic":["Обычная",0,0],"nylon":["Нейлоновая",200,10],"braid":["Плетеная",2000,25]}
BAITS={"worm":["Червь",10,0],"maggot":["Опарыш",50,10],"shrimp":["Креветка",300,25],"caviar":["Икра",1000,45]}
WATERS={"pond":["Пруд",0],"river":["Река",1000],"sea":["Море",5000],"ocean":["Океан",20000]}
STORAGE={"bucket":["Ведро",0,5],"box":["Ящик",300,20],"fridge":["Холодильник",1500,50],"freezer":["Морозильник",8000,150]}

def db():
    try:
        with open(DATA) as f: return json.load(f)
    except: return {}

def save(d):
    with open(DATA,"w") as f: json.dump(d,f,ensure_ascii=False)

def gu(uid):
    d=db()
    if uid not in d:
        d[uid]={"usd":500.0,"exp":0,"fish":{},"casts":0,"last":0,"rod":"wood","line":"basic","bait":"worm","water":"pond","storage":"bucket"}
        save(d)
    return d

def lvl(exp):
    levels=[0,500,1500,3500,7000,15000,30000,60000,120000,250000]
    names=["Новичок","Рыбак","Опытный","Умелый","Мастер","Эксперт","Профи","Легенда","Морской волк","Великий рыбак"]
    lv=1
    for i,r in enumerate(levels):
        if exp>=r: lv=i+1
    return min(lv,10),names[min(lv,10)-1]

def bonus(u):
    return RODS[u["rod"]][2]+LINES[u["line"]][2]+BAITS[u["bait"]][2]

async def start(update,ctx):
    uid=str(update.effective_user.id)
    gu(uid)
    await update.message.reply_text(
        "🎣 Привет рыбак!\n\n"
        "/fish - рыбачить\n"
        "/inv - инвентарь\n"
        "/sell - продать рыбу\n"
        "/bal - баланс\n"
        "/profile - профиль\n"
        "/shop - магазин\n"
        "/water - водоемы\n"
        "/quest - квесты\n\n"
        "Старт: $500"
    )

async def fish(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    now=time.time()
    if u["casts"]>=10:
        el=now-u["last"]
        if el<1800:
            await update.message.reply_text("😴 Отдохни "+str(int((1800-el)/60))+" мин")
            return
        u["casts"]=0
    st=STORAGE[u["storage"]]
    total=sum(u["fish"].values())
    if total>=st[2]:
        await update.message.reply_text("📦 "+st[0]+" полное! /sell рыбу")
        return
    m=await update.message.reply_dice(emoji="🎣")
    bn=bonus(u)
    caught=m.dice.value>=4 or random.randint(1,100)<=bn//2
    if caught:
        fw=FISH[u["water"]]
        pool=[]
        for name,data in fw.items():
            pool+=[name]*data[2]
        fname=random.choice(pool)
        fdata=fw[fname]
        price=random.randint(fdata[0],fdata[1])
        u["fish"][fname]=u["fish"].get(fname,0)+1
        u["exp"]+=10
        oldlv,_=lvl(u["exp"]-10)
        newlv,newname=lvl(u["exp"])
        result="🎣 Поймал "+fname+"!\n~$"+str(price)
        if newlv>oldlv:
            result+="\n\n🎉 Уровень "+str(newlv)+"! "+newname
    else:
        result="💨 Сорвалась!"
    if u["casts"]==0: u["last"]=now
    u["casts"]+=1
    save(d)
    await update.message.reply_text(result+"\n🎣 "+str(10-u["casts"])+"/10")

async def inv(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    if not u["fish"]:
        await update.message.reply_text("🎒 Пусто! /fish")
        return
    st=STORAGE[u["storage"]]
    total=sum(u["fish"].values())
    t="🎒 Рыба ("+str(total)+"/"+str(st[2])+"):\n\n"
    for k,v in u["fish"].items():
        t+=k+" x"+str(v)+"\n"
    await update.message.reply_text(t)

async def sell(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    if not u["fish"]:
        await update.message.reply_text("Нечего продавать!")
        return
    total=0
    t="🏪 Продано:\n\n"
    allfish={}
    for w in FISH.values():
        allfish.update(w)
    for k,v in u["fish"].items():
        p=allfish.get(k,[50,100,0])
        earned=random.randint(p[0],p[1])*v
        total+=earned
        t+=k+" x"+str(v)+" = $"+str(earned)+"\n"
    u["fish"]={}
    u["usd"]+=total
    save(d)
    await update.message.reply_text(t+"\n+$"+str(total)+"\n💵 $"+str(int(u["usd"])))

async def bal(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    lv,ln=lvl(u["exp"])
    await update.message.reply_text(
        "💼 Баланс\n\n"
        "💵 $"+str(int(u["usd"]))+"\n"
        "⭐ Ур."+str(lv)+" "+ln+"\n"
        "🌊 "+WATERS[u["water"]][0]+"\n"
        "🎣 "+RODS[u["rod"]][0]+"\n"
        "🧵 "+LINES[u["line"]][0]+"\n"
        "🪱 "+BAITS[u["bait"]][0]
    )

async def profile(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    lv,ln=lvl(u["exp"])
    total=sum(u["fish"].values())
    nxt=[0,500,1500,3500,7000,15000,30000,60000,120000,250000]
    ne=nxt[min(lv,9)]
    await update.message.reply_text(
        "👤 Профиль\n\n"
        "⭐ "+str(lv)+" - "+ln+"\n"
        "📊 Опыт: "+str(u["exp"])+"/"+str(ne)+"\n"
        "💵 $"+str(int(u["usd"]))+"\n"
        "🐟 Поймано: "+str(total)+"\n"
        "🌊 "+WATERS[u["water"]][0]+"\n"
        "📦 "+STORAGE[u["storage"]][0]
    )

async def water(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    rows=[]
    for wid,wdata in WATERS.items():
        cur="✅ " if u["water"]==wid else ""
        rows.append([InlineKeyboardButton(cur+wdata[0]+" | $"+str(wdata[1]),callback_data="w_"+wid)])
    await update.message.reply_text("🌊 Водоемы:\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))

async def shop(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    rows=[
        [InlineKeyboardButton("🎣 Удочки",callback_data="s_rod")],
        [InlineKeyboardButton("🧵 Леска",callback_data="s_line")],
        [InlineKeyboardButton("🪱 Наживка",callback_data="s_bait")],
        [InlineKeyboardButton("📦 Хранилище",callback_data="s_storage")],
    ]
    await update.message.reply_text("🏪 Магазин\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))

async def quest(update,ctx):
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]
    total=sum(u["fish"].values())
    q1="✅" if total>=5 else "⬜"
    q2="✅" if u["usd"]>=1000 else "⬜"
    q3="✅" if u["casts"]>=10 else "⬜"
    q4="✅" if u["exp"]>=500 else "⬜"
    await update.message.reply_text(
        "📜 Квесты\n\n"
        +q1+" Поймай 5 рыб - +$200\n"
        +q2+" Накопи $1000 - +$300\n"
        +q3+" 10 забросов - +$100\n"
        +q4+" 500 опыта - +$500"
    )

async def btn(update,ctx):
    q=update.callback_query
    await q.answer()
    uid=str(q.from_user.id)
    d=gu(uid)
    u=d[uid]
    cb=q.data

    if cb.startswith("w_"):
        wid=cb[2:]
        wp=WATERS[wid][1]
        if u["usd"]<wp:
            await q.answer("Нужно $"+str(wp),show_alert=True); return
        if u["water"]!=wid and wp>0: u["usd"]-=wp
        u["water"]=wid
        save(d)
        await q.edit_message_text("✅ Теперь рыбачишь: "+WATERS[wid][0])
        return

    if cb in ["s_rod","s_line","s_bait","s_storage"]:
        cat=cb[2:]
        items={"rod":RODS,"line":LINES,"bait":BAITS,"storage":STORAGE}[cat]
        rows=[]
        for iid,idata in items.items():
            cur="✅ " if u[cat]==iid else ""
            bonus_text=" | +"+str(idata[2])+"%" if len(idata)>2 and cat!="storage" else " | "+str(idata[2])+" рыб" if cat=="storage" else ""
            rows.append([InlineKeyboardButton(cur+idata[0]+" | $"+str(idata[1])+bonus_text,callback_data="b_"+cat+"_"+iid)])
        rows.append([InlineKeyboardButton("🔙 Назад",callback_data="back")])
        await q.edit_message_text("Выбери:",reply_markup=InlineKeyboardMarkup(rows))
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
        await q.edit_message_text("🏪 Магазин\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))

app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("fish",fish))
app.add_handler(CommandHandler("inv",inv))
app.add_handler(CommandHandler("sell",sell))
app.add_handler(CommandHandler("bal",bal))
app.add_handler(CommandHandler("profile",profile))
app.add_handler(CommandHandler("water",water))
app.add_handler(CommandHandler("shop",shop))
app.add_handler(CommandHandler("quest",quest))
app.add_handler(CallbackQueryHandler(btn))
print("Bot started!")
app.run_polling()
    
