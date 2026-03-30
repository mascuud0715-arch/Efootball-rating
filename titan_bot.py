import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import os
from pymongo import MongoClient
import hashlib

# ======================
# CONFIG
# ======================

TOKEN = os.getenv("BOT_TOKEN_3")
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

# ===== FEE SYSTEM =====
def get_fee():
    data = db.settings.find_one({"name": "fee"})
    return data["status"] if data else False

def set_fee(status):
    db.settings.update_one(
        {"name": "fee"},
        {"$set": {"status": status}},
        upsert=True
    )

def apply_fee(price):
    try:
        price = float(price)
        if get_fee():
            price += 0.5
        return str(price)
    except:
        return price
# =====================

def main_menu(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if user_id == ADMIN_ID:
        kb.add("🛒 IIBSO", "⚙️ ADMIN PANEL")
    else:
        kb.add("🛒 IIBSO")
    return kb

def admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Stats", "➕ BAR SHAX")
    kb.add("🔄 SHAX TO SHAX", "🗑 DELETE SHAX")
    kb.add("💰 FEE ON/OFF")  # 👈 NEW
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
# STATE
# ======================

admin_state = {}

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
    bot.send_message(message.chat.id, """Ku soo dhawoow Titan Market Bot 
    HalKaan waxaad Ka heli kartaa Shaxo
    soo dir Shaxda aad Rabto Inaad iibsato
    oo hel Qiimah uu kusoo siiyay admin
    oo u qaado shaxdaada si automatic 🤖 ah
    iyada oo aan lahayn wax fee ah
    nagu xirnow mar walba oo naha hel waxa ad rabto
    groupkeenana waakan Join 👇
    https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t""", reply_markup=main_menu(message.from_user.id))

# ======================
# ADMIN PANEL
# ======================

@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    bot.send_message(message.chat.id, "Admin Panel", reply_markup=admin_menu())

# ======================
# FEE BUTTON
# ======================

@bot.message_handler(func=lambda m: m.text == "💰 FEE ON/OFF" and m.from_user.id == ADMIN_ID)
def toggle_fee(message):
    current = get_fee()
    new = not current
    set_fee(new)

    status = "ON (+0.5)" if new else "OFF"
    bot.send_message(message.chat.id, f"Fee: {status}")

# ======================
# STATS
# ======================

@bot.message_handler(func=lambda m: m.text == "📊 Stats" and m.from_user.id == ADMIN_ID)
def stats(message):
    users = db.users.count_documents({})
    products = db.products.count_documents({})
    mappings = db.mappings.count_documents({})

    bot.send_message(message.chat.id, f"👥 Users: {users}\n📦 Shaxyo: {products}\n🔄 Mappings: {mappings}")

# ======================
# BAR SHAX (NORMAL)
# ======================

@bot.message_handler(func=lambda m: m.text == "➕ BAR SHAX" and m.from_user.id == ADMIN_ID)
def bar_shax(message):
    admin_state["step"] = "add_photo"
    bot.send_message(message.chat.id, "📸 Soo dir sawirka shaxda")

# ======================
# SHAX TO SHAX
# ======================

@bot.message_handler(func=lambda m: m.text == "🔄 SHAX TO SHAX" and m.from_user.id == ADMIN_ID)
def shax_to_shax(message):
    admin_state["step"] = "map_input"
    bot.send_message(message.chat.id, "📸 Soo dir sawirka INPUT (shax 1aad)")

# ======================
# DELETE SHAX
# ======================

@bot.message_handler(func=lambda m: m.text == "🗑 DELETE SHAX" and m.from_user.id == ADMIN_ID)
def delete_shax(message):
    admin_state["step"] = "delete"
    bot.send_message(message.chat.id, "📸 Soo dir sawirka shaxda aad tirtirayso")

# ======================
# HANDLE PHOTO
# ======================

@bot.message_handler(content_types=['photo'])
def handle_photo(message):

    file_info = bot.get_file(message.photo[-1].file_id)
    file = bot.download_file(file_info.file_path)
    img_hash = get_hash(file)

    # ===== ADD SHAX =====
    if message.from_user.id == ADMIN_ID and admin_state.get("step") == "add_photo":
        admin_state["hash"] = img_hash
        admin_state["step"] = "add_price"
        bot.send_message(message.chat.id, "💰 Gali qiimaha")
        return

    # ===== DELETE =====
    if message.from_user.id == ADMIN_ID and admin_state.get("step") == "delete":
        db.products.delete_one({"hash": img_hash})
        db.mappings.delete_one({"input_hash": img_hash})
        bot.send_message(message.chat.id, "🗑 Waa la tirtiray")
        admin_state.clear()
        return

    # ===== SHAX TO SHAX =====
    if message.from_user.id == ADMIN_ID and admin_state.get("step") == "map_input":
        admin_state["input_hash"] = img_hash
        admin_state["step"] = "map_output"
        bot.send_message(message.chat.id, "📸 Soo dir sawirka OUTPUT")
        return

    if message.from_user.id == ADMIN_ID and admin_state.get("step") == "map_output":
        admin_state["output_file_id"] = message.photo[-1].file_id
        admin_state["step"] = "map_text"
        bot.send_message(message.chat.id, "✍️ Gali qoraalka")
        return

    # ===== USER =====
    product = db.products.find_one({"hash": img_hash})
    mapping = db.mappings.find_one({"input_hash": img_hash})

    if product:
        price = apply_fee(product["price"])  # 👈 FEE APPLIED

        bot.send_message(
            message.chat.id,
            f"💰 Qiimaha: {price}\n\nKu dir:\n{PAY_NUMBERS}",
            reply_markup=paid_button()
        )

    elif mapping:
        bot.send_photo(
            message.chat.id,
            mapping["output_file_id"],
            caption=mapping["text"]
        )

    else:
        bot.send_message(message.chat.id, "⏳ Lama hayo, admin ayaa hubinaya")
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id)

# ======================
# SAVE TEXT / PRICE
# ======================

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def handle_admin_text(message):

    if admin_state.get("step") == "add_price":
        db.products.insert_one({
            "hash": admin_state["hash"],
            "price": message.text
        })
        bot.send_message(message.chat.id, "✅ Waa la keydiyay")
        admin_state.clear()

    elif admin_state.get("step") == "map_text":
        db.mappings.insert_one({
            "input_hash": admin_state["input_hash"],
            "output_file_id": admin_state["output_file_id"],
            "text": message.text
        })
        bot.send_message(message.chat.id, "✅ Mapping waa la keydiyay")
        admin_state.clear()

# ======================
# PAYMENT
# ======================

@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "⏳ SUG 5 MIN")

    bot.send_message(
        ADMIN_ID,
        f"User {user_id} paid",
        reply_markup=confirm_buttons(user_id)
    )

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

print("Titan bot running...")
