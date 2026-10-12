import os, json, requests, random
from flask import Flask, request

token = os.getenv("TELEGRAM_BOT_TOKEN", "8774876285:AAG0y7EbKYBsKT3yjYFNb2vPOpfAglNnD3U")
OWNER = int(os.getenv("ADMIN_ID", "8584398384"))

# --- هنا حط قنواتك ---
CHANNELS = ["-1003912977510", "-1004349325097", "-1004396829597"]  # ايديات قنواتك
CHANNEL_LINKS = ["https://t.me/+your1", "https://t.me/+your2", "https://t.me/+your3"]  # روابط القنوات

app = Flask(__name__)
DB_FILE = "db.json"

def load_db():
    try: return json.load(open(DB_FILE,"r",encoding="utf-8"))
    except: return {"users":{},"banned":[],"numbers":[],"states":{}}
def save_db(d):
    json.dump(d, open(DB_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
db = load_db()
if "states" not in db: db["states"] = {}

def tg(m,d):
    try: return requests.post(f"https://api.telegram.org/bot{token}/{m}", json=d, timeout=10).json()
    except: return {}

def check_sub(user_id):
    """يرجع True اذا مشترك في كل القنوات"""
    for ch in CHANNELS:
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getChatMember?chat_id={ch}&user_id={user_id}", timeout=5).json()
            status = r.get("result",{}).get("status","")
            if status in ["left","kicked","": ""]:
                return False
        except:
            return False
    return True

COUNTRIES={"YE":"🇾🇪 اليمن","SA":"🇸🇦 السعودية","EG":"🇪🇬 مصر","US":"🇺🇸 امريكا","AE":"🇦🇪 الامارات","TR":"🇹🇷 تركيا","RU":"🇷🇺 روسيا","GB":"🇬🇧 بريطانيا"}
SITES=["WhatsApp","Telegram","Facebook","TikTok","Instagram","Google","YouTube","Twitter","Discord","Snapchat","Uber","PayPal","Netflix"]

def admin_kb():
    return {"inline_keyboard":[[{"text":"👥 المستخدمين","callback_data":"adm_users"},{"text":"📊 احصائيات","callback_data":"adm_stats"}],[{"text":"📢 اذاعة","callback_data":"adm_broadcast"},{"text":"💰 شحن","callback_data":"adm_charge"}],[{"text":"🚫 حظر","callback_data":"adm_ban"},{"text":"📢 تعديل القنوات","callback_data":"adm_channels"}]]}
def main_kb():
    return {"keyboard":[["🛒 شراء رقم","💰 رصيدي"]], "resize_keyboard":True}
def sub_kb():
    buttons=[]
    for i, link in enumerate(CHANNEL_LINKS):
        buttons.append([{"text":f"📢 اشترك في القناة {i+1}","url":link}])
    buttons.append([{"text":"✅ تحقق من الاشتراك","callback_data":"check_sub"}])
    return {"inline_keyboard":buttons}

@app.route("/")
def home(): return "OK"
@app.route(f"/webhook/{token}", methods=["POST"])
def webhook():
   
