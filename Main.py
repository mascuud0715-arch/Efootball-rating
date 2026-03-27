import telebot
import pytesseract
from PIL import Image, ImageFilter, ImageOps
import random
import os
import re
import time

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("BOT_TOKEN")  # Telegram bot token
bot = telebot.TeleBot(TOKEN)

# Path to tesseract executable (update if needed)
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

WHATSAPP_LINK = "https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t"

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
# START COMMAND
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")

# ==============================
# LIVE ANIMATION FUNCTION
# ==============================
def animate_checking(chat_id, message_id):
    frames = ["⏳ Checking.", "⏳ Checking..", "⏳ Checking...", "⏳ Checking...."]
    for i in range(6):
        text = frames[i % len(frames)]
        try: bot.edit_message_text(text, chat_id, message_id)
        except: pass
        time.sleep(0.5)

# ==============================
# MANUAL RATING FALLBACK
# ==============================
manual_ratings = {}

@bot.message_handler(func=lambda m: m.chat.id in manual_ratings)
def handle_manual_rating(msg):
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
# HANDLE PHOTO
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        msg = bot.reply_to(message, "⏳ Checking...")
        animate_checking(message.chat.id, msg.message_id)

        # Download image
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("team.jpg", "wb") as f: f.write(downloaded_file)

        # Preprocess image
        img = Image.open("team.jpg").convert('L')
        img = img.resize((img.width*2, img.height*2))
        img = img.filter(ImageFilter.SHARPEN)
        img = ImageOps.autocontrast(img)
        img = img.point(lambda x: 0 if x < 140 else 255)

        # OCR
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        raw_text = pytesseract.image_to_string(img, config=config)

        # Fix common OCR errors
        raw_text = raw_text.replace("O", "0").replace("I", "1").replace("l", "1")
        raw_text = re.sub(r'[^0-9]', '', raw_text)
        print("OCR RAW TEXT:", raw_text)

        # Find 4-digit rating
        rating = None
        for i in range(len(raw_text)-3):
            num = raw_text[i:i+4]
            try:
                n = int(num)
                if 3000 < n < 3500:
                    rating = n
                    break
            except: continue

        if rating:
            price = get_price(rating)
            final_text = f"""🔥 **QIIMEYN DHAMEYSTIRAN** 🔥

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 Ka iibso shaxo iyo Coins 100% Tayo sare Groupkan 👇
{WHATSAPP_LINK}"""
            bot.edit_message_text(final_text, message.chat.id, msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(
                "❌ OCR-ku ma aqoonsan rating-ka.\n\nFadlan qor rating-ka 3000–3500 si manual ah:",
                message.chat.id, msg.message_id
            )
            manual_ratings[message.chat.id] = True

    except Exception as e:
        print("ERROR:", e)
        bot.send_message(message.chat.id, "❌ Qalad ayaa dhacay, isku day mar kale")

# ==============================
# RUN BOT
# ==============================
print("Bot is running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
