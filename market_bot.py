import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import os
from pymongo import MongoClient

# ======================
# CONFIG
# ======================

TOKEN = os.getenv("BOT_TOKEN_2")  # muhiim: bot 2 token gaar ah
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
        InlineKeyboardButton("⬅️ ISKA BADAL", callback_data=f"next_{index+1}"),
        InlineKeyboardButton("🛒 IIBSO", callback_data=f"buy_{index}")
    )

    bot.send_photo(
        chat_id,
        item["photo"],
        caption=f"💰 Price: ${item['price']}\n📄 Page {index+1}/{len(items)}",
        reply_markup=markup
    )


# ======================
# MAIN HANDLER
# ======================

@bot.message_handler(content_types=['text'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == "text" else None
    is_admin = (msg.from_user.id == ADMIN_ID)

    # ========= ADMIN PANEL =========

    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel(chat_id)
        return

    if is_admin:

        if text == "🔙 BACK":
            main_menu(chat_id, True)
            return

        if text == "➕ DHIG SHAX":
            admin_state[chat_id] = {"step": "photo"}
            bot.send_message(chat_id, "📸 Dir sawirka shaxda")
            return

        if text == "❌ DELETE SHAXAHA DHAN":
            market_col.delete_many({})
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

        if text == "📢 BROADCAST":
            admin_state[chat_id] = {"step": "broadcast"}
            bot.send_message(chat_id, "Qor fariin:")
            return

    # ========= ADMIN ADD FLOW =========

    state = admin_state.get(chat_id)

    if state:

        if state["step"] == "photo" and msg.content_type == "photo":
            state["photo"] = msg.photo[-1].file_id
            state["step"] = "price"
            bot.send_message(chat_id, "💰 Qor qiimaha")
            return

        if state["step"] == "price" and text:
            state["price"] = text

            market_col.insert_one({
                "photo": state["photo"],
                "price": state["price"]
            })

            bot.send_message(chat_id, "✅ Shax waa la dhigay")
            admin_state.pop(chat_id)
            return

        if state["step"] == "broadcast":
            # haddii aad rabto user system ku dar
            bot.send_message(chat_id, "✅ Broadcast la diray")
            admin_state.pop(chat_id)
            return

    # ========= BUY =========

    if text == "🛒 IIBSO":
        show_market(chat_id, 0)
        return

    # ========= SELL =========

    if text == "📤 ISKA IIBI":
        sell_state[chat_id] = {"step": "media"}
        bot.send_message(chat_id, "📸/🎥 Soo dir sawir ama video shaxdaada")
        return

    # SELL FLOW
    state = sell_state.get(chat_id)

    if state:

        if state["step"] == "rating":
            if not text.isdigit():
                bot.send_message(chat_id, "❌ Number sax ah geli")
                return

            state["rating"] = text
            state["step"] = "price"
            bot.send_message(chat_id, "💰 Qor qiimaha")
            return

        if state["step"] == "price":
            state["price"] = text
            state["step"] = "gmail"
            bot.send_message(chat_id, "📧 Qor Gmail")
            return

        if state["step"] == "gmail":
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

            bot.send_message(chat_id, f"⏳ Sug admin\n{SUPPORT}")
            sell_state.pop(chat_id)
            return


# ========= MEDIA =========

@bot.message_handler(content_types=['photo'])
def photo_handler(msg):
    chat_id = msg.chat.id

    # BUY SCREENSHOT
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
        return

    # SELL MEDIA
    if chat_id in sell_state and sell_state[chat_id]["step"] == "media":
        sell_state[chat_id]["media"] = msg.photo[-1].file_id
        sell_state[chat_id]["type"] = "photo"
        sell_state[chat_id]["step"] = "rating"
        bot.send_message(chat_id, "📊 Qor rating")
        return


@bot.message_handler(content_types=['video'])
def video_handler(msg):
    chat_id = msg.chat.id

    if chat_id in sell_state and sell_state[chat_id]["step"] == "media":
        sell_state[chat_id]["media"] = msg.video.file_id
        sell_state[chat_id]["type"] = "video"
        sell_state[chat_id]["step"] = "rating"
        bot.send_message(chat_id, "📊 Qor rating")


# ======================
# CALLBACKS (HAL MEEL)
# ======================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    # NEXT PAGE
    if data.startswith("next_"):
        index = int(data.split("_")[1])
        show_market(chat_id, index)
        return

    # BUY
    if data.startswith("buy_"):
        index = int(data.split("_")[1])
        items = list(market_col.find())
        item = items[index]

        pending_buy[chat_id] = item

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ CONFIRM", callback_data="confirm_buy"))

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
        bot.send_message(uid, "✅ Waa la xaqiijiyay")
        return

    if data.startswith("buy_no_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "❌ Waa la diiday")
        return

    # ADMIN SELL
    if data.startswith("sell_ok_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "✅ Waa la aqbalay")
        return

    if data.startswith("sell_no_"):
        uid = int(data.split("_")[2])
        bot.send_message(uid, "❌ Waa la diiday")
        return


# ======================
# RUN
# ======================

print("Market Bot Running...")
