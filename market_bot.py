import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import os
from pymongo import MongoClient

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

# STATES
admin_state = {}
sell_state = {}
pending_buy = {}

# ======================
# MENUS
# ======================

def main_menu(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 IIBSO", "📤 ISKA IIBI")

    if is_admin:
        markup.add("🛠️ Admin Panel")

    bot.send_message(chat_id, "Dooro 👇", reply_markup=markup)


def admin_panel(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "➕ DHIG SHAX",
        "❌ DELETE SHAXAHA DHAN",
        "📢 BROADCAST",
        "🔙 BACK"
    )
    bot.send_message(chat_id, "🛠️ Admin Panel", reply_markup=markup)

# ======================
# START
# ======================

@bot.message_handler(commands=['start'])
def start(msg):
    is_admin = (msg.from_user.id == ADMIN_ID)
    main_menu(msg.chat.id, is_admin)

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
        caption=f"💰 Price: ${item['price']}\n📄 Page {index+1}/{len(items)}",
        reply_markup=markup
    )

# ======================
# MAIN HANDLER (MUHIIM)
# ======================

@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == "text" else None
    is_admin = (msg.from_user.id == ADMIN_ID)

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
            bot.send_message(chat_id, "📸 Dir sawirka")
            return

        if text == "❌ DELETE SHAXAHA DHAN":
            market_col.delete_many({})
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

    # ========= ADMIN FLOW =========

    state = admin_state.get(chat_id)

    if state:
        if state["step"] == "photo" and msg.content_type == "photo":
            state["photo"] = msg.photo[-1].file_id
            state["step"] = "price"
            bot.send_message(chat_id, "💰 Qor qiimaha")
            return

        if state["step"] == "price" and text:
            market_col.insert_one({
                "photo": state["photo"],
                "price": text
            })

            bot.send_message(chat_id, "✅ Shax waa la dhigay")
            admin_state.pop(chat_id)
            return

    # ========= BUY =========

    if text == "🛒 IIBSO":
        show_market(chat_id, 0)
        return

    # ========= SELL =========

    if text == "📤 ISKA IIBI":
        sell_state[chat_id] = {"step": "media"}
        bot.send_message(chat_id, "📸/🎥 Soo dir sawir ama video")
        return

    # SELL FLOW
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
                bot.send_message(chat_id, "❌ Number sax ah geli")
                return

            state["rating"] = text
            state["step"] = "price"
            bot.send_message(chat_id, "💰 Qor qiimaha")
            return

        if state["step"] == "price":
            state["price"] = text
            state["step"] = "done"

            caption = f"""
📤 CODSI IIBIN

👤 @{msg.from_user.username}
📊 Rating: {state['rating']}
💰 Price: ${state['price']}
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
# PHOTO BUY (MUHIIM FIX)
# ======================

@bot.message_handler(content_types=['photo'])
def photo_buy(msg):
    chat_id = msg.chat.id

    if chat_id in pending_buy:
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
        pending_buy.pop(chat_id)  # muhiim fix
        return

# ======================
# CALLBACKS
# ======================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("next_"):
        show_market(chat_id, int(data.split("_")[1]))
        return

    if data.startswith("buy_"):
        index = int(data.split("_")[1])
        item = list(market_col.find())[index]

        pending_buy[chat_id] = item

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ WAAN DIRAY", callback_data="confirm_buy"))

        bot.send_message(chat_id, f"""
💰 ${item['price']}
📲 {PAY_NUMBER}
""", reply_markup=markup)
        return

    if data == "confirm_buy":
        bot.send_message(chat_id, "📸 Soo dir screenshot")
        return

    # ADMIN BUY
    if data.startswith("buy_ok_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "✅ Lacag waa la xaqiijiyay")
        return

    if data.startswith("buy_no_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "❌ Lacag lama helin")
        return

    # ADMIN SELL
    if data.startswith("sell_ok_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "✅ Shaxda waa la aqbalay")
        return

    if data.startswith("sell_no_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "❌ Codsiga waa la diiday")
        return

# ======================
# RUN
# ======================

print("Market Bot Running...")
