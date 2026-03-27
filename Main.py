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
    return 0

# ==============================
# USER SYSTEM
# ==============================
def add_user(chat_id, username=None):
    user = users_col.find_one({"chat_id": chat_id})
    if not user:
        users_col.insert_one({
            "chat_id": chat_id,
            "username": username,
            "ref": random.randint(10000, 99999),
            "invited": 0,
            "date": datetime.utcnow().date().isoformat()
        })

def get_user(chat_id):
    return users_col.find_one({"chat_id": chat_id})

# ==============================
# FREE SHAX
# ==============================
def set_free(photo, rating):
    free_col.delete_many({})
    free_col.insert_one({"photo": photo, "rating": rating})

def get_free():
    return free_col.find_one()

def delete_free():
    free_col.delete_many({})

# ==============================
# MARKET
# ==============================
def set_market(photo, rating, price):
    market_col.delete_many({})
    market_col.insert_one({
        "photo": photo,
        "rating": rating,
        "price": price
    })

def get_market():
    return market_col.find_one()

# ==============================
# HELPERS
# ==============================
def get_total_users():
    return users_col.count_documents({})

def get_today_users():
    today = datetime.utcnow().date().isoformat()
    return users_col.count_documents({"date": today})

def get_all_users():
    return [u['chat_id'] for u in users_col.find()]

# ==============================
# START
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    username = msg.from_user.username
    is_admin = (msg.from_user.id == ADMIN_ID)

    add_user(chat_id, username)
    user = get_user(chat_id)

    args = msg.text.split()

    # referral system
    if len(args) > 1:
        try:
            ref = int(args[1])
            owner = users_col.find_one({"ref": ref})

            if owner and owner["chat_id"] != chat_id:
                users_col.update_one({"ref": ref}, {"$inc": {"invited": 1}})
                invited = owner.get("invited", 0) + 1

                if invited >= 20:
                    bot.send_message(owner["chat_id"],
                        "🎉 Waxaad gaartay 20 qof!\nLa xiriir admin si aad u hesho shaxda")
                else:
                    bot.send_message(owner["chat_id"],
                        f"👥 Waxaad keentay {invited} qof\n{20-invited} baa kaa haray 👋")
        except:
            pass

    bot.send_message(chat_id, "👋 Soo dir sawirka shaxda si loo qiimeeyo 💰")
    main_menu(chat_id, is_admin)

# ==============================
# MENUS
# ==============================
def main_menu(chat_id, is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📈 Shaxda Suuqa Maanta", "🎁 SHAXAHA FREE")

    if is_admin:
        kb.add("🛠️ Admin Panel")

    bot.send_message(chat_id, "Dooro 👇", reply_markup=kb)

def admin_panel(chat_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        "📊 Stats",
        "📈 Add Market",
        "🎁 Add Free Shax",
        "❌ Delete Free Shax",
        "🔍 Checker",
        "Broadcast Text",
        "Broadcast Photo",
        "Broadcast Video",
        "Back"
    )
    bot.send_message(chat_id, "Admin Panel", reply_markup=kb)

# ==============================
# HANDLER
# ==============================
@bot.message_handler(func=lambda m: True, content_types=['text','photo','video'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == "text" else None
    is_admin = msg.from_user.id == ADMIN_ID

    user = get_user(chat_id)
    if not user:
        add_user(chat_id)
        user = get_user(chat_id)

    # ================= ADMIN =================
    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel(chat_id)
        return

    if is_admin:

        if text == "📊 Stats":
            bot.send_message(chat_id,
                f"👥 Total: {get_total_users()}\n🆕 Today: {get_today_users()}")
            return

        if text == "🔍 Checker":
            bot.send_message(chat_id, "Gali ref:")
            admin_state[chat_id] = "check"
            return

        if text == "📈 Add Market":
            bot.send_message(chat_id, "Dir sawir:")
            admin_state[chat_id] = "market_photo"
            return

        if text == "🎁 Add Free Shax":
            bot.send_message(chat_id, "Dir sawir:")
            admin_state[chat_id] = "free_photo"
            return

        if text == "❌ Delete Free Shax":
            delete_free()
            bot.send_message(chat_id, "Deleted")
            return

    # ================= STATES =================
    state = admin_state.get(chat_id)

    # checker
    if state == "check":
        try:
            ref = int(msg.text)
            u = users_col.find_one({"ref": ref})
            if u:
                bot.send_message(chat_id,
                    f"@{u.get('username')} - {u.get('invited',0)} users")
            else:
                bot.send_message(chat_id, "Not found")
        except:
            bot.send_message(chat_id, "Error")
        admin_state.pop(chat_id)
        return

    # market
    if state == "market_photo" and msg.content_type == "photo":
        admin_state["photo"] = msg.photo[-1].file_id
        admin_state[chat_id] = "market_rating"
        bot.send_message(chat_id, "Qor rating:")
        return

    if state == "market_rating":
        try:
            rating = int(msg.text)
            price = get_price(rating)
            set_market(admin_state["photo"], rating, price)
            bot.send_message(chat_id, "Market Added")
        except:
            bot.send_message(chat_id, "Error rating")
        admin_state.pop(chat_id)
        return

    # free
    if state == "free_photo" and msg.content_type == "photo":
        admin_state["photo"] = msg.photo[-1].file_id
        admin_state[chat_id] = "free_rating"
        bot.send_message(chat_id, "Qor rating:")
        return

    if state == "free_rating":
        try:
            rating = int(msg.text)
            set_free(admin_state["photo"], rating)
            bot.send_message(chat_id, "Free Added")
        except:
            bot.send_message(chat_id, "Error rating")
        admin_state.pop(chat_id)
        return

    # ================= USER =================
    if text == "📈 Shaxda Suuqa Maanta":
        data = get_market()
        if data:
            bot.send_photo(chat_id, data["photo"],
                caption=f"📊 Rating: {data['rating']}\n💰 ${data['price']}")
        else:
            bot.send_message(chat_id, "No market")
        return

    if text == "🎁 SHAXAHA FREE":
        data = get_free()
        if not data:
            bot.send_message(chat_id, "No free shax")
            return

        bot.send_photo(chat_id, data["photo"],
            caption=f"""🎁 FREE SHAX

📊 Rating: {data['rating']}

🔗 {BOT_LINK}{user['ref']}
👥 {user['invited']}/20""")
        return

    # rating system
    if msg.content_type == "photo":
        bot.send_message(chat_id, "Qor rating:")
        manual_ratings[chat_id] = True
        return

    if chat_id in manual_ratings:
        try:
            rating = int(msg.text)
            price = get_price(rating)

            bot.send_message(chat_id,
f"""🔥 QIIMEYN DHAMEYSTIRAN 🔥

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 {WHATSAPP_LINK}""")

        except:
            bot.send_message(chat_id, "Rating khaldan")

        manual_ratings.pop(chat_id)
        return

# ==============================
# RUN
# ==============================
print("Bot running...")
bot.infinity_polling()
