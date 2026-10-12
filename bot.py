import os, json, requests, random
from flask import Flask, request

token = os.getenv("TELEGRAM_BOT_TOKEN", "8774876285:AAG0y7EbKYBsKT3yjYFNb2vPOpfAglNnD3U")
OWNER = int(os.getenv("ADMIN_ID", "8584398384"))
CHANNELS = ["-1003912977510", "-1004349325097", "-1004396829597"]
CHANNEL_LINKS = ["https://t.me/+your1", "https://t.me/+your2", "https://t.me/+your3"]

app = Flask(__name__)
DB_FILE="db.json"
def load_db():
    try: return json.load(open(DB_FILE,"r",encoding="utf-8"))
    except: return {"users":{},"banned":[],"numbers":[],"states":{}}
def save_db(d): json.dump(d, open(DB_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
db=load_db()
if "states" not in db: db["states"]={}

def tg(m,d):
    try: return requests.post(f"https://api.telegram.org/bot{token}/{m}", json=d, timeout=10).json()
    except: return {}

def check_sub(user_id):
    if user_id==OWNER: return True
    for ch in CHANNELS:
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getChatMember?chat_id={ch}&user_id={user_id}", timeout=5).json()
            if r.get("result",{}).get("status","left") in ["left","kicked"]: return False
        except: return False
    return True

# ===== هنا اسعارك - تقدر تغيرها =====
SERVICES = {
    "whatsapp": {"name":"WhatsApp 🟢", "price": 25, "code":"whatsapp"},
    "telegram": {"name":"Telegram 🔵", "price": 20, "code":"telegram"},
    "facebook": {"name":"Facebook 🔵", "price": 15, "code":"facebook"},
    "tiktok": {"name":"TikTok ⚫", "price": 15, "code":"tiktok"},
    "instagram": {"name":"Instagram 🟣", "price": 15, "code":"instagram"},
    "google": {"name":"Google 🔴", "price": 18, "code":"google"},
    "discord": {"name":"Discord 🟣", "price": 12, "code":"discord"},
    "uber": {"name":"Uber ⚫", "price": 18, "code":"uber"},
}

COUNTRIES = {
    "YE": {"name":"🇾🇪 اليمن", "price_plus": 0},
    "SA": {"name":"🇸🇦 السعودية", "price_plus": 10},
    "EG": {"name":"🇪🇬 مصر", "price_plus": 5},
    "US": {"name":"🇺🇸 امريكا", "price_plus": 5},
    "GB": {"name":"🇬🇧 بريطانيا", "price_plus": 15},
    "RU": {"name":"🇷🇺 روسيا", "price_plus": 0},
}

def main_kb(): return {"keyboard":[["🛒 شراء رقم","💰 رصيدي"],["📦 ارقامي","🆔 ايدي"]], "resize_keyboard":True}
def sub_kb():
    b=[]
    for i, link in enumerate(CHANNEL_LINKS): b.append([{"text":f"📢 اشترك {i+1}","url":link}])
    b.append([{"text":"✅ تحقق","callback_data":"check_sub"}])
    return {"inline_keyboard":b}
def services_kb():
    rows=[]
    for key, s in SERVICES.items():
        rows.append([{"text":f"{s['name']} - {s['price']} ₽", "callback_data":f"svc_{key}"}])
    return {"inline_keyboard":rows}
def countries_kb(svc_key):
    rows=[]
    for code, c in COUNTRIES.items():
        total = SERVICES[svc_key]["price"] + c["price_plus"]
        rows.append([{"text":f"{c['name']} - {total} ₽", "callback_data":f"buy_{svc_key}_{code}"}])
    rows.append([{"text":"⬅️ رجوع","callback_data":"back_services"}])
    return {"inline_keyboard":rows}

@app.route("/")
def home(): return "OK"

@app.route(f"/webhook/{token}", methods=["POST"])
def webhook():
    data=request.get_json()
    if not data: return "ok"

    if "callback_query" in data:
        cq=data["callback_query"]; chat_id=cq["message"]["chat"]["id"]; mid=cq["message"]["message_id"]; cdata=cq["data"]; uid=str(chat_id)
        if cdata=="check_sub":
            if check_sub(chat_id):
                tg("editMessageText", {"chat_id":chat_id,"message_id":mid,"text":"✅ تم التحقق"})
                tg("sendMessage", {"chat_id":chat_id,"text":f"مرحبا في بوت الرقام 👋\n💰 رصيدك: {db['users'].get(uid,{}).get('balance',0)} ₽","reply_markup":main_kb()})
            else: tg("answerCallbackQuery", {"callback_query_id":cq["id"],"text":"❌ ما اشتركت","show_alert":True})
            tg("answerCallbackQuery", {"callback_query_id":cq["id"]}); return "ok"

        if cdata.startswith("svc_"):
            svc=cdata.split("_")[1]
            tg("editMessageText", {"chat_id":chat_id,"message_id":mid,"text":f"اخترت {SERVICES[svc]['name']}\n\nالان اختر الدولة 🌍:","reply_markup":countries_kb(svc)})

        elif cdata=="back_services":
            tg("editMessageText", {"chat_id":chat_id,"message_id":mid,"text":"🛒 اختر التطبيق اللي تبي رقم له:","reply_markup":services_kb()})

        elif cdata.startswith("buy_"):
            _, svc, country = cdata.split("_")
            total = SERVICES[svc]["price"] + COUNTRIES[country]["price_plus"]
            bal=db["users"].get(uid,{}).get("balance",0)
            if bal < total:
                tg("answerCallbackQuery", {"callback_query_id":cq["id"],"text":f"❌ رصيدك {bal} ₽ - تحتاج {total} ₽","show_alert":True}); return "ok"
            # هنا تربط API حق الارقام الحقيقي - الحين نعطي رقم وهمي للتجربة
            db["users"][uid]["balance"]-=total
            number=f"+{random.randint(1000000000,99999999999)}"
            db.setdefault("numbers",[]).append({"user":uid,"service":svc,"country":country,"number":number,"price":total})
            save_db(db)
            tg("editMessageText", {"chat_id":chat_id,"message_id":mid,"text":f"✅ تم شراء الرقم بنجاح!\n\n📱 التطبيق: {SERVICES[svc]['name']}\n🌍 الدولة: {COUNTRIES[country]['name']}\n📞 الرقم: `{number}`\n💰 السعر: {total} ₽\n\nانتظر الكود...","parse_mode":"Markdown"})

        tg("answerCallbackQuery", {"callback_query_id":cq["id"]}); return "ok"

    if "message" not in data: return "ok"
    msg=data["message"]; chat_id=msg["chat"]["id"]; text=msg.get("text","") or ""; uid=str(chat_id)
    if uid not in db["users"]: db["users"][uid]={"balance":0}; save_db(db)

    if text in ["/id","id","🆔 ايدي","/myid"]:
        tg("sendMessage", {"chat_id":chat_id,"text":f"🆔 ID حقك: {chat_id}"}); return "ok"

    if text=="/admin":
        if chat_id==OWNER: tg("sendMessage", {"chat_id":chat_id,"text":f"🎛️ لوحة تحكم\n👥 {len(db['users'])}"})
        else: tg("sendMessage", {"chat_id":chat_id,"text":f"ID حقك: {chat_id} - انت مو ادمن"}); return "ok"

    if chat_id!=OWNER and not check_sub(chat_id):
        tg("sendMessage", {"chat_id":chat_id,"text":"⚠️ اشترك اولا 👇","reply_markup":sub_kb()}); return "ok"

    if text=="/start":
        bal=db["users"][uid].get("balance",0)
        tg("sendMessage", {"chat_id":chat_id,"text":f"مرحبا في بوت الرقام 👋\n\n🤖 نوفر ارقام وهمية لـ:\n🟢 واتساب\n🔵 تليجرام\n🔵 فيسبوك، تيك توك، انستا وغيرها\n\n💰 رصيدك: {bal} ₽\n\nاختر من القائمة 👇","reply_markup":main_kb()})
    elif text=="💰 رصيدي":
        tg("sendMessage", {"chat_id":chat_id,"text":f"💰 رصيدك: {db['users'][uid].get('balance',0)} ₽\n\nللشحن تواصل: @username"})
    elif text=="🛒 شراء رقم":
        tg("sendMessage", {"chat_id":chat_id,"text":"🛒 اختر التطبيق اللي تبي رقم له:","reply_markup":services_kb()})
    elif text=="📦 ارقامي":
        nums=[n for n in db.get("numbers",[]) if n["user"]==uid][-5:]
        if not nums: tg("sendMessage", {"chat_id":chat_id,"text":"📭 ما عندك ارقام"})
        else:
            t="📦 اخر ارقامك:\n\n"
            for n in nums: t+=f"{SERVICES[n['service']]['name']} | {COUNTRIES[n['country']]['name']} | {n['number']}\n"
            tg("sendMessage", {"chat_id":chat_id,"text":t})
    return "ok"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
