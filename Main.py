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
# MONGODB CONFIG
# ==============================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["efootball_bot"]

users_collection = db["users"]
market_collection = db["market"]

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
# STORAGE
# ==============================
manual_ratings = {}
today_market = {}
admin_state = {}
all_users = set()

# ==============================
# LOAD DATA FROM MONGO
# ==============================
for user in users_collection.find():
    all_users.add(user["_id"])

market_data = market_collection.find_one({"_id": "today"})
if market_data:
    today_market = market_data

# ==============================
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id

    # SAVE USER
    users_collection.update_one(
        {"_id": chat_id},
        {"$set": {"user_id": chat_id}},
        upsert=True
    )

    all_users.add(chat_id)

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
        KeyboardButton("📊 Stats"),
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

    if text == "📈 Shaxda Suuqa Maanta":
        if 'photo_file_id' in today_market:
            rating = today_market.get('rating', '?')
            price = today_market.get('price', '?')
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {rating}\n💰 Qiimaha: ${price}\n\n📢 Ka iibso shaxo iyo Coins 👇\n{WHATSAPP_LINK}"
            bot.send_photo(chat_id, today_market['photo_file_id'], caption=caption)
        else:
            bot.send_message(chat_id, "❌ Shaxda suuqa maanta wali lama dhigin.")
        return

    elif text == "🛠️ Admin Panel":
        if not user_is_admin:
            bot.send_message(chat_id, "❌ Ma aadan ahayn admin.")
            return
        admin_panel_buttons(chat_id)
        admin_state[chat_id] = None
        return

    if user_is_admin:
        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "📸 Soo dir sawirka:")
            admin_state[chat_id] = 'add_new'
            return

        elif text == "Delete Shaxda Maanta":
            today_market.clear()
            market_collection.delete_one({"_id": "today"})
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

        elif text == "Broadcast Fariin":
            bot.send_message(chat_id, "📢 Soo dir fariin:")
            admin_state[chat_id] = 'broadcast'
            return

        elif text == "📊 Stats":
            bot.send_message(chat_id, f"Users: {len(all_users)}")
            return

# ==============================
# PHOTO HANDLER
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    state = admin_state.get(chat_id)

    if state == 'add_new':
        today_market['photo_file_id'] = message.photo[-1].file_id
        bot.send_message(chat_id, "Qor Rating iyo Price: 3150 25")
        admin_state[chat_id] = 'awaiting_rating_price'
        return

    if state == 'broadcast' and chat_id == ADMIN_ID:
        for user_id in all_users:
            try:
                bot.send_photo(user_id, message.photo[-1].file_id)
            except:
                pass
        bot.send_message(chat_id, "✅ Broadcast done")
        admin_state[chat_id] = None
        return

    bot.reply_to(message, "Qor rating:")
    manual_ratings[chat_id] = True

# ==============================
# VIDEO HANDLER
# ==============================
@bot.message_handler(content_types=['video'])
def handle_video(message):
    if message.chat.id == ADMIN_ID and admin_state.get(message.chat.id) == 'broadcast':
        for user_id in all_users:
            try:
                bot.send_video(user_id, message.video.file_id)
            except:
                pass
        bot.send_message(message.chat.id, "✅ Video sent")
        admin_state[message.chat.id] = None

# ==============================
# ADMIN RATING + PRICE
# ==============================
@bot.message_handler(func=lambda m: admin_state.get(m.chat.id) == 'awaiting_rating_price')
def handle_admin_rating_price(msg):
    try:
        rating, price = map(float, msg.text.split())
        today_market['rating'] = int(rating)
        today_market['price'] = price

        # SAVE TO MONGO
        market_collection.update_one(
            {"_id": "today"},
            {"$set": today_market},
            upsert=True
        )

        bot.send_message(msg.chat.id, "✅ Saved")
        admin_state[msg.chat.id] = None
    except:
        bot.send_message(msg.chat.id, "❌ Error")

# ==============================
# BROADCAST TEXT
# ==============================
@bot.message_handler(func=lambda m: admin_state.get(m.chat.id) == 'broadcast')
def handle_broadcast_text(msg):
    if msg.chat.id == ADMIN_ID:
        for user_id in all_users:
            try:
                bot.send_message(user_id, msg.text)
            except:
                pass
        bot.send_message(msg.chat.id, "✅ Sent")
        admin_state[msg.chat.id] = None

# ==============================
# RUN
# ==============================
print("Bot is running...")
bot.infinity_polling()
