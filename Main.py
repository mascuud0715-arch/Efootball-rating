import telebot
from telebot.types import ReplyKeyboardMarkup
import random
import os
from pymongo import MongoClient
from datetime import datetime

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8669162116
WHATSAPP_LINK = "https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t"
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
    return random.randint(1, 5)

# ==============================
# USER SYSTEM
# ==============================
def generate_ref():
    while True:
        ref = random.randint(10000, 99999)
        if not users_col.find_one({"ref": ref}):
            return ref

def add_user(chat_id, username=None):
    if not users_col.find_one({"chat_id": chat_id}):
        users_col.insert_one({
            "chat_id": chat_id,
            "username": username,
            "ref": generate_ref(),
            "invited": 0,
            "date": datetime.utcnow().date().isoformat()
        })

def get_user(chat_id):
    return users_col.find_one({"chat_id": chat_id})

def get_all_users():
    return [u['chat_id'] for u in users_col.find()]

# ==============================
# MARKET + FREE
# ==============================
def set_free(photo, rating):
    free_col.delete_many({})
    free_col.insert_one({"photo": photo, "rating": rating})

def get_free():
    return free_col.find_one() or {}

def delete_free():
    free_col.delete_many({})

def set_market(photo, rating, price):
    market_col.delete_many({})
    market_col.insert_one({
        "photo": photo,
        "rating": rating,
        "price": price
    })

def get_market():
    return market_col.find_one() or {}

# ==============================
# MENUS
# ==============================
def main_menu(chat_id, is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📈 Shaxda Suuqa Maanta", "🎁 SHAXAHA FREE")
    if is_admin:
        kb.add("🛠️ Admin Panel")
    bot.send_message(chat_id, "Dooro option 👇", reply_markup=kb)

def admin_panel(chat_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        "📊 Stats", "🔍 Checker",
        "Gali Shax Cusub", "Delete Shaxda Maanta",
        "🎁 Add Free Shax", "❌ Delete Free Shax",
        "Broadcast Text", "Broadcast Photo", "Broadcast Video",
        "Back"
    )
    bot.send_message(chat_id, "🛠️ Admin Panel", reply_markup=kb)

# ==============================
# START
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    add_user(chat_id, msg.from_user.username)
    is_admin = msg.from_user.id == ADMIN_ID

    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")
    main_menu(chat_id, is_admin)

# ==============================
# HANDLER
# ==============================
@bot.message_handler(func=lambda m: True, content_types=['text','photo','video'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == "text" else None
    is_admin = msg.from_user.id == ADMIN_ID

    # ================= ADMIN =================
    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel(chat_id)
        return

    if is_admin:

        if text == "Back":
            main_menu(chat_id, True)
            return

        if text == "📊 Stats":
            bot.send_message(chat_id, f"Users: {users_col.count_documents({})}")
            return

        if text == "🔍 Checker":
            bot.send_message(chat_id, "Gali ref:")
            admin_state[chat_id] = "check"
            return

        if text == "Gali Shax Cusub":
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

        if text == "Delete Shaxda Maanta":
            market_col.delete_many({})
            bot.send_message(chat_id, "Deleted")
            return

        if text == "Broadcast Text":
            admin_state[chat_id] = "b_text"
            bot.send_message(chat_id, "Qor fariin:")
            return

        if text == "Broadcast Photo":
            admin_state[chat_id] = "b_photo"
            bot.send_message(chat_id, "Dir sawir:")
            return

    # ================= STATES =================
    state = admin_state.get(chat_id)

    if state == "check":
        u = users_col.find_one({"ref": int(text)})
        bot.send_message(chat_id, str(u))
        admin_state.pop(chat_id)
        return

    if state == "market_photo" and msg.content_type == "photo":
        admin_state["m_photo"] = msg.photo[-1].file_id
        admin_state[chat_id] = "market_rating"
        bot.send_message(chat_id, "Rating?")
        return

    if state == "market_rating":
        admin_state["m_rating"] = int(text)
        admin_state[chat_id] = "market_price"
        bot.send_message(chat_id, "Price?")
        return

    if state == "market_price":
        set_market(admin_state["m_photo"], admin_state["m_rating"], int(text))
        bot.send_message(chat_id, "Market added ✅")
        admin_state.pop(chat_id)
        return

    if state == "free_photo" and msg.content_type == "photo":
        admin_state["f_photo"] = msg.photo[-1].file_id
        admin_state[chat_id] = "free_rating"
        bot.send_message(chat_id, "Rating?")
        return

    if state == "free_rating":
        set_free(admin_state["f_photo"], int(text))
        bot.send_message(chat_id, "Free added ✅")
        admin_state.pop(chat_id)
        return

    if state == "b_text":
        for u in get_all_users():
            try: bot.send_message(u, text)
            except: pass
        admin_state.pop(chat_id)
        return

    if state == "b_photo" and msg.content_type == "photo":
        for u in get_all_users():
            try: bot.send_photo(u, msg.photo[-1].file_id)
            except: pass
        admin_state.pop(chat_id)
        return

    # ================= USER =================
    if text == "🎁 SHAXAHA FREE":
        data = get_free()
        if data:
            bot.send_photo(chat_id, data["photo"],
                caption=f"Rating: {data['rating']}")
        else:
            bot.send_message(chat_id, "No free shax")
        return

    if text == "📈 Shaxda Suuqa Maanta":
        data = get_market()
        if data:
            bot.send_photo(chat_id, data["photo"],
                caption=f"Rating: {data['rating']}\nPrice: ${data['price']}")
        else:
            bot.send_message(chat_id, "No market yet")
        return

    # ================= RATING =================
    if chat_id in admin_state:
        return

    if msg.content_type == "photo":
        manual_ratings[chat_id] = True
        bot.reply_to(msg, "Qor rating:")
        return

    if chat_id in manual_ratings and msg.content_type == "text":

        if not text.isdigit():
            bot.send_message(chat_id, "Number sax ah geli")
            return

        rating = int(text)
        price = get_price(rating)

        bot.send_message(chat_id,
f"""🔥 QIIMEYN 🔥

Rating: {rating}
Qiimaha: ${price}

{WHATSAPP_LINK}
""")

        manual_ratings.pop(chat_id)
        return

# ==============================
# RUN
# ==============================
print("Bot running...")
bot.infinity_polling()
