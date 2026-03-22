import os,json,time,random
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder,CommandHandler,CallbackQueryHandler,MessageHandler,filters,ContextTypes

TOKEN=os.environ.get("TOKEN")
DATA_FILE="users.json"

FISH=[
["karas","Карась","🐟",20,50,5,40],
["okun","Окунь","🐠",80,150,10,30],
["shchuka","Щука","🦈",300,600,30,20],
["som","Сом","🐬",500,1000,50,8],
["zolotaya","Золотая","👑",10000,50000,500,2],
]

SHOP={
"rod":[["wood","Деревянная",0,0],["steel","Стальная",500,15],["carbon","Карбоновая",2000,30],["gold","Золотая",10000,50]],
"line":[["basic","Обычная",0,0],["nylon","Нейлоновая",200,10],["braid","Плетёная",2000,25]],
"bait":[["worm","Червь",10,0],["maggot","Опарыш",50,10],["shrimp","Креветка",300,25]],
}

def db():
    try:
        with open(DATA_FILE) as f: return json.load(f)
    except: return {}

def save(d):
    with open(DATA_FILE,"w") as f: json.dump(d,f,ensure_ascii=False)

def gu(uid):
    d=db()
    if uid not in d:
        d[uid]={"usd":500.0,"fish":{},"casts":0,"last":0,"rod":"wood","line":"basic","bait":"worm"}
        save(d)
    return d

def bonus(u):
    rb=next((x[3] for x in SHOP["rod"] if x[0]==u["rod"]),0)
    lb=next((x[3] for x in SHOP["line"] if x[0]==u["line"]),0)
    bb=next((x[3] for x in SHOP["bait"] if x[0]==u["bait"]),0)
    return rb+lb+bb

def do_catch(u):
    if random.randint(1,100)>45+bonus(u)//2: return None
    pool=[]
    for f in FISH:
        pool+=[f]*f[6]
    return random.choice(pool)

async def start(update,ctx):
    uid=str(update.effective_user.id)
    gu(uid)
    await update.message.reply_text(
        "🎣 Привет!\n\n"
        "рыбачить - закинуть удочку\n"
        "инвентарь - моя рыба\n"
        "базар - продать рыбу\n"
        "баланс - мой счёт\n"
        "магазин - снаряжение\n\n"
        "💵 Баланс: $500"
    )

async def msg(update,ctx):
    text=update.message.text.lower().strip()
    uid=str(update.effective_user.id)
    d=gu(uid)
    u=d[uid]

    if text in ["рыбачить","рыбалка"]:
        now=time.time()
        if u["casts"]>=10:
            el=now-u["last"]
            if el<1800:
                await update.message.reply_text("😴 Отдохни "+str(int((1800-el)/60))+" мин.")
                return
            u["casts"]=0
        m=await update.message.reply_dice(emoji="🎣")
        f=do_catch(u)
        if f:
            fid=f[0]
            u["fish"][fid]=u["fish"].get(fid,0)+1
            u["casts"]+=1
            if u["casts"]==1: u["last"]=now
            save(d)
            await update.message.reply_text("🎣 "+f[2]+" "+f[1]+"!\n💰 ~$"+str(random.randint(f[3],f[4]))+"\n\nЗабросов: "+str(10-u["casts"])+"/10")
        else:
            u["casts"]+=1
            if u["casts"]==1: u["last"]=now
            save(d)
            await update.message.reply_text("💨 Сорвалась!\n\nЗабросов: "+str(10-u["casts"])+"/10")
        return

    if text in ["инвентарь","рыба"]:
        if not u["fish"]: await update.message.reply_text("🎒 Пусто!"); return
        msg_text="🎒 Рыба:\n\n"
        for fid,cnt in u["fish"].items():
            f=next((x for x in FISH if x[0]==fid),None)
            if f: msg_text+=f[2]+" "+f[1]+" x"+str(cnt)+"\n"
        await update.message.reply_text(msg_text)
        return

    if text in ["базар","продать"]:
        if not u["fish"]: await update.message.reply_text("Нечего продавать!"); return
        total=0
        msg_text="🏪 Продано:\n\n"
        for fid,cnt in u["fish"].items():
            f=next((x for x in FISH if x[0]==fid),None)
            if f:
                p=random.randint(f[3],f[4])*cnt
                total+=p
                msg_text+=f[2]+" "+f[1]+" x"+str(cnt)+" = $"+str(p)+"\n"
        u["fish"]={}
        u["usd"]+=total
        save(d)
        await update.message.reply_text(msg_text+"\n💵 +$"+str(total)+"\n💰 $"+str(int(u["usd"])))
        returnif text in ["баланс","balance"]:
        rn=next((x[1] for x in SHOP["rod"] if x[0]==u["rod"]),"")
        ln=next((x[1] for x in SHOP["line"] if x[0]==u["line"]),"")
        bn=next((x[1] for x in SHOP["bait"] if x[0]==u["bait"]),"")
        await update.message.reply_text("💼 Баланс\n\n💵 $"+str(int(u["usd"]))+"\n🎣 "+rn+"\n🧵 "+ln+"\n🪱 "+bn)
        return

    if text in ["магазин","shop"]:
        rows=[
            [InlineKeyboardButton("🎣 Удочки",callback_data="s_rod")],
            [InlineKeyboardButton("🧵 Леска",callback_data="s_line")],
            [InlineKeyboardButton("🪱 Наживка",callback_data="s_bait")],
        ]
        await update.message.reply_text("🏪 МАГАЗИН\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))
        return

async def btn(update,ctx):
    q=update.callback_query
    await q.answer()
    uid=str(q.from_user.id)
    d=gu(uid)
    u=d[uid]
    cb=q.data

    if cb in ["s_rod","s_line","s_bait"]:
        cat=cb[2:]
        items=SHOP[cat]
        cur=u[cat]
        rows=[]
        for item in items:
            mark="✅ " if item[0]==cur else ""
            rows.append([InlineKeyboardButton(mark+item[1]+" | $"+str(item[2])+" | +"+str(item[3])+"%",callback_data="b_"+cat+"_"+item[0])])
        rows.append([InlineKeyboardButton("🔙 Назад",callback_data="back")])
        await q.edit_message_text("🏪 Выбери:",reply_markup=InlineKeyboardMarkup(rows))
        return

    if cb.startswith("b_"):
        parts=cb.split("_")
        cat=parts[1]
        item_id=parts[2]
        item=next((x for x in SHOP[cat] if x[0]==item_id),None)
        if not item: return
        if u[cat]==item_id:
            await q.answer("Уже есть!",show_alert=True); return
        if u["usd"]<item[2]:
            await q.answer("Нужно $"+str(item[2])+"!",show_alert=True); return
        u["usd"]-=item[2]
        u[cat]=item_id
        save(d)
        await q.answer(item[1]+" куплено!",show_alert=True)
        return

    if cb=="back":
        rows=[
            [InlineKeyboardButton("🎣 Удочки",callback_data="s_rod")],
            [InlineKeyboardButton("🧵 Леска",callback_data="s_line")],
            [InlineKeyboardButton("🪱 Наживка",callback_data="s_bait")],
        ]
        await q.edit_message_text("🏪 МАГАЗИН\n💵 $"+str(int(u["usd"])),reply_markup=InlineKeyboardMarkup(rows))

app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,msg))
print("🎣 Бот запущен!")
app.run_polling()
