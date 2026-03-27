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
ADMIN_ID = int(os.getenv("ADMIN_ID"))

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
manual_ratings = {}  # {chat_id: True}
today_market = {}    # {'photo_file_id': '', 'rating': int, 'price': int}

# ==============================
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("📈 Shaxda Suuqa Maanta"),
        KeyboardButton("🛠️ Admin Panel")
    )
    bot.send_message(msg.chat.id,
                     "👋 Soo dhawoow! Riix button-ka hoose si aad u aragto shaxda suuqa maanta ama admin panel.",
                     reply_markup=markup)

# ==============================
# BUTTON HANDLER
# ==============================
@bot.message_handler(func=lambda m: True)
def button_handler(msg):
    if msg.text == "📈 Shaxda Suuqa Maanta":
        if 'photo_file_id' in today_market:
            rating = today_market.get('rating', '?')
            price = today_market.get('price', '?')
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {rating}\n💰 Qiimaha: ${price}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(msg.chat.id, today_market['photo_file_id'], caption=caption)
        else:
            bot.send_message(msg.chat.id, "❌ Shaxda suuqa maanta wali lama dhigin. Fadlan sug.")
    elif msg.text == "🛠️ Admin Panel":
        if msg.from_user.id != ADMIN_ID:
            bot.send_message(msg.chat.id, "❌ Ma aadan ahayn admin.")
            return
        bot.send_message(msg.chat.id, "🛠️ Admin Panel: Soo dir sawirka shaxda maanta.")
        today_market['waiting'] = True
    elif msg.chat.id in manual_ratings:
        # HANDLE MANUAL RATING INPUT
        try:
            rating = int(msg.text)
            if rating < 3000 or rating > 3500:
                bot.reply_to(msg, "❌ Rating-ka waa inuu noqdaa 3000–3500. Dib u qor.")
                return

            price = get_price(rating)
            final_text = f"""🔥 **QIIMEYN DHAMEYSTIRAN** 🔥

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇
{WHATSAPP_LINK}"""

            bot.send_message(msg.chat.id, final_text)
            manual_ratings.pop(msg.chat.id)
        except:
            bot.reply_to(msg, "❌ Fadlan qoro number sax ah oo 4-digit ah.")

# ==============================
# ADMIN PHOTO HANDLER
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_admin_photo(message):
    if 'waiting' in today_market and today_market['waiting'] and message.from_user.id == ADMIN_ID:
        today_market['photo_file_id'] = message.photo[-1].file_id
        bot.reply_to(message, "📊 Fadlan qor rating-ka shaxda maanta:")
        today_market['waiting'] = 'awaiting_rating'
        return

    # User normal photo handling
    bot.reply_to(message, "📸 Sawirka waa la helay!\nFadlan qor **rating-ka** shaxda eFootball (tusaale: 3150):")
    manual_ratings[message.chat.id] = True

# ==============================
# ADMIN RATING HANDLER
# ==============================
@bot.message_handler(func=lambda m: 'waiting' in today_market and today_market['waiting'] == 'awaiting_rating' and m.from_user.id == ADMIN_ID)
def handle_admin_rating(msg):
    try:
        rating = int(msg.text)
        price = get_price(rating)
        today_market['rating'] = rating
        today_market['price'] = price
        today_market.pop('waiting')
        bot.reply_to(msg, f"✅ Shaxda suuqa maanta waa la keydiyay!\nRating: {rating}\nPrice: ${price}")
    except:
        bot.reply_to(msg, "❌ Fadlan qor number sax ah.")

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
