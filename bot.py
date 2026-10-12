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
    for ch in CHANNELS:
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getChatMember?chat_id={ch}&user_id={user_id}", timeout=5).json()
            status = r.get("result",{}).get("status","left")
            if status in ["left","kicked"]: return False
        except: return False
    return True

def main_kb(): return {"keyboard":[["🛒 شراء رقم","💰 رصيدي"]], "resize_keyboard":True}
def sub_kb():
    buttons=[]
    for i, link in enumerate(CHANNEL_LINKS): buttons.append([{"text":f"📢 اشترك {i+1}","url":link}])
    buttons.append([{"text":"✅ تحقق","callback_data":"check_sub"}])
    return {"inline_keyboard":buttons}
def admin_kb():
    return {"inline_keyboard":[[{"text":"👥 المستخدمين","callback_data":"adm_users"},{"text":"📊 احصائيات","callback_data":"adm_stats"}],[{"text":"📢 اذاعة","callback_data":"adm_broadcast"},{"text":"💰 شحن","callback_data":"adm_charge"}]]}

@app.route("/")
def home(): return "OK"

@app.route(f"/webhook/{token}", methods=["POST"])
def webhook():
    data=request.get_json()
    if not data: return "ok"

    if "callback_query" in data:
        cq=data["callback_query"]; chat_id=cq["message"]["chat"]["id"]; mid=cq["message"]["message_id"]; cdata=cq["data"]
        if cdata=="check_sub":
            if check_sub(chat_id):
                tg("editMessageText", {"chat_id":chat_id,"message_id":mid,"text":"✅ تم التحقق"})
                tg("sendMessage", {"chat_id":chat_id,"text":f"مرحبا في بوت الرقام 👋\n💰 رصيدك: {db['users'].get(str(chat_id),{}).get('balance',0)} ₽","reply_markup":main_kb()})
            else: tg("answerCallbackQuery", {"callback_query_id":cq["id"],"text":"❌ ما اشتركت","show_alert":True})
        tg("answerCallbackQuery", {"callback_query_id":cq["id"]}); return "ok"

    if "message" not in data: return "ok"
    msg=data["message"]; chat_id=msg["chat"]["id"]; text=msg.get("text","") or ""; uid=str(chat_id)
    if uid not in db["users"]: db["users"][uid]={"balance":0}; save_db(db)

    # امر /id الجديد
    if text=="/id" or text.lower()=="id":
        tg("sendMessage", {"chat_id":chat_id,"text":f"🆔 ID حقك: {chat_id}"})
        return "ok"

    if chat_id!=OWNER and not check_sub(chat_id):
        tg("sendMessage", {"chat_id":chat_id,"text":"⚠️ اشترك في القنوات اولا 👇","reply_markup":sub_kb()}); return "ok"

    if text=="/start":
        bal=db["users"][uid].get("balance",0)
        # هنا غيرتها زي ما طلبت
        tg("sendMessage", {"chat_id":chat_id,"text":f"مرحبا في بوت الرقام 👋\n\n💰 رصيدك: {bal} ₽\n\nاختر من القائمة 👇","reply_markup":main_kb()})

    elif text=="/admin" and chat_id==OWNER:
        tg("sendMessage", {"chat_id":chat_id,"text":f"🎛️ لوحة التحكم\n👥 {len(db['users'])}","reply_markup":admin_kb()})

    elif text=="💰 رصيدي":
        tg("sendMessage", {"chat_id":chat_id,"text":f"💰 رصيدك: {db['users'][uid].get('balance',0)} ₽"})
    elif text=="🛒 شراء رقم":
        kb={"inline_keyboard":[[{"text":"🇾🇪 اليمن","callback_data":"c_YE"},{"text":"🇸🇦 السعودية","callback_data":"c_SA"}]]}
        tg("sendMessage", {"chat_id":chat_id,"text":"🌍 اختر الدولة:","reply_markup":kb})
    return "ok"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
