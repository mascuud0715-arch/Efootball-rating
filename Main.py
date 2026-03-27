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
# PRICE SYSTEM (Live calculation)
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

def add_user(chat_id):
    users_col.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

def get_all_users():
    return [u['chat_id'] for u in users_col.find()]

# ==============================
# START
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    add_user(chat_id)
    is_admin = (msg.from_user.id == ADMIN_ID)
    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")
    main_menu_buttons(chat_id, is_admin)

# ==============================
# MAIN MENU
# ==============================
def main_menu_buttons(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📈 Shaxda Suuqa Maanta"))
    if is_admin:
        markup.add(KeyboardButton("🛠️ Admin Panel"))
    bot.send_message(chat_id, "Riix button-ka hoose:", reply_markup=markup)

# ==============================
# ADMIN PANEL
# ==============================
def admin_panel_buttons(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("Gali Shax Cusub"),
        KeyboardButton("Delete Shaxda Maanta"),
        KeyboardButton("Broadcast Fariin"),
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

    if text == "📈 Shaxda Suuqa Maanta":
        today = get_today_market()
        if today:
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {today['rating']}\n💰 Qiimaha: ${today['price']}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(chat_id, today['photo_file_id'], caption=caption)
        else:
            bot.send_message(chat_id, "❌ Shaxda suuqa maanta wali lama dhigin. Fadlan sug.")
        return

    if text == "🛠️ Admin Panel" and user_is_admin:
        admin_panel_buttons(chat_id)
        set_admin_state(chat_id, None)
        return

    if user_is_admin:
        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka shaxda cusub:")
            set_admin_state(chat_id, 'awaiting_photo')
            return
        elif text == "Delete Shaxda Maanta":
            reset_today_market()
            bot.send_message(chat_id, "✅ Shaxda suuqa maanta waa la tirtiray.")
            admin_panel_buttons(chat_id)
            return
        elif text == "Broadcast Fariin":
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
            set_admin_state(chat_id, None)
            return

# ==============================
# PHOTO HANDLER (Admin + Broadcast + User live)
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    state = get_admin_state(chat_id)
    user_is_admin = (message.from_user.id == ADMIN_ID)

    if user_is_admin:
        if state == 'awaiting_photo':
            photo_id = message.photo[-1].file_id
            set_admin_temp(chat_id, 'photo_file_id', photo_id)
            set_admin_state(chat_id, 'awaiting_rating')
            bot.send_message(chat_id, "📊 Fadlan qor **Rating** shaxda (tusaale: 3160):")
            return
        elif state == 'broadcast':
            for user_id in get_all_users():
                bot.send_photo(user_id, message.photo[-1].file_id)
            bot.send_message(chat_id, "✅ Broadcast photo waa la diray dhammaan users-ka.")
            set_admin_state(chat_id, None)
            return

    # User sending photo for live rating simulation
    price = random.randint(5, 50)  # example live price
    bot.send_message(chat_id, f"📸 Sawirka waa la helay!\n\n📊 Rating: {random.randint(3100, 3300)}\n💰 Qiimaha: ${price}")

# ==============================
# ADMIN RATING + PRICE HANDLER
# ==============================
@bot.message_handler(func=lambda m: get_admin_state(m.chat.id) in ['awaiting_rating', 'awaiting_price'])
def handle_rating_price(msg):
    chat_id = msg.chat.id
    state = get_admin_state(chat_id)
    user_is_admin = (msg.from_user.id == ADMIN_ID)
    if not user_is_admin:
        return

    if state == 'awaiting_rating':
        try:
            rating = int(msg.text)
            set_admin_temp(chat_id, 'rating', rating)
            set_admin_state(chat_id, 'awaiting_price')
            bot.send_message(chat_id, "💰 Fadlan qor **Price** shaxda (tusaale: 30):")
        except:
            bot.send_message(chat_id, "❌ Fadlan qor number sax ah oo rating-ka ah.")
    elif state == 'awaiting_price':
        try:
            price = float(msg.text)
            photo_id = get_admin_temp(chat_id, 'photo_file_id')
            rating = get_admin_temp(chat_id, 'rating')
            if not photo_id or not rating:
                bot.send_message(chat_id, "❌ Wax sawir ama rating lama hayo. Fadlan dib u soo dir.")
                set_admin_state(chat_id, 'awaiting_photo')
                return
            set_today_market({
                "today": True,
                "photo_file_id": photo_id,
                "rating": rating,
                "price": price
            })
            bot.send_message(chat_id, f"✅ Shaxda suuqa maanta waa la keydiyay!\n📊 Rating: {rating}\n💰 Qiimaha: ${price}")
            admin_panel_buttons(chat_id)
            set_admin_state(chat_id, None)
            set_admin_temp(chat_id, 'photo_file_id', None)
            set_admin_temp(chat_id, 'rating', None)
        except:
            bot.send_message(chat_id, "❌ Fadlan qor number sax ah oo price ah.")

# ==============================
# BROADCAST TEXT/PHOTO/VIDEO
# ==============================
@bot.message_handler(func=lambda m: get_admin_state(m.chat.id) == 'broadcast')
def handle_broadcast(msg):
    chat_id = msg.chat.id
    user_is_admin = (msg.from_user.id == ADMIN_ID)
    if not user_is_admin:
        return

    if msg.content_type == 'text':
        for user_id in get_all_users():
            bot.send_message(user_id, msg.text)
        bot.send_message(chat_id, "✅ Broadcast text waa la diray dhammaan users-ka.")
        set_admin_state(chat_id, None)
    elif msg.content_type == 'photo':
        for user_id in get_all_users():
            bot.send_photo(user_id, msg.photo[-1].file_id)
        bot.send_message(chat_id, "✅ Broadcast photo waa la diray dhammaan users-ka.")
        set_admin_state(chat_id, None)
    elif msg.content_type == 'video':
        for user_id in get_all_users():
            bot.send_video(user_id, msg.video.file_id)
        bot.send_message(chat_id, "✅ Broadcast video waa la diray dhammaan users-ka.")
        set_admin_state(chat_id, None)

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
