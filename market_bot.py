import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import os
from pymongo import MongoClient
import re

# ======================
# CONFIG
# ======================

TOKEN = os.getenv("BOT_TOKEN_2")
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8669162116
PAY_NUMBER = "+252907868526"
SUPPORT = "@Manager_efootball_shop"

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['market_bot']

market_col = db['market']
users_col = db['users']

# STATES
admin_state = {}
sell_state = {}
pending_buy = {}
market_request = {}

# ======================
# HELPERS
# ======================

def is_valid_gmail(email):
    return re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email)

def price_validator(rating, price):
    rating = int(rating)
    price = float(price)

    if 3100 <= rating <= 3150:
        return 3 <= price <= 10
    elif 3150 <= rating <= 3200:
        return 5 <= price <= 14
    elif 3200 <= rating <= 3250:
        return 14 <= price <= 25
    elif 3250 <= rating <= 3330:
        return 1 <= price <= 100

    return False

def add_user(user_id):
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id})

def stats_text():
    total_users = users_col.count_documents({})
    total_market = market_col.count_documents({})
    return f"📊 STATS\n👥 Users: {total_users}\n🛒 Shaxyo: {total_market}"

# ======================
# MENUS
# ======================

def main_menu(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 IIBSO", "📤 ISKA IIBI")
    markup.add("📥 SHAX SUUQA DHIGO")

    if is_admin:
        markup.add("🛠️ Admin Panel", "📊 STATS")

    bot.send_message(chat_id, "Dooro 👇", reply_markup=markup)


def admin_panel(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "➕ DHIG SHAX",
        "❌ DELETE SHAXAHA DHAN"
    )
    markup.add(
        "📢 BROADCAST",
        "📊 STATS",
        "🔙 BACK"
    )
    bot.send_message(chat_id, "🛠️ Admin Panel", reply_markup=markup)


# ======================
# START
# ======================

@bot.message_handler(commands=['start'])
def start(msg):
    add_user(msg.from_user.id)
    main_menu(msg.chat.id, msg.from_user.id == ADMIN_ID)


# ======================
# SHOW MARKET
# ======================

def show_market(chat_id, index):
    items = list(market_col.find())

    if not items:
        bot.send_message(chat_id, "❌ Shax ma jiro")
        return

    if index >= len(items):
        index = 0

    item = items[index]

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("➡️ NEXT", callback_data=f"next_{index+1}"),
        InlineKeyboardButton("🛒 IIBSO", callback_data=f"buy_{index}")
    )

    bot.send_photo(
        chat_id,
        item["photo"],
        caption=f"💰 ${item['price']}\n📊 Rating: {item.get('rating','N/A')}\n📄 {index+1}/{len(items)}",
        reply_markup=markup
    )

# ======================
# MAIN HANDLER (PART 1)
# ======================

@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle(msg):
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    text = msg.text if msg.content_type == "text" else None
    is_admin = (user_id == ADMIN_ID)

    add_user(user_id)

    # ========= STATS =========
    if text == "📊 STATS" and is_admin:
        bot.send_message(chat_id, stats_text())
        return

    # ========= BUY SCREENSHOT =========
    if msg.content_type == "photo" and chat_id in pending_buy:
        item = pending_buy[chat_id]

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ CONFIRM", callback_data=f"buy_ok_{chat_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"buy_no_{chat_id}")
        )

        bot.send_photo(
            ADMIN_ID,
            msg.photo[-1].file_id,
            caption=f"🛒 BUY\nUser:{chat_id}\nPrice:${item['price']}",
            reply_markup=markup
        )

        bot.send_message(chat_id, "⏳ Sug admin")
        pending_buy.pop(chat_id)
        return

    # ========= ADMIN =========
    # ========= ADMIN =========
    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel(chat_id)
        return

    if is_admin:
        if text == "🔙 BACK":
            main_menu(chat_id, True)
            return

        if text == "➕ DHIG SHAX":
            admin_state[chat_id] = {"step": "photo"}
            bot.send_message(chat_id, "📸 Dir sawir")
            return

        if text == "❌ DELETE SHAXAHA DHAN":
            market_col.delete_many({})
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

        if text == "📢 BROADCAST":
            admin_state[chat_id] = {"step": "broadcast"}
            bot.send_message(chat_id, "Qor fariinta:")
            return

    # ========= BROADCAST =========
    if chat_id in admin_state and admin_state[chat_id]["step"] == "broadcast":
        users = users_col.find()
        for u in users:
            try:
                bot.send_message(u["user_id"], text)
            except:
                pass

        bot.send_message(chat_id, "✅ Broadcast waa la diray")
        admin_state.pop(chat_id)
        return

    # ========= ADMIN ADD SHAX (FIXED + LIMIT 10) =========
    state = admin_state.get(chat_id)

    if state:

        # STEP 1: PHOTO
        if state["step"] == "photo":
            if msg.content_type != "photo":
                bot.send_message(chat_id, "❌ Fadlan sawir soo dir")
                return

            # LIMIT 10 SHAX
            total = market_col.count_documents({})
            if total >= 10:
                bot.send_message(chat_id, "❌ Waxaad gaartay limit-ka 10 shax")
                admin_state.pop(chat_id)
                return

            state["photo"] = msg.photo[-1].file_id
            state["step"] = "price"
            bot.send_message(chat_id, "💰 Qor qiimaha")
            return

        # STEP 2: PRICE
        if state["step"] == "price":
            if not text:
                bot.send_message(chat_id, "❌ Qiime geli")
                return

            try:
                float(text)
            except:
                bot.send_message(chat_id, "❌ Qiime sax ah geli")
                return

            market_col.insert_one({
                "photo": state["photo"],
                "price": text
            })

            bot.send_message(chat_id, "✅ Shax waa la dhigay suuqa")
            admin_state.pop(chat_id)
            return

    # ========= BUY =========
    if text == "🛒 IIBSO":
        show_market(chat_id, 0)
        return

    # ========= MARKET REQUEST =========
    if text == "📥 SHAX SUUQA DHIGO":
        market_request[chat_id] = {"step": "photo"}
        bot.send_message(chat_id, "📸 Dir sawirka shaxda")
        return

    state = market_request.get(chat_id)

    if state:

        if state["step"] == "photo":
            if msg.content_type != "photo":
                return
            state["photo"] = msg.photo[-1].file_id
            state["step"] = "rating"
            bot.send_message(chat_id, "📊 Qor rating")
            return

        if state["step"] == "rating":
            if not text or not text.isdigit():
                bot.send_message(chat_id, "❌ Rating sax geli")
                return
            state["rating"] = text
            state["step"] = "price"
            bot.send_message(chat_id, "💰 Qor qiimaha")
            return

        if state["step"] == "price":
            if not text:
                return

            if not price_validator(state["rating"], text):
                bot.send_message(chat_id, "❌ Qiimaha kuma haboona rating-ka")
                return

            state["price"] = text
            state["step"] = "pay"

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ CONFIRM", callback_data=f"market_pay_{chat_id}"))

            bot.send_message(
                chat_id,
                f"💳 Dir $0.1 → {PAY_NUMBER}\nKadib riix CONFIRM",
                reply_markup=markup
            )
            return

# ========= SELL =========
    if text == "📤 ISKA IIBI":
        sell_state[chat_id] = {"step": "media"}
        bot.send_message(chat_id, "📸/🎥 Soo dir sawir ama video")
        return

    state = sell_state.get(chat_id)

    if state:

        if state["step"] == "media":
            if msg.content_type == "photo":
                state["media"] = msg.photo[-1].file_id
                state["type"] = "photo"
            elif msg.content_type == "video":
                state["media"] = msg.video.file_id
                state["type"] = "video"
            else:
                return

            state["step"] = "rating"
            bot.send_message(chat_id, "📊 Qor rating")
            return

        if state["step"] == "rating":
            if not text or not text.isdigit():
                bot.send_message(chat_id, "❌ Rating sax geli")
                return

            state["rating"] = text
            state["step"] = "price"
            bot.send_message(chat_id, "💰 Qor qiimaha")
            return

        if state["step"] == "price":
            if not price_validator(state["rating"], text):
                bot.send_message(chat_id, "❌ Qiimaha kuma haboona rating-ka")
                return

            state["price"] = text
            state["step"] = "gmail"
            bot.send_message(chat_id, "📧 Qor Gmail (example@gmail.com)")
            return

        if state["step"] == "gmail":
            if not is_valid_gmail(text):
                bot.send_message(chat_id, "❌ Gmail sax geli (example@gmail.com)")
                return

            state["gmail"] = text
            state["step"] = "password"
            bot.send_message(chat_id, "🔑 Qor Password")
            return

        if state["step"] == "password":
            state["password"] = text
            state["step"] = "number"
            bot.send_message(chat_id, "📲 Qor number lacag")
            return

        if state["step"] == "number":
            state["number"] = text

            caption = f"""
📤 CODSI IIBIN

👤 @{msg.from_user.username}
📊 Rating: {state['rating']}
💰 Price: ${state['price']}
📧 {state['gmail']}
🔑 {state['password']}
📲 {state['number']}
🆔 {chat_id}
"""

            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ CONFIRM", callback_data=f"sell_ok_{chat_id}"),
                InlineKeyboardButton("❌ REJECT", callback_data=f"sell_no_{chat_id}")
            )

            if state["type"] == "photo":
                bot.send_photo(ADMIN_ID, state["media"], caption=caption, reply_markup=markup)
            else:
                bot.send_video(ADMIN_ID, state["media"], caption=caption, reply_markup=markup)

            bot.send_message(chat_id, "⏳ Sug admin...")
            sell_state.pop(chat_id)
            return


# ======================
# CALLBACKS
# ======================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    # ========= NEXT =========
    if data.startswith("next_"):
        show_market(chat_id, int(data.split("_")[1]))
        return

    # ========= BUY =========
    if data.startswith("buy_"):
        index = int(data.split("_")[1])
        item = list(market_col.find())[index]

        pending_buy[chat_id] = item

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ CONFIRM", callback_data="confirm_buy"))

        bot.send_message(chat_id, f"💰 ${item['price']}\n📲 {PAY_NUMBER}", reply_markup=markup)
        return

    if data == "confirm_buy":
        bot.send_message(chat_id, "📸 Soo dir screenshot")
        return

    # ========= ADMIN BUY =========
    if data.startswith("buy_ok_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "✅ Lacag waa la xaqiijiyay")
        return

    if data.startswith("buy_no_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "❌ Lacag lama helin")
        return

    # ========= SELL APPROVE =========
    if data.startswith("sell_ok_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "✅ Waa la aqbalay")
        return

    if data.startswith("sell_no_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "❌ Waa la diiday")
        return

    # ========= MARKET PAYMENT CONFIRM =========
    if data.startswith("market_pay_"):
        uid = int(data.split("_")[2])
        req = market_request.get(uid)

        if not req:
            return

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ APPROVE", callback_data=f"market_ok_{uid}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"market_no_{uid}")
        )

        bot.send_photo(
            ADMIN_ID,
            req["photo"],
            caption=f"""
📥 SUUQ GALIN CODSI

User: {uid}
📊 Rating: {req['rating']}
💰 Price: ${req['price']}
""",
            reply_markup=markup
        )

        bot.send_message(uid, "⏳ Sug admin...")
        return

    # ========= ADMIN MARKET APPROVE =========
    if data.startswith("market_ok_"):
        uid = int(data.split("_")[2])
        req = market_request.get(uid)

        if not req:
            return

        # ku dar market
        market_col.insert_one({
            "photo": req["photo"],
            "price": req["price"],
            "rating": req["rating"]
        })

        bot.send_message(uid, "✅ Shaxda suuqa waa la geliyay")
        market_request.pop(uid)
        return

    if data.startswith("market_no_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "❌ Codsiga waa la diiday")
        market_request.pop(uid)
        return


# ======================
# RUN
# ======================

print("Market Bot Running...")
