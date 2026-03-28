import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import random
import os
from pymongo import MongoClient
from datetime import datetime

# ==============================
# CONFIG
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8669162116

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['efb_bot']

users_col = db['users']
market_col = db['market']
free_col = db['free']

manual_ratings = {}
admin_state = {}

# USER MARKET + BUY SYSTEM
user_market = {}
buy_state = {}

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
    return 0

# ==============================
# USER SYSTEM
# ==============================

def generate_ref():
    while True:
        ref = random.randint(10000, 99999)
        if not users_col.find_one({"ref": ref}):
            return ref

def add_user(chat_id, username=None):
    if not users_col.find_one({"chat_id": chat_id}):
        users_col.insert_one({
            "chat_id": chat_id,
            "username": username,
            "ref": generate_ref(),
            "date": datetime.utcnow().date().isoformat()
        })

def get_user(chat_id):
    return users_col.find_one({"chat_id": chat_id})

# ==============================
# MARKET
# ==============================

def get_today_market():
    return market_col.find_one({"today": True}) or {}

def set_today_market(photo, rating, price):
    market_col.update_one(
        {"today": True},
        {"$set": {
            "photo": photo,
            "rating": rating,
            "price": price,
            "today": True
        }},
        upsert=True
    )

# ==============================
# MENUS
# ==============================

def main_menu(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📈 Shaxda Suuqa Maanta", "🎁 SHAXAHA FREE")
    markup.add("🛒 SHAX DHIGO SUUQA")

    if is_admin:
        markup.add("🛠️ Admin Panel")

    bot.send_message(chat_id, "Dooro 👇", reply_markup=markup)

# ==============================
# START
# ==============================

@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    username = msg.from_user.username

    add_user(chat_id, username)

    bot.send_message(chat_id, "👋 Kusoo dhawoow Bot-ka Suuqa")
    main_menu(chat_id, msg.from_user.id == ADMIN_ID)

# ==============================
# MAIN HANDLER
# ==============================

@bot.message_handler(func=lambda m: True, content_types=['text','photo'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == "text" else None
    is_admin = (msg.from_user.id == ADMIN_ID)

    # ==========================
    # ADD MARKET (USER)
    # ==========================

    if text == "🛒 SHAX DHIGO SUUQA":
        user_market[chat_id] = {"step": "photo"}
        bot.send_message(chat_id, "📸 Soo dir sawirka")
        return

    state = user_market.get(chat_id)

    if state and state["step"] == "photo" and msg.content_type == "photo":
        user_market[chat_id]["photo"] = msg.photo[-1].file_id
        user_market[chat_id]["step"] = "rating"
        bot.send_message(chat_id, "📊 Qor rating")
        return

    if state and state["step"] == "rating":
        if not text or not text.isdigit():
            bot.send_message(chat_id, "❌ Number sax ah geli")
            return

        user_market[chat_id]["rating"] = int(text)
        user_market[chat_id]["step"] = "price"
        bot.send_message(chat_id, "💰 Qor price")
        return

    if state and state["step"] == "price":
        if not text or not text.isdigit():
            bot.send_message(chat_id, "❌ Number sax ah geli")
            return

        user_market[chat_id]["price"] = int(text)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ WAAN DIRAY", callback_data="user_confirm"))

        bot.send_message(chat_id,
            "📲 Ku dir lacag kadib riix WAAN DIRAY",
            reply_markup=markup)
        return

    # ==========================
    # VIEW MARKET + BUY
    # ==========================

    if text == "📈 Shaxda Suuqa Maanta":
        data = get_today_market()

        if "photo" not in data:
            bot.send_message(chat_id, "❌ Ma jiro")
            return

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🛒 IIBSO", callback_data="buy"))

        bot.send_photo(chat_id, data["photo"],
            caption=f"📊 {data['rating']}\n💰 ${data['price']}",
            reply_markup=markup)
        return

# ==============================
# CALLBACKS
# ==============================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id

    # USER SEND CONFIRM
    if call.data == "user_confirm":
        data = user_market.get(chat_id)

        if not data:
            return

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ CONFIRM", callback_data=f"admin_ok_{chat_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"admin_no_{chat_id}")
        )

        bot.send_photo(
            ADMIN_ID,
            data["photo"],
            caption=f"New Market\nUser: {chat_id}\nRating: {data['rating']}\nPrice: {data['price']}",
            reply_markup=markup
        )

        bot.send_message(chat_id, "⏳ Sug admin")
        user_market.pop(chat_id)

    # ==============================
# CALLBACK CONTINUATION (ADMIN + BUY SYSTEM)
# ==============================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    # ==========================
    # ADMIN APPROVE MARKET
    # ==========================
    if data.startswith("admin_ok_"):
        user_id = int(data.split("_")[2])

        # GET LAST DATA (TEMP FIX)
        # waxaad rabtaa inaad DB ku kaydiso mustaqbalka
        bot.send_message(user_id, "✅ Shaxdaada waa la aqbalay waxayna gashay suuqa")

        # waxaan ka qaadeynaa message caption
        caption = call.message.caption

        try:
            rating = int(caption.split("Rating: ")[1].split("\n")[0])
            price = int(caption.split("Price: ")[1])
        except:
            rating = 0
            price = 0

        set_today_market(call.message.photo[-1].file_id, rating, price)

        bot.edit_message_caption(
            "✅ LA AQBALAY",
            call.message.chat.id,
            call.message.message_id
        )

    # ==========================
    # ADMIN REJECT MARKET
    # ==========================
    elif data.startswith("admin_no_"):
        user_id = int(data.split("_")[2])

        bot.send_message(user_id, "❌ Codsigaaga waa la diiday")

        bot.edit_message_caption(
            "❌ LA DIIDAY",
            call.message.chat.id,
            call.message.message_id
        )

    # ==========================
    # USER BUY CLICK
    # ==========================
    elif data == "buy":
        today = get_today_market()

        if not today:
            return

        buy_state[chat_id] = {
            "step": "waiting_payment",
            "price": today["price"],
            "photo": today["photo"],
            "rating": today["rating"]
        }

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ CONFIRM", callback_data="buy_confirm"))

        bot.send_message(chat_id, f"""
💰 Qiimaha: ${today['price']}

📲 Ku dir lacag:
+252907868526

Kadib riix CONFIRM
""", reply_markup=markup)

    # ==========================
    # USER CONFIRM BUY
    # ==========================
    elif data == "buy_confirm":
        state = buy_state.get(chat_id)

        if not state:
            return

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ CONFIRM", callback_data=f"buy_ok_{chat_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"buy_no_{chat_id}")
        )

        bot.send_photo(
            ADMIN_ID,
            state["photo"],
            caption=f"""
🛒 IIBSI

👤 User: {chat_id}
📊 Rating: {state['rating']}
💰 Price: {state['price']}
""",
            reply_markup=markup
        )

        bot.send_message(chat_id, "⏳ Sug xaqijinta admin")
        buy_state.pop(chat_id)

    # ==========================
    # ADMIN APPROVE BUY
    # ==========================
    elif data.startswith("buy_ok_"):
        user_id = int(data.split("_")[2])

        bot.send_message(user_id, "✅ Waa lagu guuleystay iibka! Admin wuu xaqiijiyay")

        bot.edit_message_caption(
            "✅ IIB LA AQBALAY",
            call.message.chat.id,
            call.message.message_id
        )

    # ==========================
    # ADMIN REJECT BUY
    # ==========================
    elif data.startswith("buy_no_"):
        user_id = int(data.split("_")[2])

        bot.send_message(user_id, "❌ Iibka waa la diiday")

        bot.edit_message_caption(
            "❌ IIB LA DIIDAY",
            call.message.chat.id,
            call.message.message_id
        )

# ==============================
# DATABASE COLLECTIONS (NEW)
# ==============================

requests_col = db['requests']   # market requests
buys_col = db['buys']           # buy requests

# ==============================
# SAVE MARKET REQUEST (DB)
# ==============================

def save_market_request(user_id, photo, rating, price):
    return requests_col.insert_one({
        "user_id": user_id,
        "photo": photo,
        "rating": rating,
        "price": price,
        "status": "pending",
        "date": datetime.utcnow()
    }).inserted_id

def get_market_request(req_id):
    return requests_col.find_one({"_id": req_id})

def update_market_status(req_id, status):
    requests_col.update_one({"_id": req_id}, {"$set": {"status": status}})

# ==============================
# SAVE BUY REQUEST (DB)
# ==============================

def save_buy_request(user_id, photo, rating, price):
    return buys_col.insert_one({
        "user_id": user_id,
        "photo": photo,
        "rating": rating,
        "price": price,
        "status": "pending",
        "date": datetime.utcnow()
    }).inserted_id

def get_buy_request(req_id):
    return buys_col.find_one({"_id": req_id})

def update_buy_status(req_id, status):
    buys_col.update_one({"_id": req_id}, {"$set": {"status": status}})

# ==============================
# 🔥 UPDATE PART 1 LOGIC
# ==============================

# BADAL qaybta user_confirm (QAYBTA 1) → this version

@bot.callback_query_handler(func=lambda call: call.data == "user_confirm")
def user_confirm(call):
    chat_id = call.message.chat.id
    data = user_market.get(chat_id)

    if not data:
        return

    # SAVE DB
    req_id = save_market_request(chat_id, data["photo"], data["rating"], data["price"])

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ CONFIRM", callback_data=f"admin_ok_{req_id}"),
        InlineKeyboardButton("❌ REJECT", callback_data=f"admin_no_{req_id}")
    )

    bot.send_photo(
        ADMIN_ID,
        data["photo"],
        caption=f"""
🆕 SHAX SUUQA

👤 User: {chat_id}
📊 Rating: {data['rating']}
💰 Price: {data['price']}
🆔 ReqID: {req_id}
""",
        reply_markup=markup
    )

    bot.send_message(chat_id, "⏳ Sug xaqijin admin")
    user_market.pop(chat_id)

# ==============================
# 🔥 UPDATE PART 2 CALLBACKS
# ==============================

@bot.callback_query_handler(func=lambda call: True)
def callback_final(call):
    data = call.data

    # ==========================
    # ADMIN APPROVE MARKET (DB)
    # ==========================
    if data.startswith("admin_ok_"):
        req_id = data.split("_")[2]

        req = requests_col.find_one({"_id": __import__("bson").ObjectId(req_id)})
        if not req:
            return

        set_today_market(req["photo"], req["rating"], req["price"])
        update_market_status(__import__("bson").ObjectId(req_id), "approved")

        bot.send_message(req["user_id"], "✅ Shaxdaada suuqa waa la geliyay")

        bot.edit_message_caption(
            "✅ LA AQBALAY",
            call.message.chat.id,
            call.message.message_id
        )

    # ==========================
    # ADMIN REJECT MARKET
    # ==========================
    elif data.startswith("admin_no_"):
        req_id = data.split("_")[2]

        req = requests_col.find_one({"_id": __import__("bson").ObjectId(req_id)})
        if not req:
            return

        update_market_status(__import__("bson").ObjectId(req_id), "rejected")

        bot.send_message(req["user_id"], "❌ Codsigaaga waa la diiday")

        bot.edit_message_caption(
            "❌ LA DIIDAY",
            call.message.chat.id,
            call.message.message_id
        )

    # ==========================
    # USER BUY CONFIRM → SAVE DB
    # ==========================
    elif data == "buy_confirm":
        state = buy_state.get(call.message.chat.id)

        if not state:
            return

        req_id = save_buy_request(
            call.message.chat.id,
            state["photo"],
            state["rating"],
            state["price"]
        )

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ CONFIRM", callback_data=f"buy_ok_{req_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"buy_no_{req_id}")
        )

        bot.send_photo(
            ADMIN_ID,
            state["photo"],
            caption=f"""
🛒 IIBSI

👤 User: {call.message.chat.id}
📊 Rating: {state['rating']}
💰 Price: {state['price']}
🆔 BuyID: {req_id}
""",
            reply_markup=markup
        )

        bot.send_message(call.message.chat.id, "⏳ Sug admin")
        buy_state.pop(call.message.chat.id)

    # ==========================
    # ADMIN APPROVE BUY
    # ==========================
    elif data.startswith("buy_ok_"):
        req_id = data.split("_")[2]

        req = buys_col.find_one({"_id": __import__("bson").ObjectId(req_id)})
        if not req:
            return

        update_buy_status(__import__("bson").ObjectId(req_id), "approved")

        bot.send_message(req["user_id"], "✅ Iibka waa la xaqiijiyay 🎉")

        bot.edit_message_caption(
            "✅ IIB LA AQBALAY",
            call.message.chat.id,
            call.message.message_id
        )

    # ==========================
    # ADMIN REJECT BUY
    # ==========================
    elif data.startswith("buy_no_"):
        req_id = data.split("_")[2]

        req = buys_col.find_one({"_id": __import__("bson").ObjectId(req_id)})
        if not req:
            return

        update_buy_status(__import__("bson").ObjectId(req_id), "rejected")

        bot.send_message(req["user_id"], "❌ Iibka waa la diiday")

        bot.edit_message_caption(
            "❌ IIB LA DIIDAY",
            call.message.chat.id,
            call.message.message_id
        )

# ==============================
# FINAL RUN
# ==============================

print("🔥 BOT FULLY RUNNING...")
bot.infinity_polling()
