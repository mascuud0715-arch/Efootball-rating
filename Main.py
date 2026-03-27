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
manual_ratings = {}   # user manual rating input
today_market = {}     # {'photo_file_id': '', 'rating': int, 'price': int}
admin_state = {}      # track admin actions

# ==============================
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    is_admin = (msg.from_user.id == ADMIN_ID)
    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")
    main_menu_buttons(msg.chat.id, is_admin)

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

    # --------------------------
    # MAIN MENU ACTIONS
    # --------------------------
    if text == "📈 Shaxda Suuqa Maanta":
        if 'photo_file_id' in today_market:
            rating = today_market.get('rating', '?')
            price = today_market.get('price', '?')
            caption = f"🔥 Shaxda Suuqa Maanta 🔥\n\n📊 Rating: {rating}\n💰 Qiimaha: ${price}\n\n📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇\n{WHATSAPP_LINK}"
            bot.send_photo(chat_id, today_market['photo_file_id'], caption=caption)
        else:
            bot.send_message(chat_id, "❌ Shaxda suuqa maanta wali lama dhigin. Fadlan sug.")
        return

    elif text == "🛠️ Admin Panel":
        if msg.from_user.id != ADMIN_ID:
            bot.send_message(chat_id, "❌ Ma aadan ahayn admin.")
            return
        admin_panel_buttons(chat_id)
        admin_state[chat_id] = None
        return

    # --------------------------
    # ADMIN PANEL ACTIONS
    # --------------------------
    elif text == "Gali Shax Cusub" and msg.from_user.id == ADMIN_ID:
        bot.send_message(chat_id, "📸 Fadlan soo dir sawirka shaxda cusub:")
        admin_state[chat_id] = 'add_new'
        return

    elif text == "Update Shax Cusub" and msg.from_user.id == ADMIN_ID:
        if 'photo_file_id' not in today_market:
            bot.send_message(chat_id, "❌ Shaxda maanta lama hayo, fadlan marka hore gali.")
            return
        bot.send_message(chat_id, "📸 Fadlan soo dir sawirka cusub ee shaxda maanta:")
        admin_state[chat_id] = 'update'
        return

    elif text == "Delete Shaxda Maanta" and msg.from_user.id == ADMIN_ID:
        today_market.clear()
        bot.send_message(chat_id, "✅ Shaxda suuqa maanta waa la tirtiray.")
        admin_panel_buttons(chat_id)
        return

    elif text == "Back":
        main_menu_buttons(chat_id)
        return

    # --------------------------
    # USER MANUAL RATING INPUT
    # --------------------------
    elif chat_id in manual_ratings:
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
# PHOTO HANDLER (ADMIN & USER HALIS)
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    state = admin_state.get(chat_id)

    # --------------------------
    # ADMIN PHOTO
    # --------------------------
    if state in ['add_new', 'update']:
        today_market['photo_file_id'] = message.photo[-1].file_id
        bot.send_message(chat_id, "📊 Fadlan qor **Rating iyo Qiimaha** shaxda (Tusaale: 3150 25):")
        admin_state[chat_id] = 'awaiting_rating_price'
        return

    # --------------------------
    # USER PHOTO
    # --------------------------
    bot.reply_to(message, "📸 Sawirka waa la helay!\nFadlan qor **rating-ka** shaxda eFootball (tusaale: 3150):")
    manual_ratings[chat_id] = True

# ==============================
# HANDLE ADMIN RATING + PRICE
# ==============================
@bot.message_handler(func=lambda m: admin_state.get(m.chat.id) == 'awaiting_rating_price')
def handle_admin_rating_price(msg):
    chat_id = msg.chat.id
    try:
        parts = msg.text.split()
        if len(parts) != 2:
            bot.send_message(chat_id, "❌ Fadlan qor Rating iyo Price sida: 3150 25")
            return
        rating = int(parts[0])
        price = float(parts[1])
        today_market['rating'] = rating
        today_market['price'] = price
        admin_state[chat_id] = None
        bot.send_message(chat_id, f"✅ Shaxda suuqa maanta waa la keydiyay!\n📊 Rating: {rating}\n💰 Qiimaha: ${price}")
        admin_panel_buttons(chat_id)
    except:
        bot.send_message(chat_id, "❌ Fadlan qor number sax ah oo qaab: Rating Price (tusaale: 3150 25)")

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
