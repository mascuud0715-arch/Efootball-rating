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

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['efb_bot']
users_col = db['users']
market_col = db['market']

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
admin_state = {}

# ==============================
# MONGO HELPERS
# ==============================
def add_user(chat_id):
    users_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id, "date": datetime.utcnow().date().isoformat()}},
        upsert=True
    )

def get_total_users():
    return users_col.count_documents({})

def get_today_users():
    today = datetime.utcnow().date().isoformat()
    return users_col.count_documents({"date": today})

def get_all_users():
    return [u['chat_id'] for u in users_col.find()]

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

# ==============================
# START
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    is_admin = (msg.from_user.id == ADMIN_ID)

    add_user(chat_id)

    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")
    main_menu(chat_id, is_admin)

# ==============================
# MENUS
# ==============================
def main_menu(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📈 Shaxda Suuqa Maanta"))

    if is_admin:
        markup.add(KeyboardButton("🛠️ Admin Panel"))

    bot.send_message(chat_id, "Dooro option 👇", reply_markup=markup)

def admin_panel(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("📊 Stats"),
        KeyboardButton("Gali Shax Cusub"),
        KeyboardButton("Delete Shaxda Maanta"),
        KeyboardButton("Broadcast Text"),
        KeyboardButton("Broadcast Photo"),
        KeyboardButton("Broadcast Video"),
        KeyboardButton("Back")
    )
    bot.send_message(chat_id, "🛠️ Admin Panel", reply_markup=markup)

# ==============================
# HANDLER
# ==============================
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == 'text' else None
    is_admin = (msg.from_user.id == ADMIN_ID)

    # =============================
    # MAIN MENU
    # =============================
    if text == "📈 Shaxda Suuqa Maanta":
        today = get_today_market()
        if 'photo_file_id' in today:
            bot.send_photo(
                chat_id,
                today['photo_file_id'],
                caption=f"📊 Rating: {today['rating']}\n💰 Price: ${today['price']}"
            )
        else:
            bot.send_message(chat_id, "❌ Wali lama dhigin")
        return

    # =============================
    # ADMIN PANEL
    # =============================
    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel(chat_id)
        return

    if is_admin:

        if text == "📊 Stats":
            total = get_total_users()
            today = get_today_users()

            bot.send_message(chat_id,
                f"📊 STATS\n\n👥 Total Users: {total}\n🆕 Today Users: {today}")
            return

        elif text == "Gali Shax Cusub":
            bot.send_message(chat_id, "📸 Soo dir sawir")
            bot.register_next_step_handler(msg, admin_photo)
            return

        elif text == "Delete Shaxda Maanta":
            reset_today_market()
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

        elif text == "Broadcast Text":
            bot.send_message(chat_id, "Qor fariin:")
            admin_state[chat_id] = "text"
            return

        elif text == "Broadcast Photo":
            bot.send_message(chat_id, "Dir sawir:")
            admin_state[chat_id] = "photo"
            return

        elif text == "Broadcast Video":
            bot.send_message(chat_id, "Dir video:")
            admin_state[chat_id] = "video"
            return

        elif text == "Back":
            main_menu(chat_id, True)
            return

    # =============================
    # BROADCAST
    # =============================
    state = admin_state.get(chat_id)
    if state:
        users = get_all_users()

        for u in users:
            try:
                if state == "text":
                    bot.send_message(u, msg.text)
                elif state == "photo":
                    bot.send_photo(u, msg.photo[-1].file_id)
                elif state == "video":
                    bot.send_video(u, msg.video.file_id)
            except:
                pass

        bot.send_message(chat_id, "✅ Broadcast done")
        admin_state.pop(chat_id)
        return

    # =============================
    # USER FLOW
    # =============================
    if msg.content_type == 'photo':
        bot.reply_to(msg, "Qor rating:")
        manual_ratings[chat_id] = True
        return

    if chat_id in manual_ratings:
        try:
            rating = int(msg.text)
            price = get_price(rating)

            bot.send_message(chat_id,
                f"📊 Rating: {rating}\n💰 Price: ${price}")
            manual_ratings.pop(chat_id)
        except:
            bot.send_message(chat_id, "❌ Error")
        return

# ==============================
# ADMIN PHOTO
# ==============================
def admin_photo(msg):
    chat_id = msg.chat.id

    if msg.content_type != 'photo':
        bot.send_message(chat_id, "❌ Dir sawir")
        return

    rating = random.randint(3100, 3300)
    price = get_price(rating)

    set_today_market(msg.photo[-1].file_id, rating, price)

    bot.send_message(chat_id, "✅ La dhigay suuqa")

# ==============================
# RUN
# ==============================
print("Bot running...")
bot.infinity_polling()
