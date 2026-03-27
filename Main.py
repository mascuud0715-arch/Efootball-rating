import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import random
import os
from pymongo import MongoClient
from datetime import datetime

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

WHATSAPP_LINK = "https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t"
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BOT_LINK = "https://t.me/Efootball_seller_bot?start="

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['efb_bot']

users_col = db['users']
market_col = db['market']
free_col = db['free']

manual_ratings = {}
admin_state = {}

# ==============================
# PRICE SYSTEM
# ==============================
def get_price(rating):
    if 3100 <= rating <= 3130: return random.randint(2, 4)
    elif 3130 < rating <= 3150: return random.randint(6, 8)
    elif 3150 < rating <= 3170: return random.randint(7, 10)
    elif 3170 < rating <= 3190: return random.randint(9, 12)
    elif 3190 < rating <= 3210: return random.randint(10, 14)
    elif 3210 < rating <= 3250: return random.randint(20, 40)
    elif 3250 < rating <= 3310: return random.randint(40, 100)
    else: return 0   # FIXED None

# ==============================
# USER SYSTEM
# ==============================
def add_user(chat_id, username=None):
    if not users_col.find_one({"chat_id": chat_id}):
        while True:
            ref_id = random.randint(10000, 99999)
            if not users_col.find_one({"ref_id": ref_id}):
                break

        users_col.insert_one({
            "chat_id": chat_id,
            "username": username,
            "ref_id": ref_id,
            "invited": 0,
            "date": datetime.utcnow().date().isoformat()
        })

def get_user(chat_id):
    return users_col.find_one({"chat_id": chat_id})

# ==============================
# FREE SHAX
# ==============================
def set_free_shax(photo, rating):
    free_col.delete_many({})
    free_col.insert_one({"photo": photo, "rating": rating})

def delete_free_shax():
    free_col.delete_many({})

def get_free_shax():
    return free_col.find_one() or {}

# ==============================
# MARKET
# ==============================
def get_today_market():
    return market_col.find_one({"today": True}) or {}

def set_today_market(photo, rating, price):
    market_col.update_one(
        {"today": True},
        {"$set": {"photo_file_id": photo, "rating": rating, "price": price, "today": True}},
        upsert=True
    )

def reset_today_market():
    market_col.delete_many({"today": True})

# ==============================
# MENUS
# ==============================
def main_menu(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📈 Shaxda Suuqa Maanta", "🎁 SHAXAHA FREE")

    if is_admin:
        markup.add("🛠️ Admin Panel")

    bot.send_message(chat_id, "Dooro option 👇", reply_markup=markup)

def admin_panel(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "📊 Stats",
        "Gali Shax Cusub",
        "Delete Shaxda Maanta",
        "🎁 Add Free Shax",
        "❌ Delete Free Shax",
        "Broadcast Text",
        "Broadcast Photo",
        "Broadcast Video",
        "🔍 Checker",
        "Back"
    )
    bot.send_message(chat_id, "🛠️ Admin Panel", reply_markup=markup)

# ==============================
# START
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    is_admin = (msg.from_user.id == ADMIN_ID)

    add_user(chat_id, msg.from_user.username)

    args = msg.text.split()

    # REFERRAL FIXED
    if len(args) > 1:
        try:
            ref = int(args[1])
            owner = users_col.find_one({"ref_id": ref})

            if owner and owner["chat_id"] != chat_id:
                users_col.update_one({"ref_id": ref}, {"$inc": {"invited": 1}})

                invited = owner.get("invited", 0) + 1

                bot.send_message(owner["chat_id"],
                    f"👥 Waxaad keentay {invited} qof")
        except:
            pass

    bot.reply_to(msg, "👋 Soo dir sawir shax ah si loo qiimeeyo 💰")
    main_menu(chat_id, is_admin)

# ==============================
# BROADCAST
# ==============================
def broadcast_all(func):
    users = users_col.find()
    for u in users:
        try:
            func(u['chat_id'])
        except:
            pass

# ==============================
# HANDLER
# ==============================
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == 'text' else None
    is_admin = (msg.from_user.id == ADMIN_ID)

    user = get_user(chat_id)

    # FREE SHAX
    if text == "🎁 SHAXAHA FREE":
        data = get_free_shax()

        if not data:
            bot.send_message(chat_id, "❌ Free shax ma jiro")
            return

        ref = user.get("ref_id")
        invited = user.get("invited", 0)

        bot.send_photo(chat_id, data['photo'],
            caption=f"📊 Rating: {data['rating']}\n👥 {invited}/20\n🔗 {BOT_LINK}{ref}")
        return

    # MARKET
    if text == "📈 Shaxda Suuqa Maanta":
        d = get_today_market()
        if d.get("photo_file_id"):
            bot.send_photo(chat_id, d['photo_file_id'],
                caption=f"📊 Rating: {d['rating']}\n💰 ${d['price']}")
        else:
            bot.send_message(chat_id, "❌ Ma jiro")
        return

    # ADMIN PANEL
    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel(chat_id)
        return

    if is_admin:

        if text == "❌ Delete Free Shax":
            delete_free_shax()
            bot.send_message(chat_id, "✅ Free shax waa la tirtiray")

        elif text == "Broadcast Text":
            admin_state[chat_id] = "bc_text"
            bot.send_message(chat_id, "Qor message:")

        elif text == "Broadcast Photo":
            admin_state[chat_id] = "bc_photo"
            bot.send_message(chat_id, "Dir sawir:")

        elif text == "Broadcast Video":
            admin_state[chat_id] = "bc_video"
            bot.send_message(chat_id, "Dir video:")

        elif text == "Back":
            main_menu(chat_id, True)

    # =============================
    # ADMIN STATES
    # =============================
    state = admin_state.get(chat_id)

    if state == "bc_text":
        broadcast_all(lambda uid: bot.send_message(uid, msg.text))
        bot.send_message(chat_id, "✅ Done")
        admin_state.pop(chat_id)

    elif state == "bc_photo" and msg.content_type == "photo":
        broadcast_all(lambda uid: bot.send_photo(uid, msg.photo[-1].file_id))
        bot.send_message(chat_id, "✅ Done")
        admin_state.pop(chat_id)

    elif state == "bc_video" and msg.content_type == "video":
        broadcast_all(lambda uid: bot.send_video(uid, msg.video.file_id))
        bot.send_message(chat_id, "✅ Done")
        admin_state.pop(chat_id)

    # =============================
    # USER FLOW (QIIMEYN NEW)
    # =============================
    if msg.content_type == 'photo':
        manual_ratings[chat_id] = True
        bot.reply_to(msg, "Qor rating:")
        return

    if chat_id in manual_ratings:
        try:
            rating = int(msg.text)
            price = get_price(rating)

            bot.send_message(chat_id, f"""🔥 **QIIMEYN DHAMEYSTIRAN** 🔥

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 Ka iibso shaxo iyo Coins 👇
{WHATSAPP_LINK}
""", parse_mode="Markdown")

            manual_ratings.pop(chat_id)
        except:
            bot.send_message(chat_id, "❌ Error")
        return

# ==============================
# RUN
# ==============================
print("Bot running...")
bot.infinity_polling()
