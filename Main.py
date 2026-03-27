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
    elif 3210 < rating <= 3250: return random.randint(20, 35)
    elif 3250 < rating <= 3310: return random.randint(40, 100)
    else: return None

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
    state_doc = admin_state_col.find_one({"chat_id": chat_id})
    return state_doc['state'] if state_doc else None

def set_admin_state(chat_id, state):
    admin_state_col.update_one({"chat_id": chat_id}, {"$set": {"state": state}}, upsert=True)

def add_user(chat_id):
    users_col.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

def get_all_users():
    return [u['chat_id'] for u in users_col.find()]

# ==============================
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    add_user(chat_id)
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
        KeyboardButton("Stats Admin"),
        KeyboardButton("Back")
    )
    bot.send_message(chat_id, "🛠️ Admin Panel:", reply_markup=markup)

# ==============================
# BUTTON HANDLER
# ==============================
manual_ratings = {}  # temporary manual rating state

@bot.message_handler(func=lambda m: True)
def handle_buttons(msg):
    chat_id = msg.chat.id
    text = msg.text
    user_is_admin = (msg.from_user.id == ADMIN_ID)
    state = get_admin_state(chat_id)

    # --------------------------
    # MAIN MENU ACTIONS
    # --------------------------
    if text == "📈 Shaxda Suuqa Maanta":
        today = get_today_market()
        if today:
            rating = today.get('rating', '?')
            price = today.get('price', '?')
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {rating}\n💰 Qiimaha: ${price}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(chat_id, today['photo_file_id'], caption=caption)
        else:
            bot.send_message(chat_id, "❌ Shaxda suuqa maanta wali lama dhigin. Fadlan sug.")
        return

    elif text == "🛠️ Admin Panel":
        if not user_is_admin:
            bot.send_message(chat_id, "❌ Ma aadan ahayn admin.")
            return
        admin_panel_buttons(chat_id)
        set_admin_state(chat_id, None)
        return

    # --------------------------
    # ADMIN PANEL ACTIONS
    # --------------------------
    if user_is_admin:
        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka shaxda cusub:")
            set_admin_state(chat_id, 'add_new')
            return

        elif text == "Update Shax Cusub":
            today = get_today_market()
            if not today:
                bot.send_message(chat_id, "❌ Shaxda maanta lama hayo, fadlan marka hore gali.")
                return
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka cusub ee shaxda maanta:")
            set_admin_state(chat_id, 'update')
            return

        elif text == "Delete Shaxda Maanta":
            reset_today_market()
            bot.send_message(chat_id, "✅ Shaxda suuqa maanta waa la tirtiray.")
            admin_panel_buttons(chat_id)
            return

        elif text == "Broadcast Fariin":
            bot.send_message(chat_id, "📢 Fadlan soo dir fariinta broadcast (text, photo ama video):")
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
    state = get_admin_state(chat_id)

    # --------------------------
    # ADMIN PHOTO
    # --------------------------
    if state in ['add_new', 'update']:
        photo_id = message.photo[-1].file_id
        bot.send_message(chat_id, "📊 Fadlan qor **Rating iyo Qiimaha** shaxda (Tusaale: 3150 25):")
        set_admin_state(chat_id, 'awaiting_rating_price')
        admin_state_col.update_one({"chat_id": chat_id}, {"$set": {"photo_file_id": photo_id}}, upsert=True)
        return

    # --------------------------
    # BROADCAST PHOTO
    # --------------------------
    if state == 'broadcast' and chat_id == ADMIN_ID:
        for user_id in get_all_users():
            bot.send_photo(user_id, message.photo[-1].file_id)
        bot.send_message(chat_id, "✅ Broadcast photo waa la diray dhammaan users-ka.")
        set_admin_state(chat_id, None)
        return

    # --------------------------
    # USER PHOTO (manual rating)
    # --------------------------
    bot.reply_to(message, "📸 Sawirka waa la helay!\nFadlan qor **rating-ka** shaxda eFootball (tusaale: 3150):")
    manual_ratings[chat_id] = True

# ==============================
# VIDEO HANDLER (BROADCAST)
# ==============================
@bot.message_handler(content_types=['video'])
def handle_video(message):
    chat_id = message.chat.id
    if get_admin_state(chat_id) == 'broadcast' and chat_id == ADMIN_ID:
        for user_id in get_all_users():
            bot.send_video(user_id, message.video.file_id)
        bot.send_message(chat_id, "✅ Broadcast video waa la diray dhammaan users-ka.")
        set_admin_state(chat_id, None)

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
        state_doc = admin_state_col.find_one({"chat_id": chat_id})
        photo_id = state_doc.get('photo_file_id') if state_doc else None
        if not photo_id:
            bot.send_message(chat_id, "❌ Wax sawir ah lama hayo. Fadlan dib u soo dir sawirka.")
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
    except:
        bot.send_message(chat_id, "❌ Fadlan qor number sax ah oo qaab: Rating Price (tusaale: 3150 25)")

# ==============================
# BROADCAST TEXT HANDLER
# ==============================
@bot.message_handler(func=lambda m: get_admin_state(m.chat.id) == 'broadcast')
def handle_broadcast_text(msg):
    chat_id = msg.chat.id
    if chat_id == ADMIN_ID and msg.content_type == 'text':
        for user_id in get_all_users():
            bot.send_message(user_id, msg.text)
        bot.send_message(chat_id, "✅ Broadcast text waa la diray dhammaan users-ka.")
        set_admin_state(chat_id, None)

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
