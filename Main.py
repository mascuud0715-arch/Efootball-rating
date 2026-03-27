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

# ==============================
# MONGO
# ==============================
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["bot_db"]

users_col = db["users"]
market_col = db["market"]

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
# STORAGE (Mongo)
# ==============================
manual_ratings = {}
admin_state = {}

def save_user(user_id):
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id})

def get_all_users():
    return [u["user_id"] for u in users_col.find()]

def save_market(photo, rating, price):
    market_col.delete_many({})
    market_col.insert_one({
        "photo_file_id": photo,
        "rating": rating,
        "price": price
    })

def get_market():
    return market_col.find_one()

def delete_market():
    market_col.delete_many({})

# ==============================
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    save_user(chat_id)

    is_admin = (msg.from_user.id == ADMIN_ID)
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
        KeyboardButton("Broadcast Fariin"),
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

    # --------------------------
    # MAIN MENU ACTIONS
    # --------------------------
    if text == "📈 Shaxda Suuqa Maanta":
        data = get_market()
        if data:
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {data.get('rating','?')}\n💰 Qiimaha: ${data.get('price','?')}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(chat_id, data['photo_file_id'], caption=caption)
        else:
            bot.send_message(chat_id, "❌ Shaxda suuqa maanta wali lama dhigin. Fadlan sug.")
        return

    elif text == "🛠️ Admin Panel":
        if not user_is_admin:
            bot.send_message(chat_id, "❌ Ma aadan ahayn admin.")
            return
        admin_panel_buttons(chat_id)
        admin_state[chat_id] = None
        return

    # --------------------------
    # ADMIN PANEL ACTIONS
    # --------------------------
    if user_is_admin:
        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka shaxda cusub:")
            admin_state[chat_id] = 'add_new'
            return

        elif text == "Update Shax Cusub":
            data = get_market()
            if not data:
                bot.send_message(chat_id, "❌ Shaxda maanta lama hayo, fadlan marka hore gali.")
                return
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka cusub ee shaxda maanta:")
            admin_state[chat_id] = 'update'
            return

        elif text == "Delete Shaxda Maanta":
            delete_market()
            bot.send_message(chat_id, "✅ Shaxda suuqa maanta waa la tirtiray.")
            admin_panel_buttons(chat_id)
            return

        elif text == "Broadcast Fariin":
            bot.send_message(chat_id, "📢 Fadlan soo dir fariinta broadcast (text, photo ama video):")
            admin_state[chat_id] = 'broadcast'
            return

        elif text == "Back":
            main_menu_buttons(chat_id, True)
            return

    # --------------------------
    # USER MANUAL RATING INPUT
    # --------------------------
    if chat_id in manual_ratings:
        try:
            rating = int(text)
            if rating < 3000 or rating > 3500:
                bot.reply_to(msg, "❌ Rating-ka waa inuu noqdaa 3000–3500. Dib u qor.")
                return
            price = get_price(rating)
            final_text = f"""🔥 **QIIMEYN DHAMEYSTIRAN** 🔥

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇
{WHATSAPP_LINK}"""
            bot.send_message(chat_id, final_text)
            manual_ratings.pop(chat_id)
        except:
            bot.reply_to(msg, "❌ Fadlan qoro number sax ah oo 4-digit ah.")

# ==============================
# PHOTO HANDLER
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    state = admin_state.get(chat_id)

    if state in ['add_new', 'update']:
        photo_id = message.photo[-1].file_id
        bot.send_message(chat_id, "📊 Fadlan qor **Rating iyo Qiimaha** shaxda (Tusaale: 3150 25):")
        admin_state[chat_id] = ('awaiting_rating_price', photo_id)
        return

    if state == 'broadcast' and chat_id == ADMIN_ID:
        for user_id in get_all_users():
            bot.send_photo(user_id, message.photo[-1].file_id)
        bot.send_message(chat_id, "✅ Broadcast photo waa la diray dhammaan users-ka.")
        admin_state[chat_id] = None
        return

    bot.reply_to(message, "📸 Sawirka waa la helay!\nFadlan qor **rating-ka** shaxda eFootball (tusaale: 3150):")
    manual_ratings[chat_id] = True

# ==============================
# VIDEO HANDLER
# ==============================
@bot.message_handler(content_types=['video'])
def handle_video(message):
    chat_id = message.chat.id
    if admin_state.get(chat_id) == 'broadcast' and chat_id == ADMIN_ID:
        for user_id in get_all_users():
            bot.send_video(user_id, message.video.file_id)
        bot.send_message(chat_id, "✅ Broadcast video waa la diray dhammaan users-ka.")
        admin_state[chat_id] = None

# ==============================
# HANDLE ADMIN RATING + PRICE
# ==============================
@bot.message_handler(func=lambda m: isinstance(admin_state.get(m.chat.id), tuple))
def handle_admin_rating_price(msg):
    chat_id = msg.chat.id
    state = admin_state.get(chat_id)

    try:
        photo_id = state[1]
        parts = msg.text.split()
        if len(parts) != 2:
            bot.send_message(chat_id, "❌ Fadlan qor Rating iyo Price sida: 3150 25")
            return

        rating = int(parts[0])
        price = float(parts[1])

        save_market(photo_id, rating, price)

        admin_state[chat_id] = None
        bot.send_message(chat_id, f"✅ Shaxda suuqa maanta waa la keydiyay!\n📊 Rating: {rating}\n💰 Qiimaha: ${price}")
        admin_panel_buttons(chat_id)

    except:
        bot.send_message(chat_id, "❌ Fadlan qor number sax ah oo qaab: 3150 25")

# ==============================
# BROADCAST TEXT HANDLER
# ==============================
@bot.message_handler(func=lambda m: admin_state.get(m.chat.id) == 'broadcast')
def handle_broadcast_text(msg):
    chat_id = msg.chat.id
    if chat_id == ADMIN_ID and msg.content_type == 'text':
        for user_id in get_all_users():
            bot.send_message(user_id, msg.text)
        bot.send_message(chat_id, "✅ Broadcast text waa la diray dhammaan users-ka.")
        admin_state[chat_id] = None

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
