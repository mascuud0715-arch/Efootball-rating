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
manual_ratings = {}   # {chat_id: True}
admin_state = {}      # {chat_id: state} e.g. broadcast

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

def get_all_users():
    return [u['chat_id'] for u in users_col.find()]

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

# ==============================
# ADMIN PANEL BUTTONS
# ==============================
def admin_panel_buttons(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("Gali Shax Cusub"),
        KeyboardButton("Delete Shaxda Maanta"),
        KeyboardButton("Broadcast Text"),
        KeyboardButton("Broadcast Photo"),
        KeyboardButton("Broadcast Video"),
        KeyboardButton("Back")
    )
    bot.send_message(chat_id, "🛠️ Admin Panel:", reply_markup=markup)

# ==============================
# BUTTON HANDLER
# ==============================
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video'])
def handle_buttons(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == 'text' else None
    is_admin = (msg.from_user.id == ADMIN_ID)

    # --------------------------
    # MAIN MENU
    # --------------------------
    if text == "📈 Shaxda Suuqa Maanta":
        today = get_today_market()
        if 'photo_file_id' in today:
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {today.get('rating')}\n💰 Qiimaha: ${today.get('price')}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(chat_id, today['photo_file_id'], caption=caption)
        else:
            bot.send_message(chat_id, "❌ Shaxda suuqa maanta wali lama dhigin.")
        return

    # --------------------------
    # ADMIN PANEL
    # --------------------------
    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel_buttons(chat_id)
        return

    if is_admin:
        # ========================
        # ADMIN ACTIONS
        # ========================
        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka shaxda cusub:")
            bot.register_next_step_handler(msg, admin_photo_step)
            return

        elif text == "Delete Shaxda Maanta":
            reset_today_market()
            bot.send_message(chat_id, "✅ Shaxda suuqa maanta waa la tirtiray.")
            admin_panel_buttons(chat_id)
            return

        elif text == "Broadcast Text":
            bot.send_message(chat_id, "📢 Fadlan qor qoraalka aad rabto inaad u dirto dhamaan users:")
            admin_state[chat_id] = 'broadcast_text'
            return

        elif text == "Broadcast Photo":
            bot.send_message(chat_id, "📸 Fadlan soo dir sawirka aad rabto inaad u dirto dhamaan users:")
            admin_state[chat_id] = 'broadcast_photo'
            return

        elif text == "Broadcast Video":
            bot.send_message(chat_id, "🎥 Fadlan soo dir video-ga aad rabto inaad u dirto dhamaan users:")
            admin_state[chat_id] = 'broadcast_video'
            return

        elif text == "Back":
            main_menu_buttons(chat_id, True)
            return

    # --------------------------
    # HANDLE BROADCAST
    # --------------------------
    state = admin_state.get(chat_id)
    if state:
        all_users = get_all_users()
        try:
            if state == 'broadcast_text':
                for u in all_users:
                    bot.send_message(u, msg.text)
                bot.send_message(chat_id, f"✅ Broadcast Text waa la diray {len(all_users)} users.")
                admin_state[chat_id] = None
                return

            elif state == 'broadcast_photo' and msg.content_type == 'photo':
                for u in all_users:
                    bot.send_photo(u, msg.photo[-1].file_id, caption=msg.caption or "")
                bot.send_message(chat_id, f"✅ Broadcast Photo waa la diray {len(all_users)} users.")
                admin_state[chat_id] = None
                return

            elif state == 'broadcast_video' and msg.content_type == 'video':
                for u in all_users:
                    bot.send_video(u, msg.video.file_id, caption=msg.caption or "")
                bot.send_message(chat_id, f"✅ Broadcast Video waa la diray {len(all_users)} users.")
                admin_state[chat_id] = None
                return
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error broadcast: {e}")
            admin_state[chat_id] = None
            return

    # --------------------------
    # HANDLE USER PHOTO (MANUAL RATING)
    # --------------------------
    if msg.content_type == 'photo':
        bot.reply_to(msg, "📸 Sawirka waa la helay! Fadlan qor **rating-ka** shaxda eFootball (tusaale: 3150):")
        manual_ratings[chat_id] = True
        return

    # --------------------------
    # HANDLE USER RATING
    # --------------------------
    if chat_id in manual_ratings:
        try:
            rating = int(msg.text)
            if rating < 3000 or rating > 3500:
                bot.reply_to(msg, "❌ Rating-ka waa inuu noqdaa 3000–3500. Dib u qor.")
                return
            price = get_price(rating)
            caption = f"""🔥 **QIIMEYN DHAMEYSTIRAN** 🔥

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇
{WHATSAPP_LINK}"""
            bot.send_message(chat_id, caption)
            manual_ratings.pop(chat_id)
        except:
            bot.reply_to(msg, "❌ Fadlan qoro number sax ah oo 4-digit ah.")
        return

# ==============================
# ADMIN PHOTO HANDLER (AUTO RATING)
# ==============================
def admin_photo_step(msg):
    chat_id = msg.chat.id
    if msg.content_type != 'photo':
        bot.send_message(chat_id, "❌ Fadlan sawir u dir.")
        bot.register_next_step_handler(msg, admin_photo_step)
        return
    photo_id = msg.photo[-1].file_id
    rating = random.randint(3100, 3300)
    price = get_price(rating)
    set_today_market(photo_id, rating, price)
    bot.send_message(chat_id, f"✅ Shaxda suuqa maanta waa la keydiyay!\n📊 Rating: {rating}\n💰 Qiimaha: ${price}")
    admin_panel_buttons(chat_id)

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
