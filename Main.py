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
    else: return None

# ==============================
# MONGO HELPERS
# ==============================
def add_user(chat_id):
    users_col.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

def get_today_market():
    return market_col.find_one({"today": True}) or {}

def set_today_market(photo_file_id, rating, price):
    market_col.update_one(
        {"today": True},
        {"$set": {"photo_file_id": photo_file_id, "rating": rating, "price": price, "today": True}},
        upsert=True
    )

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
        KeyboardButton("Stats"),
        KeyboardButton("Back")
    )
    bot.send_message(chat_id, "🛠️ Admin Panel:", reply_markup=markup)

# ==============================
# BUTTON HANDLER (TEXT/PHOTO/VIDEO)
# ==============================
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video'])
def handle_buttons(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == 'text' else None
    is_admin = (msg.from_user.id == ADMIN_ID)
    state = get_admin_state(chat_id)

    # MAIN MENU
    if text == "📈 Shaxda Suuqa Maanta":
        today = get_today_market()
        if 'photo_file_id' in today:
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {today.get('rating')}\n💰 Qiimaha: ${today.get('price')}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(chat_id, today['photo_file_id'], caption=caption)
        else:
            bot.send_message(chat_id, "❌ Shaxda suuqa maanta wali lama dhigin.")
        return

    # ADMIN PANEL
    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel_buttons(chat_id)
        set_admin_state(chat_id, None)
        return

    # ADMIN ACTIONS
    if is_admin:
        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka shaxda cusub:")
            set_admin_state(chat_id, 'add_new')
            return

        elif text == "Update Shax Cusub":
            today = get_today_market()
            if 'photo_file_id' not in today:
                bot.send_message(chat_id, "❌ Shaxda maanta lama hayo.")
                return
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka cusub:")
            set_admin_state(chat_id, 'update')
            return

        elif text == "Delete Shaxda Maanta":
            reset_today_market()
            bot.send_message(chat_id, "✅ Shaxda suuqa maanta waa la tirtiray.")
            admin_panel_buttons(chat_id)
            return

        elif text == "Broadcast":
            bot.send_message(chat_id, "📢 Fadlan soo dir **text / photo / video** broadcast-ka:")
            set_admin_state(chat_id, 'broadcast')
            return

        elif text == "Stats":
            total = users_col.count_documents({})
            bot.send_message(chat_id, f"📊 Total Users: {total}")
            return

        elif text == "Back":
            main_menu_buttons(chat_id, True)
            return

    # BROADCAST
    if state == 'broadcast':
        for u in users_col.find({}):
            try:
                if msg.content_type == 'text':
                    bot.send_message(u['chat_id'], msg.text)
                elif msg.content_type == 'photo':
                    bot.send_photo(u['chat_id'], msg.photo[-1].file_id)
                elif msg.content_type == 'video':
                    bot.send_video(u['chat_id'], msg.video.file_id)
            except: pass
        bot.send_message(chat_id, "✅ Broadcast waa la diray.")
        set_admin_state(chat_id, None)
        return

# ==============================
# HANDLE ADMIN PHOTO + RATING/PRICE
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_admin_photo(message):
    chat_id = message.chat.id
    is_admin = (message.from_user.id == ADMIN_ID)
    state = get_admin_state(chat_id)

    if is_admin and state in ['add_new', 'update']:
        photo_id = message.photo[-1].file_id
        set_admin_temp(chat_id, 'photo_file_id', photo_id)
        set_admin_state(chat_id, 'awaiting_rating_price')
        bot.send_message(chat_id, "📊 Fadlan qor **Rating iyo Qiimaha** shaxda (Tusaale: 3150 25)")

@bot.message_handler(func=lambda m: get_admin_state(m.chat.id) == 'awaiting_rating_price', content_types=['text'])
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
        set_today_market(photo_id, rating, price)
        set_admin_state(chat_id, None)
        bot.send_message(chat_id, f"✅ Shaxda suuqa maanta waa la keydiyay!\n📊 Rating: {rating}\n💰 Qiimaha: ${price}")
        admin_panel_buttons(chat_id)
    except:
        bot.send_message(chat_id, "❌ Fadlan qor number sax ah oo qaab: Rating Price (tusaale: 3150 25)")

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
