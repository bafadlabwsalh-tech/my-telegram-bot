import os, json, requests, random
from flask import Flask, request, render_template_string, redirect

# --- من متغيرات Kuberns ---
token = os.getenv("TELEGRAM_BOT_TOKEN", "8774876285:AAG0y7EbKYBsKT3yjYFNb2vPOpfAglNnD3U")
OWNER = int(os.getenv("ADMIN_ID", "8584398384"))
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_URL = os.getenv("KUBERNS_URL", "").rstrip("/")

ch1="-1003912977510"
ch3="-1004349325097"
ch4="-1004396829597"
API_KEY=token

app = Flask(__name__)
DB_FILE = "db.json"

def load_db():
    try:
        return json.load(open(DB_FILE, "r", encoding="utf-8"))
    except:
        return {"users": {}, "banned": [], "numbers": []}

def save_db(d):
    json.dump(d, open(DB_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

db = load_db()

def bot(m, d={}):
    try:
        return requests.post(f"https://api.telegram.org/bot{API_KEY}/{m}", data=d, timeout=15).json()
    except:
        return {}

COUNTRIES={"AF":"🇦🇫 افغانستان","AL":"🇦🇱 البانيا","DZ":"🇩🇿 الجزائر","US":"🇺🇸 امريكا","SA":"🇸🇦 السعودية","YE":"🇾🇪 اليمن","EG":"🇪🇬 مصر","AE":"🇦🇪 الامارات","TR":"🇹🇷 تركيا","DE":"🇩🇪 المانيا","GB":"🇬🇧 بريطانيا","RU":"🇷🇺 روسيا","IN":"🇮🇳 الهند","ID":"🇮🇩 اندونيسيا","PK":"🇵🇰 باكستان","FR":"🇫🇷 فرنسا","IT":"🇮🇹 ايطاليا","BR":"🇧🇷 البرازيل","CA":"🇨🇦 كندا","AU":"🇦🇺 استراليا"}
SITES=["WhatsApp","Telegram","Facebook","TikTok","Instagram","Google","YouTube","Twitter","Discord","Snapchat","Uber","Bolt","PayPal","Amazon","Netflix","IMO","Viber","Line","WeChat","Tinder"]*25 # 500 موقع

# --- لوحة التحكم الويب اللي طلبتها ---
ADMIN_HTML = """
<html dir=rtl><head><meta charset=utf-8><title>لوحة بوت الارقام</title>
<style>body{background:#0f172a;color:#fff;font-family:sans-serif;padding:20px}.card{background:#1e293b;padding:15px;border-radius:12px;margin:10px 0}button,input{padding:8px;border-radius:8px;border:0}button{background:#2563eb;color:#fff;cursor:pointer}table{width:100%;border-collapse:collapse}td,th{border:1px solid #334155;padding:6px}</style>
</head><body>
<h1>🎛️ لوحة تحكم بوت الارقام</h1>
<div class=card><h3>📢 ارسال اشعار في البوت</h3><form method=POST action=/admin/broadcast><input name=msg style="width:70%" placeholder="نص الاشعار"><button>ارسال للكل</button></form></div>
<div class=card><h3>👥 المستخدمين: {{users|length}}</h3><table><tr><th>ID</th><th>الرصيد ₽</th><th>شحن روبل</th><th>حظر</th></tr>
{% for uid, u in users.items() %}
<tr><td>{{uid}}</td><td>{{u.get('balance',0)}} ₽</td>
<td><form method=POST action=/admin/charge><input type=hidden name=uid value={{uid}}><input name=amount type=number placeholder="مبلغ"><button>شحن</button></form></td>
<td><form method=POST action=/admin/ban><input type=hidden name=uid value={{uid}}><button style="background:{{'green' if uid in banned else 'red'}}">{{'فك' if uid in banned else 'حظر'}}</button></form></td></tr>
{% endfor %}</table></div>
</body></html>
"""

@app.route("/")
def home(): return "Bot Running ✅"

@app.route("/admin")
def admin_panel():
    return render_template_string(ADMIN_HTML, users=db["users"], banned=db["banned"])

@app.route("/admin/charge", methods=["POST"])
def charge():
    uid = request.form["uid"]; amount = int(request.form["amount"])
    if uid not in db["users"]: db["users"][uid] = {"balance":0}
    db["users"][uid]["balance"] = db["users"][uid].get("balance",0) + amount
    save_db(db)
    bot("sendMessage", {"chat_id": uid, "text": f"✅ تم شحن رصيدك {amount} ₽\nرصيدك الحالي: {db['users'][uid]['balance']} ₽"})
    return redirect("/admin")

@app.route("/admin/ban", methods=["POST"])
def ban_user():
    uid = request.form["uid"]
    if uid in db["banned"]: db["banned"].remove(uid)
    else: db["banned"].append(uid)
    save_db(db)
    return redirect("/admin")

@app.route("/admin/broadcast", methods=["POST"])
def broadcast():
    msg = request.form["msg"]
    for uid in db["users"]:
        bot("sendMessage", {"chat_id": uid, "text": f"📢 اشعار من الادارة:\n\n{msg}"})
    return redirect("/admin")

# --- استقبال رسائل تليجرام ---
@app.route(f"/webhook/{token}", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "message" not in data: return "ok"
    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text","")
    uid = str(chat_id)

    if uid in db["banned"]:
        bot("sendMessage", {"chat_id": chat_id, "text": "⛔️ انت محظور"})
        return "ok"

    if uid not in db["users"]:
        db["users"][uid] = {"balance": 0, "name": msg["from"].get("first_name","")}
        save_db(db)

    if text == "/start":
        bot("sendMessage", {"chat_id": chat_id, "text": f"مرحبا! بوت ارقام 500 موقع\nرصيدك: {db['users'][uid].get('balance',0)} ₽\n\nاستخدم /admin لو انت الادمن"})

    elif text.startswith("/charge") and chat_id == OWNER:
        # /charge ID مبلغ
        try:
            _, tid, amt = text.split()
            if tid not in db["users"]: db["users"][tid] = {"balance":0}
            db["users"][tid]["balance"] += int(amt)
            save_db(db)
            bot("sendMessage", {"chat_id": tid, "text": f"✅ تم شحنك {amt} ₽"})
            bot("sendMessage", {"chat_id": chat_id, "text": "تم الشحن"})
        except: bot("sendMessage", {"chat_id": chat_id, "text": "الاستخدام: /charge ID مبلغ"})

    elif text.startswith("/ban") and chat_id == OWNER:
        try:
            _, tid = text.split()
            if tid in db["banned"]: db["banned"].remove(tid)
            else: db["banned"].append(tid)
            save_db(db)
            bot("sendMessage", {"chat_id": chat_id, "text": f"تم تحديث حظر {tid}"})
        except: pass

    return "ok"

if __name__ == "__main__":
    # ضبط webhook تلقائيا
    if WEBHOOK_URL:
        requests.get(f"https://api.telegram.org/bot{token}/setWebhook?url={WEBHOOK_URL}/webhook/{token}")
    app.run(host="0.0.0.0", port=PORT)
