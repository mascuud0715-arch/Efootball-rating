import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import os
from pymongo import MongoClient
import hashlib

# ======================
# CONFIG
# ======================

TOKEN = os.getenv("BOT_TOKEN_2")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

PAY_NUMBERS = "+252677868526\n+252907868526"

bot = telebot.TeleBot(TOKEN)

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["titan_bot"]

# ======================
# HELPERS
# ======================

def get_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 IIBSO")
    return kb

def admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Stats", "➕ BAR SHAX")
    return kb

def paid_button():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ WAAN DIRAY", callback_data="paid"))
    return kb

def confirm_buttons(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ CONFIRM", callback_data=f"ok_{user_id}"),
        InlineKeyboardButton("❌ REJECT", callback_data=f"no_{user_id}")
    )
    return kb

# ======================
# START
# ======================

@bot.message_handler(commands=['start'])
def start(message):
    db.users.update_one(
        {"id": message.from_user.id},
        {"$set": {"id": message.from_user.id}},
        upsert=True
    )
    bot.send_message(message.chat.id, "Ku soo dhawoow 🤝", reply_markup=main_menu())

# ======================
# IIBSO
# ======================

@bot.message_handler(func=lambda m: m.text == "🛒 IIBSO")
def iibso(message):
    bot.send_message(message.chat.id, "📸 SOO DIR SHAXDA aad rabto inaad iibsatid")

# ======================
# HANDLE PHOTO (USER + ADMIN)
# ======================

admin_state = {}

@bot.message_handler(content_types=['photo'])
def handle_photo(message):

    # haddii admin BAR SHAX ku jiro
    if message.from_user.id == ADMIN_ID and admin_state.get("step") == "photo":
        file_info = bot.get_file(message.photo[-1].file_id)
        file = bot.download_file(file_info.file_path)

        img_hash = get_hash(file)

        admin_state["hash"] = img_hash
        admin_state["step"] = "price"

        bot.send_message(message.chat.id, "💰 Gali qiimaha shaxdan")
        return

    # USER NORMAL
    file_info = bot.get_file(message.photo[-1].file_id)
    file = bot.download_file(file_info.file_path)

    img_hash = get_hash(file)

    product = db.products.find_one({"hash": img_hash})

    if product:
        price = product["price"]

        bot.send_message(
            message.chat.id,
            f"💰 Qiimaha: {price}\n\nKu dir lacag:\n{PAY_NUMBERS}",
            reply_markup=paid_button()
        )
    else:
        bot.send_message(message.chat.id, "⏳ Shaxdan lama hayo, admin ayaa hubinaya...")

        bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"📥 Shax cusub user: {message.from_user.id}"
        )

# ======================
# ADMIN PANEL
# ======================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Admin Panel", reply_markup=admin_menu())

# ======================
# STATS
# ======================

@bot.message_handler(func=lambda m: m.text == "📊 Stats" and m.from_user.id == ADMIN_ID)
def stats(message):
    users = db.users.count_documents({})
    products = db.products.count_documents({})

    bot.send_message(
        message.chat.id,
        f"👥 Users: {users}\n📦 Shaxyo: {products}"
    )

# ======================
# BAR SHAX
# ======================

@bot.message_handler(func=lambda m: m.text == "➕ BAR SHAX" and m.from_user.id == ADMIN_ID)
def bar_shax(message):
    admin_state["step"] = "photo"
    bot.send_message(message.chat.id, "📸 Soo dir sawirka shaxda")

# ======================
# SAVE PRICE
# ======================

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def save_price(message):
    if admin_state.get("step") == "price":

        db.products.insert_one({
            "hash": admin_state["hash"],
            "price": message.text
        })

        bot.send_message(message.chat.id, "✅ Shax waa la keydiyay")

        admin_state.clear()

# ======================
# USER PAID
# ======================

@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid(call):
    user_id = call.from_user.id

    bot.send_message(user_id, "⏳ SUG 5 MIN SI LOO XAQIIJIYO")

    bot.send_message(
        ADMIN_ID,
        f"💳 User {user_id} wuxuu yiri WAA BIXIYAY",
        reply_markup=confirm_buttons(user_id)
    )

# ======================
# CONFIRM / REJECT
# ======================

@bot.callback_query_handler(func=lambda call: call.data.startswith("ok_"))
def confirm(call):
    user_id = int(call.data.split("_")[1])
    bot.send_message(user_id, "✅ WAA LA XAQIIJIYAY")

@bot.callback_query_handler(func=lambda call: call.data.startswith("no_"))
def reject(call):
    user_id = int(call.data.split("_")[1])
    bot.send_message(user_id, "❌ WAA LA DIIDAY")

# ======================
# RUN
# ======================

print("Bot running...")
