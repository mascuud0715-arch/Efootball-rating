import telebot
import pytesseract
from PIL import Image
import random
import os
import re
import time

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

WHATSAPP_LINK = "https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t"

# ==============================
# PRICE SYSTEM
# ==============================
def get_price(rating):
    if 3100 <= rating <= 3130:
        return random.randint(2, 4)
    elif 3130 < rating <= 3150:
        return random.randint(6, 8)
    elif 3150 < rating <= 3170:
        return random.randint(7, 10)
    elif 3170 < rating <= 3190:
        return random.randint(9, 12)
    elif 3190 < rating <= 3210:
        return random.randint(10, 14)
    elif 3210 < rating <= 3250:
        return random.randint(20, 40)
    elif 3250 < rating <= 3310:
        return random.randint(40, 100)
    else:
        return None

# ==============================
# START
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")

# ==============================
# LIVE ANIMATION FUNCTION
# ==============================
def animate_checking(chat_id, message_id):
    frames = ["⏳ Checking.", "⏳ Checking..", "⏳ Checking...", "⏳ Checking...."]
    for i in range(6):  # tirada animation-ka
        text = frames[i % len(frames)]
        try:
            bot.edit_message_text(text, chat_id, message_id)
        except:
            pass
        time.sleep(0.5)

# ==============================
# HANDLE PHOTO
# ==============================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # Send initial message
        msg = bot.reply_to(message, "⏳ Checking...")

        # Start animation
        animate_checking(message.chat.id, msg.message_id)

        # download image
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open("team.jpg", "wb") as f:
            f.write(downloaded_file)

        # OCR
        img = Image.open("team.jpg")
        text = pytesseract.image_to_string(img)

        numbers = re.findall(r'\d{4}', text)

        rating = None
        for num in numbers:
            num = int(num)
            if 3000 < num < 3500:
                rating = num
                break

        if rating:
            price = get_price(rating)

            if price:
                final_text = f"""🔥 **QIIMEYN DHAMEYSTIRAN** 🔥

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 Fadlan Ka iibso shaxo iyo Coinsba La hubo 100% Tayo sare Groupkan Mahadsanid 👇
{WHATSAPP_LINK}
"""
            else:
                final_text = "❌ Rating-ka lama taageerin"
        else:
            final_text = "❌ Sawirkan ma aha shax eFootball ah.\n\n👉 Fadlan soo dir shaxdaada si loo qiimeeyo Qiimaheeda $"

        # Edit final result (NO DELETE)
        bot.edit_message_text(
            final_text,
            message.chat.id,
            msg.message_id,
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.send_message(message.chat.id, "❌ Qalad ayaa dhacay, isku day mar kale")

# ==============================
# RUN
# ==============================
print("Bot is running...")
bot.infinity_polling()
