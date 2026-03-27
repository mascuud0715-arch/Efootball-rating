import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import random
import os

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

WHATSAPP_LINK = "https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t"
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Telegram ID admin-ka

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
# TODAY MARKET STORAGE
# ==============================
today_market = {}  # {'photo_file_id': '', 'rating': int, 'price': int}

# ==============================
# REPLY KEYBOARD
# ==============================
def main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Shaxda Suuqa Maanta"))
    if user_id == ADMIN_ID:
        markup.add(KeyboardButton("Admin Panel"))
    return markup

# ==============================
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "👋 Soo dhawoow! Riix button-ka hoose:",
        reply_markup=main_keyboard(msg.from_user.id)
    )

# ==============================
# ADMIN STATE
# ==============================
admin_state = {}  # {'awaiting_photo': bool, 'awaiting_rating': bool}

# ==============================
# HANDLE TEXT BUTTONS
# ==============================
@bot.message_handler(func=lambda m: True)
def handle_buttons(msg):
    text = msg.text

    # ==============================
    # User wants to view today's market
    # ==============================
    if text == "Shaxda Suuqa Maanta":
        if 'photo_file_id' in today_market:
            rating = today_market.get('rating', '?')
            price = today_market.get('price', '?')
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {rating}\n💰 Qiimaha: ${price}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(msg.chat.id, today_market['photo_file_id'], caption=caption)
        else:
            bot.send_message(msg.chat.id, "❌ Shaxda suuqa maanta wali lama dhigin. Fadlan sug.")
        return

    # ==============================
    # Admin Panel
    # ==============================
    if text == "Admin Panel":
        if msg.from_user.id != ADMIN_ID:
            bot.send_message(msg.chat.id, "❌ Ma aadan ahayn admin.")
            return
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("Gali Shax Cusub"),
            KeyboardButton("Update Shaxda Maanta"),
            KeyboardButton("Delete Shaxda Maanta"),
        )
        bot.send_message(msg.chat.id, "🛠 Admin Panel - dooro ficilka:", reply_markup=markup)
        return

    # ==============================
    # Admin Gali Shax Cusub
    # ==============================
    if text == "Gali Shax Cusub" and msg.from_user.id == ADMIN_ID:
        bot.send_message(msg.chat.id, "📸 Fadlan soo dir sawirka shaxda suuqa maanta.")
        admin_state[msg.chat.id] = {'awaiting_photo': True}
        return

    # ==============================
    # Admin Update Shax
    # ==============================
    if text == "Update Shaxda Maanta" and msg.from_user.id == ADMIN_ID:
        if 'photo_file_id' not in today_market:
            bot.send_message(msg.chat.id, "❌ Shaxda maanta wali lama dhigin. Isticmaal 'Gali Shax Cusub'.")
            return
        bot.send_message(msg.chat.id, "📸 Fadlan soo dir sawirka cusub ee shaxda suuqa maanta.")
        admin_state[msg.chat.id] = {'awaiting_photo': True}
        return

    # ==============================
    # Admin Delete Shax
    # ==============================
    if text == "Delete Shaxda Maanta" and msg.from_user.id == ADMIN_ID:
        today_market.clear()
        bot.send_message(msg.chat.id, "🗑 Shaxda suuqa maanta waa la tirtiray.")
        return

    bot.send_message(msg.chat.id, "❌ Fadlan dooro button sax ah.", reply_markup=main_keyboard(msg.from_user.id))

# ==============================
# HANDLE ADMIN PHOTO
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_admin_photo(message):
    chat_id = message.chat.id
    if chat_id in admin_state and admin_state[chat_id].get('awaiting_photo'):
        today_market['photo_file_id'] = message.photo[-1].file_id
        bot.send_message(chat_id, "Fadlan qor **rating-ka** shaxda:")
        admin_state[chat_id]['awaiting_photo'] = False
        admin_state[chat_id]['awaiting_rating'] = True
        return

# ==============================
# HANDLE ADMIN RATING
# ==============================
@bot.message_handler(func=lambda m: m.chat.id in admin_state and admin_state[m.chat.id].get('awaiting_rating'))
def handle_admin_rating(msg):
    chat_id = msg.chat.id
    try:
        rating = int(msg.text)
        price = get_price(rating)
        today_market['rating'] = rating
        today_market['price'] = price
        admin_state[chat_id]['awaiting_rating'] = False
        bot.send_message(chat_id, f"✅ Shaxda suuqa maanta waa la keydiyay!\nRating: {rating}\nPrice: ${price}", reply_markup=main_keyboard(chat_id))
    except:
        bot.send_message(chat_id, "❌ Fadlan qor number sax ah oo 4-digit ah.")

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
