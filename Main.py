import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import random
import os
from pymongo import MongoClient

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

WHATSAPP_LINK = "https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t"
ADMIN_ID = int(os.getenv("ADMIN_ID"))

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['efb_bot']
users_col = db['users']
market_col = db['market']
admin_state_col = db['admin_state']

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
    else: return 0

# ==============================
# HELPER FUNCTIONS
# ==============================
def add_user(chat_id):
    users_col.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

def get_all_users():
    return [u['chat_id'] for u in users_col.find()]

def get_today_market():
    return market_col.find_one({"today": True})

def set_today_market(data):
    market_col.update_one({"today": True}, {"$set": data}, upsert=True)

def reset_today_market():
    market_col.delete_many({"today": True})

def get_admin_state(chat_id):
    doc = admin_state_col.find_one({"chat_id": chat_id})
    return doc['state'] if doc else None

def set_admin_state(chat_id, state):
    admin_state_col.update_one({"chat_id": chat_id}, {"$set": {"state": state}}, upsert=True)

def set_admin_temp(chat_id, key, value):
    admin_state_col.update_one({"chat_id": chat_id}, {"$set": {key: value}}, upsert=True)

def get_admin_temp(chat_id, key):
    doc = admin_state_col.find_one({"chat_id": chat_id})
    return doc.get(key) if doc else None

# ==============================
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    is_admin = (msg.from_user.id == ADMIN_ID)
    add_user(chat_id)
    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")
    main_menu_buttons(chat_id, is_admin)

# ==============================
# MAIN MENU BUTTONS
# ==============================
def main_menu_buttons(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📈 Shaxda Suuqa Maanta"))
    if is_admin:
        markup.add(KeyboardButton("🛠️ Admin Panel"))
    bot.send_message(chat_id, "Riix button-ka hoose:", reply_markup=markup)

# ==============================
# ADMIN PANEL BUTTONS
# ==============================
def admin_panel_buttons(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("Gali Shax Cusub"),
        KeyboardButton("Update Shax Cusub"),
        KeyboardButton("Delete Shaxda Maanta"),
        KeyboardButton("Broadcast"),
        KeyboardButton("Stats Admin"),
        KeyboardButton("Back")
    )
    bot.send_message(chat_id, "🛠️ Admin Panel:", reply_markup=markup)

# ==============================
# BUTTON HANDLER
# ==============================
@bot.message_handler(func=lambda m: True)
def handle_buttons(msg):
    chat_id = msg.chat.id
    text = msg.text
    user_is_admin = (msg.from_user.id == ADMIN_ID)
    state = get_admin_state(chat_id)

    # MAIN MENU
    if text == "📈 Shaxda Suuqa Maanta":
        today = get_today_market()
        if today:
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {today['rating']}\n💰 Qiimaha: ${today['price']}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(chat_id, today['photo_file_id'], caption=caption)
        else:
            bot.send_message(chat_id, "❌ Shaxda suuqa maanta wali lama dhigin.")
        return

    if text == "🛠️ Admin Panel" and user_is_admin:
        admin_panel_buttons(chat_id)
        set_admin_state(chat_id, None)
        return

    # ADMIN PANEL
    if user_is_admin:
        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka shaxda cusub:")
            set_admin_state(chat_id, 'awaiting_photo')
            return
        elif text == "Update Shax Cusub":
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka cusub ee shaxda maanta:")
            set_admin_state(chat_id, 'update_photo')
            return
        elif text == "Delete Shaxda Maanta":
            reset_today_market()
            bot.send_message(chat_id, "✅ Shaxda suuqa maanta waa la tirtiray.")
            admin_panel_buttons(chat_id)
            return
        elif text == "Broadcast":
            bot.send_message(chat_id, "📢 Soo dir fariinta broadcast (text, photo ama video):")
            set_admin_state(chat_id, 'broadcast')
            return
        elif text == "Stats Admin":
            total_users = users_col.count_documents({})
            bot.send_message(chat_id, f"📊 Total Users: {total_users}")
            admin_panel_buttons(chat_id)
            return
        elif text == "Back":
            main_menu_buttons(chat_id, True)
            return

# ==============================
# PHOTO HANDLER
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    user_is_admin = (message.from_user.id == ADMIN_ID)
    state = get_admin_state(chat_id)

    # ADMIN PHOTO
    if user_is_admin and state in ['awaiting_photo', 'update_photo']:
        photo_id = message.photo[-1].file_id
        set_admin_temp(chat_id, 'photo_file_id', photo_id)
        set_admin_state(chat_id, 'awaiting_rating_price')
        bot.send_message(chat_id, "📊 Fadlan qor **Rating iyo Price** shaxda (tusaale: 3150 25):")
        return

    # USER PHOTO
    bot.reply_to(message, "📸 Sawirka waa la helay!\nFadlan qor **rating-ka** shaxda eFootball (tusaale: 3150):")
    set_admin_temp(chat_id, 'manual', True)

# ==============================
# HANDLE ADMIN RATING + PRICE
# ==============================
@bot.message_handler(func=lambda m: get_admin_state(m.chat.id) == 'awaiting_rating_price')
def handle_admin_rating_price(msg):
    chat_id = msg.chat.id
    try:
        parts = msg.text.split()
        if len(parts) != 2:
            bot.send_message(chat_id, "❌ Fadlan qor Rating iyo Price sida: 3150 25")
            return
        rating = int(parts[0])
        price = float(parts[1])
        photo_id = get_admin_temp(chat_id, 'photo_file_id')
        set_today_market({
            "today": True,
            "photo_file_id": photo_id,
            "rating": rating,
            "price": price
        })
        bot.send_message(chat_id, f"✅ Shaxda suuqa maanta waa la keydiyay!\n📊 Rating: {rating}\n💰 Qiimaha: ${price}")
        admin_panel_buttons(chat_id)
        set_admin_state(chat_id, None)
    except:
        bot.send_message(chat_id, "❌ Fadlan qor number sax ah oo qaab: Rating Price (tusaale: 3150 25)")

# ==============================
# BROADCAST HANDLER
# ==============================
@bot.message_handler(func=lambda m: get_admin_state(m.chat.id) == 'broadcast')
def handle_broadcast(msg):
    chat_id = msg.chat.id
    if msg.from_user.id != ADMIN_ID:
        return

    for user_id in get_all_users():
        if msg.content_type == 'text':
            bot.send_message(user_id, msg.text)
        elif msg.content_type == 'photo':
            bot.send_photo(user_id, msg.photo[-1].file_id, caption=msg.caption)
        elif msg.content_type == 'video':
            bot.send_video(user_id, msg.video.file_id, caption=msg.caption)
    bot.send_message(chat_id, "✅ Broadcast waa la diray dhammaan users-ka.")
    set_admin_state(chat_id, None)

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
