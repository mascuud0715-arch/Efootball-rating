import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
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
# STORE TODAY'S MARKET
# ==============================
today_market = {}  # {'photo_file_id': '', 'rating': int, 'price': int}

# ==============================
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📈 Shaxda Suuqa Maanta", callback_data="view_market"))
    bot.send_message(msg.chat.id, "👋 Soo dhawoow! Riix button-ka hoose si aad u aragto shaxda suuqa maanta.", reply_markup=markup)

# ==============================
# ADMIN: SET MARKET
# ==============================
@bot.message_handler(commands=['set_market'])
def set_market(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "❌ Ma aadan ahayn admin.")
        return
    bot.reply_to(msg, "📸 Fadlan soo dir sawirka shaxda suuqa maanta oo wata rating:")

    # Set admin waiting state
    today_market['waiting'] = True

@bot.message_handler(content_types=['photo'])
def handle_admin_photo(message):
    if 'waiting' in today_market and today_market['waiting'] and message.from_user.id == ADMIN_ID:
        today_market['photo_file_id'] = message.photo[-1].file_id
        bot.reply_to(message, "Fadlan qor rating-ka shaxda:")
        today_market['waiting'] = 'awaiting_rating'
        return

    # User normal photo handling can go here if needed
    bot.reply_to(message, "📸 Sawirka waa la helay, laakiin tani waa user-ka caadiga ah.")

@bot.message_handler(func=lambda m: 'waiting' in today_market and today_market['waiting'] == 'awaiting_rating' and m.from_user.id == ADMIN_ID)
def handle_admin_rating(msg):
    try:
        rating = int(msg.text)
        price = get_price(rating)
        today_market['rating'] = rating
        today_market['price'] = price
        today_market.pop('waiting')  # clear state
        bot.reply_to(msg, f"✅ Shaxda suuqa maanta waa la keydiyay!\nRating: {rating}\nPrice: ${price}")
    except:
        bot.reply_to(msg, "❌ Fadlan qor number sax ah.")

# ==============================
# USER: VIEW MARKET BUTTON
# ==============================
@bot.callback_query_handler(func=lambda call: call.data == "view_market")
def view_market(call):
    if 'photo_file_id' in today_market:
        rating = today_market.get('rating', '?')
        price = today_market.get('price', '?')
        caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {rating}\n💰 Qiimaha: ${price}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
        bot.send_photo(call.message.chat.id, today_market['photo_file_id'], caption=caption)
    else:
        bot.send_message(call.message.chat.id, "❌ Shaxda suuqa maanta wali lama dhigin. Fadlan sug.")

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
