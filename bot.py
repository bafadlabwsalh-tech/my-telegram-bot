import os, json, requests, random
from flask import Flask, request, render_template_string, redirect

token = os.getenv("TELEGRAM_BOT_TOKEN", "8774876285:AAG0y7EbKYBsKT3yjYFNb2vPOpfAglNnD3U")
OWNER = int(os.getenv("ADMIN_ID", "8584398384"))
WEBHOOK_URL = "https://my-telegram-bot-main-ee5be57.kuberns.cloud"

app = Flask(__name__)
DB_FILE = "db.json"

def load_db():
    try: return json.load(open(DB_FILE,"r",encoding="utf-8"))
    except: return {"users":{},"banned":[],"numbers":[]}
def save_db(d):
    try: json.dump(d, open(DB_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    except: pass
db = load_db()

def tg(m,d):
    try: return requests.post(f"https://api.telegram.org/bot{token}/{m}", json=d, timeout=10).json()
    except: return {}

COUNTRIES={
"YE":"🇾🇪 اليمن","SA":"🇸🇦 السعودية","EG":"🇪🇬 مصر","US":"🇺🇸 امريكا",
"AE":"🇦🇪 الامارات","TR":"🇹🇷 تركيا","RU":"🇷🇺 روسيا","GB":"🇬🇧 بريطانيا",
"DE":"🇩🇪 المانيا","FR":"🇫🇷 فرنسا","IN":"🇮🇳 الهند","PK":"🇵🇰 باكستان"
}
SITES=["WhatsApp","Telegram","Facebook","TikTok","Instagram","Google","YouTube","Twitter","Discord","Snapchat","Uber","PayPal","Netflix"]

# لوحة التحكم
ADMIN_HTML = """
<html dir=rtl><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>لوحة التحكم</title>
<style>body{background:#0f172a;color:#fff;font-family:sans-serif;padding:15px}.card{background:#1e293b;padding:15px;border-radius:12px;margin:10px 0}button,input{padding:8px 12px;border-radius:8px;border:0}button{background:#2563eb;color:#fff}table{width:100%;border-collapse:collapse}td,th{border:1px solid #334155;padding:6px;text-align:center}</style>
</head><body>
<h2>🎛️ لوحة تحكم بوت الارقام</h2>
<div class=card><h3>📢 ارسال اشعار</h3><form method=POST action=/admin/broadcast><input name=msg style="width:70%"><button>ارسال للكل</button></form></div>
<div class=card><h3>👥 المستخدمين {{users|length}}</h3>
<table><tr><th>ID</th><th>رصيد</th><th>شحن</th><th>حظر</th></tr>
{% for uid,u in users.items() %}<tr><td>{{uid}}</td><td>{{u.get('balance',0)}} ₽</td>
<td><form method=POST action=/admin/charge><input type=hidden name=uid value={{uid}}><input name=amount type=number style="width:70px"><button>شحن</button></form></td>
<td><form method=POST action=/admin/ban><input type=hidden name=uid value={{uid}}><button style="background:{{'green' if uid in banned else 'red'}}">{{'فك' if uid in banned else 'حظر'}}</button></form></td></tr>{% endfor %}</table></div>
<div class=card><h3>📦 الطلبات {{numbers|length}}</h3>
<table><tr><th>المستخدم</th><th>الدولة</th><th>الموقع</th><th>الرقم</th></tr>
{% for n in numbers[-20:] %}<tr><td>{{n['user']}}</td><td>{{n['country']}}</td><td>{{n['site']}}</td><td>{{n['number']}}</td></tr>{% endfor %}</table>
</div>
</body></html>
"""

@app.route("/")
def home(): return "OK"
@app.route("/admin")
def admin_panel(): return render_template_string(ADMIN_HTML, users=db["users"], banned=db["banned"], numbers=db.get("numbers",[]))

@app.route("/admin/charge", methods=["POST"])
def charge():
    uid=request.form["uid"]; amount=int(request.form["amount"] or 0)
    if uid not in db["users"]: db["users"][uid]={"balance":0}
    db["users"][uid]["balance"]=db["users"][uid].get("balance",0)+amount; save_db(db)
    tg("sendMessage", {"chat_id":uid, "text":f"✅ تم شحن {amount} ₽\nرصيدك: {db['users'][uid]['balance']} ₽"})
    return redirect("/admin")

@app.route("/admin/ban", methods=["POST"])
def ban_user():
    uid=request.form["uid"]
    if uid in db["banned"]: db["banned"].remove(uid)
    else: db["banned"].append(uid)
    save_db(db); return redirect("/admin")

@app.route("/admin/broadcast", methods=["POST"])
def broadcast():
    msg=request.form["msg"]
    for uid in db["users"]:
        try: tg("sendMessage", {"chat_id":uid, "text":f"📢 من الادارة:\n\n{msg}"})
        except: pass
    return redirect("/admin")

def main_kb():
    return {"keyboard":[["🛒 شراء رقم","💰 رصيدي"]], "resize_keyboard":True}

@app.route(f"/webhook/{token}", methods=["POST"])
def webhook():
    data=request.get_json()
    if not data: return "ok"

    # ازرار inline
    if "callback_query" in data:
        cq=data["callback_query"]; chat_id=cq["message"]["chat"]["id"]; uid=str(chat_id); cdata=cq["data"]
        if cdata.startswith("country_"):
            country=cdata.split("_")[1]
            # عرض المواقع
            kb={"inline_keyboard": [[{"text":s, "callback_data":f"site_{country}_{s}"}] for s in SITES[:10]]}
            tg("editMessageText", {"chat_id":chat_id, "message_id":cq["message"]["message_id"], "text":f"اخترت {COUNTRIES.get(country,country)}\n\nالان اختر الموقع:", "reply_markup":kb})
        elif cdata.startswith("site_"):
            _,country,site=cdata.split("_",2)
            price=15 # سعر ثابت
            bal=db["users"].get(uid,{}).get("balance",0)
            if bal < price:
                tg("answerCallbackQuery", {"callback_query_id":cq["id"], "text":f"رصيدك لا يكفي! تحتاج {price} ₽", "show_alert":True})
                return "ok"
            # خصم وشراء
            db["users"][uid]["balance"]-=price
            num=f"+{random.randint(1000000000,9999999999)}"
            db.setdefault("numbers",[]).append({"user":uid,"country":country,"site":site,"number":num})
            save_db(db)
            tg("editMessageText", {"chat_id":chat_id, "message_id":cq["message"]["message_id"], "text":f"✅ تم شراء الرقم!\n\n🌍 الدولة: {COUNTRIES.get(country,country)}\n📱 الموقع: {site}\n📞 الرقم: `{num}`\n💰 السعر: {price} ₽\n\nانتظر الكود...", "parse_mode":"Markdown"})
        tg("answerCallbackQuery", {"callback_query_id":cq["id"]})
        return "ok"

    if "message" not in data: return "ok"
    msg=data["message"]; chat_id=msg["chat"]["id"]; text=msg.get("text",""); uid=str(chat_id)

    if uid in db["banned"]: tg("sendMessage", {"chat_id":chat_id, "text":"⛔ محظور"}); return "ok"
    if uid not in db["users"]: db["users"][uid]={"balance":0,"name":msg["from"].get("first_name","")}; save_db(db)

    if text=="/start":
        bal=db["users"][uid].get("balance",0)
        tg("sendMessage", {"chat_id":chat_id, "text":f"مرحبا! بوت ارقام 500 موقع\n💰 رصيدك: {bal} ₽\n\nاضغط 🛒 شراء رقم", "reply_markup":main_kb()})
    elif text=="💰 رصيدي":
        bal=db["users"][uid].get("balance",0)
        tg("sendMessage", {"chat_id":chat_id, "text":f"💰 رصيدك: {bal} ₽\n\nللشحن تواصل مع الادمن"})
    elif text=="🛒 شراء رقم":
        kb={"inline_keyboard": [[{"text":f"{name}", "callback_data":f"country_{code}"}] for code,name in list(COUNTRIES.items())[:8]]}
        tg("sendMessage", {"chat_id":chat_id, "text":"🌍 اختر الدولة:", "reply_markup":kb})
    elif text=="/admin" and chat_id==OWNER:
        tg("sendMessage", {"chat_id":chat_id, "text":f"🎛️ لوحة التحكم:\n{WEBHOOK_URL}/admin"})
    elif text.startswith("/charge") and chat_id==OWNER:
        try:
            _,tid,amt=text.split()
            if tid not in db["users"]: db["users"][tid]={"balance":0}
            db["users"][tid]["balance"]+=int(amt); save_db(db)
            tg("sendMessage", {"chat_id":tid, "text":f"✅ تم شحنك {amt} ₽"}); tg("sendMessage", {"chat_id":chat_id, "text":"تم ✅"})
        except: pass

    return "ok"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
