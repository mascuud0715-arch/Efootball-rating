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

WHATSAPP_LINK = "https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t"
ADMIN_ID = 8669162116
BOT_LINK = "https://t.me/Efootball_seller_bot?start="

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['efb_bot']

users_col = db['users']
market_col = db['market']
free_col = db['free']

manual_ratings = {}
admin_state = {}

# 🔥 NEW STORAGE
user_market = {}
pending_requests = {}
buy_requests = {}

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

def add_user(chat_id, username=None, invited_by=None):
    if not users_col.find_one({"chat_id": chat_id}):
        free = get_free()
        users_col.insert_one({
            "chat_id": chat_id,
            "username": username,
            "ref": generate_ref(),
            "invited": 0,
            "invited_by": invited_by,
            "round": free.get("round", 1),
            "date": datetime.utcnow().date().isoformat()
        })

def get_user(chat_id):
    return users_col.find_one({"chat_id": chat_id})

# ==============================
# FREE SHAX
# ==============================

def set_free(photo, rating):
    free_col.delete_many({})
    last = free_col.find_one(sort=[("round", -1)])
    new_round = (last["round"] + 1) if last else 1

    free_col.insert_one({
        "photo": photo,
        "rating": rating,
        "round": new_round
    })

    users_col.update_many({}, {"$set": {"invited": 0}})

def get_free():
    return free_col.find_one() or {}

def delete_free():
    free_col.delete_many({})
    users_col.update_many({}, {"$set": {"invited": 0}})

# ==============================
# MARKET
# ==============================

def get_today_market():
    return market_col.find_one({"today": True}) or {}

def set_today_market(photo, rating, price):
    market_col.update_one(
        {"today": True},
        {"$set": {
            "photo_file_id": photo,
            "rating": rating,
            "price": price,
            "today": True
        }},
        upsert=True
    )

def reset_today_market():
    market_col.delete_many({"today": True})

# ==============================
# HELPERS
# ==============================

def get_total_users():
    return users_col.count_documents({})

def get_today_users():
    today = datetime.utcnow().date().isoformat()
    return users_col.count_documents({"date": today})

def get_all_users():
    return [u['chat_id'] for u in users_col.find()]

# ==============================
# MENUS
# ==============================

def main_menu(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📈 Shaxda Suuqa Maanta", "🎁 SHAXAHA FREE")
    markup.add("🛒 SHAX DHIGO SUUQA", "🛍️ IIBSO")

    if is_admin:
        markup.add("🛠️ Admin Panel")

    bot.send_message(chat_id, "Dooro option 👇", reply_markup=markup)

def admin_panel(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "📊 Stats",
        "Gali Shax Cusub",
        "Delete Shaxda Maanta",
        "🎁 Add Free Shax",
        "❌ Delete Free Shax",
        "🔍 Checker",
        "Broadcast Text",
        "Broadcast Photo",
        "Broadcast Video",
        "Back"
    )
    bot.send_message(chat_id, "🛠️ Admin Panel", reply_markup=markup)

# ==============================
# START
# ==============================

@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    username = msg.from_user.username
    is_admin = (msg.from_user.id == ADMIN_ID)

    add_user(chat_id, username)
    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")
    main_menu(chat_id, is_admin)

# ==============================
# HANDLER (IMPORTANT FIX)
# ==============================

@bot.message_handler(func=lambda m: True, content_types=['text','photo','video'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == 'text' else None
    is_admin = (msg.from_user.id == ADMIN_ID)

    user = get_user(chat_id)
    if not user:
        add_user(chat_id)
        user = get_user(chat_id)

    # ==============================
    # ADMIN PANEL (🔥 FIXED)
    # ==============================

    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel(chat_id)
        return

    if is_admin:

        if text == "Back":
            main_menu(chat_id, True)
            return

        if text == "📊 Stats":
            bot.send_message(chat_id,
                f"👥 Total: {get_total_users()}\n🆕 Today: {get_today_users()}")
            return

        if text == "❌ Delete Free Shax":
            delete_free()
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

        if text == "Delete Shaxda Maanta":
            reset_today_market()
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

        if text == "🎁 Add Free Shax":
            bot.send_message(chat_id, "Dir sawir free shax")
            admin_state[chat_id] = "free_photo"
            return

        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "Dir sawir market")
            admin_state[chat_id] = "market_photo"
            return

        if text == "Broadcast Text":
            bot.send_message(chat_id, "Qor fariinta")
            admin_state[chat_id] = "broadcast_text"
            return

        if text == "Broadcast Photo":
            bot.send_message(chat_id, "Dir sawirka")
            admin_state[chat_id] = "broadcast_photo"
            return

        if text == "Broadcast Video":
            bot.send_message(chat_id, "Dir video")
            admin_state[chat_id] = "broadcast_video"
            return

        if text == "🔍 Checker":
            bot.send_message(chat_id, "Gali ref")
            admin_state[chat_id] = "checker"
            return

# ==============================
    # SELL SHAX SYSTEM
    # ==============================

    if text == "🛒 SHAX DHIGO SUUQA":
        user_market[chat_id] = {"step": "photo"}
        bot.send_message(chat_id, "📸 Soo dir sawirka shaxda")
        return

    state_u = user_market.get(chat_id)

    # PHOTO
    if state_u and state_u["step"] == "photo" and msg.content_type == "photo":
        user_market[chat_id]["photo"] = msg.photo[-1].file_id
        user_market[chat_id]["step"] = "rating"
        bot.send_message(chat_id, "📊 Qor rating-ka")
        return

    # RATING
    if state_u and state_u["step"] == "rating":
        if not text or not text.isdigit():
            bot.send_message(chat_id, "❌ Number sax ah geli")
            return

        rating = int(text)
        user_market[chat_id]["rating"] = rating
        user_market[chat_id]["step"] = "price"

        bot.send_message(chat_id, "💰 Qor qiimaha")
        return

    # PRICE
    if state_u and state_u["step"] == "price":
        if not text or not text.isdigit():
            bot.send_message(chat_id, "❌ Number sax ah geli")
            return

        price = int(text)
        rating = user_market[chat_id]["rating"]

        user_market[chat_id]["price"] = price
        user_market[chat_id]["step"] = "pay"

        # 🔥 INLINE BUTTON
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ WAAN DIRAY", callback_data="paid_sell"))

        bot.send_message(chat_id, f"""
📊 Rating: {rating}
💰 Price: ${price}

📲 Ku dir $0.1:
+252907868526
""", reply_markup=markup)
        return


    # ==============================
    # BUY SYSTEM
    # ==============================

    if text == "🛍️ IIBSO":
        today = get_today_market()

        if "photo_file_id" not in today:
            bot.send_message(chat_id, "❌ Shax lama hayo")
            return

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 CONFIRM IIB", callback_data="buy_confirm"))

        bot.send_photo(
            chat_id,
            today['photo_file_id'],
            caption=f"""
📊 Rating: {today['rating']}
💰 Price: ${today['price']}

📲 Ku dir lacag:
+252907868526
""",
            reply_markup=markup
        )
        return


    # ==============================
    # ADMIN STATE HANDLING
    # ==============================

    if chat_id in admin_state:

        # ADD FREE SHAX
        if admin_state[chat_id] == "free_photo" and msg.content_type == "photo":
            admin_state[chat_id] = {"step": "free_rating", "photo": msg.photo[-1].file_id}
            bot.send_message(chat_id, "Qor rating free shax")
            return

        if isinstance(admin_state.get(chat_id), dict):
            state = admin_state[chat_id]

            if state.get("step") == "free_rating":
                if not text or not text.isdigit():
                    bot.send_message(chat_id, "Number sax ah geli")
                    return

                set_free(state["photo"], int(text))
                bot.send_message(chat_id, "✅ Free shax waa la geliyay")
                admin_state.pop(chat_id)
                return

        # MARKET ADD
        if admin_state[chat_id] == "market_photo" and msg.content_type == "photo":
            admin_state[chat_id] = {"step": "market_rating", "photo": msg.photo[-1].file_id}
            bot.send_message(chat_id, "Qor rating")
            return

        if isinstance(admin_state.get(chat_id), dict):
            state = admin_state[chat_id]

            if state.get("step") == "market_rating":
                if not text or not text.isdigit():
                    bot.send_message(chat_id, "Number sax ah geli")
                    return

                state["rating"] = int(text)
                state["step"] = "market_price"
                bot.send_message(chat_id, "Qor price")
                return

            if state.get("step") == "market_price":
                if not text or not text.isdigit():
                    bot.send_message(chat_id, "Number sax ah geli")
                    return

                set_today_market(state["photo"], state["rating"], int(text))
                bot.send_message(chat_id, "✅ Market waa la geliyay")
                admin_state.pop(chat_id)
                return

        # BROADCAST TEXT
        if admin_state[chat_id] == "broadcast_text":
            for uid in get_all_users():
                try:
                    bot.send_message(uid, text)
                except:
                    pass

            bot.send_message(chat_id, "✅ Broadcast done")
            admin_state.pop(chat_id)
            return

        # BROADCAST PHOTO
        if admin_state[chat_id] == "broadcast_photo" and msg.content_type == "photo":
            for uid in get_all_users():
                try:
                    bot.send_photo(uid, msg.photo[-1].file_id)
                except:
                    pass

            bot.send_message(chat_id, "✅ Photo sent")
            admin_state.pop(chat_id)
            return

        # BROADCAST VIDEO
        if admin_state[chat_id] == "broadcast_video" and msg.content_type == "video":
            for uid in get_all_users():
                try:
                    bot.send_video(uid, msg.video.file_id)
                except:
                    pass

            bot.send_message(chat_id, "✅ Video sent")
            admin_state.pop(chat_id)
            return

        return

# ==============================
# CALLBACKS (FINAL)
# ==============================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    data = call.data
    chat_id = call.message.chat.id

    # ==============================
    # USER SELL → WAAN DIRAY
    # ==============================

    if data == "paid_sell":
        user_data = user_market.get(chat_id)

        if not user_data:
            bot.answer_callback_query(call.id, "❌ Error")
            return

        bot.send_message(chat_id, "⏳ Sug xaqijinta admin...")

        # SAVE REQUEST
        pending_requests[chat_id] = user_data

        # ADMIN BUTTONS
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ CONFIRM", callback_data=f"approve_{chat_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{chat_id}")
        )

        bot.send_photo(
            ADMIN_ID,
            user_data["photo"],
            caption=f"""
🆕 SHAX SUUQA

👤 User ID: {chat_id}
📊 Rating: {user_data['rating']}
💰 Price: ${user_data['price']}
""",
            reply_markup=markup
        )

        user_market.pop(chat_id)
        bot.answer_callback_query(call.id)
        return


    # ==============================
    # ADMIN → APPROVE SELL
    # ==============================

    if data.startswith("approve_"):
        uid = int(data.split("_")[1])
        req = pending_requests.get(uid)

        if req:
            set_today_market(req["photo"], req["rating"], req["price"])

            bot.send_message(uid,
                "✅ Shaxdaada waa la ansixiyay\n🎉 Waxay hadda taal suuqa")

            pending_requests.pop(uid)

        bot.answer_callback_query(call.id, "Approved")
        return


    # ==============================
    # ADMIN → REJECT SELL
    # ==============================

    if data.startswith("reject_"):
        uid = int(data.split("_")[1])

        if uid in pending_requests:
            bot.send_message(uid, "❌ Codsigaaga waa la diiday")
            pending_requests.pop(uid)

        bot.answer_callback_query(call.id, "Rejected")
        return


    # ==============================
    # USER BUY → CONFIRM
    # ==============================

    if data == "buy_confirm":
        today = get_today_market()

        if not today:
            bot.answer_callback_query(call.id, "❌ Shax ma jiro")
            return

        bot.send_message(chat_id, "⏳ Sug xaqijinta admin...")

        buy_requests[chat_id] = today

        # ADMIN BUTTONS
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ CONFIRM", callback_data=f"buy_ok_{chat_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"buy_no_{chat_id}")
        )

        bot.send_message(
            ADMIN_ID,
            f"""
💰 CODSI IIB

👤 User: {chat_id}
📊 Rating: {today.get('rating')}
💰 Price: ${today.get('price')}
""",
            reply_markup=markup
        )

        bot.answer_callback_query(call.id)
        return


    # ==============================
    # ADMIN → APPROVE BUY
    # ==============================

    if data.startswith("buy_ok_"):
        uid = int(data.split("_")[2])

        if uid in buy_requests:
            bot.send_message(uid, "✅ Iibsigaaga waa la ansixiyay 🎉")
            buy_requests.pop(uid)

        bot.answer_callback_query(call.id, "Approved")
        return


    # ==============================
    # ADMIN → REJECT BUY
    # ==============================

    if data.startswith("buy_no_"):
        uid = int(data.split("_")[2])

        if uid in buy_requests:
            bot.send_message(uid, "❌ Iibsiga waa la diiday")
            buy_requests.pop(uid)

        bot.answer_callback_query(call.id, "Rejected")
        return


# ==============================
# USER FEATURES (FINAL)
# ==============================

@bot.message_handler(func=lambda m: True, content_types=['text'])
def user_features(msg):
    chat_id = msg.chat.id
    text = msg.text

    user = get_user(chat_id)

    if text == "🎁 SHAXAHA FREE":
        data = get_free()

        if not data:
            bot.send_message(chat_id, "❌ Free shax ma jiro")
            return

        bot.send_photo(chat_id, data["photo"],
            caption=f"""🎁 FREE SHAX

📊 Rating: {data['rating']}

🔗 Link:
{BOT_LINK}{user['ref']}

👥 {user['invited']}/20""")
        return


    if text == "📈 Shaxda Suuqa Maanta":
        today = get_today_market()

        if "photo_file_id" in today:
            bot.send_photo(chat_id, today['photo_file_id'],
                caption=f"""📊 Rating: {today['rating']}
💰 Price: ${today['price']}""")
        else:
            bot.send_message(chat_id, "❌ Wali lama dhigin")
        return


# ==============================
# USER RATING SYSTEM
# ==============================

@bot.message_handler(content_types=['photo'])
def rating_photo(msg):
    chat_id = msg.chat.id
    manual_ratings[chat_id] = True
    bot.reply_to(msg, "📊 Fadlan qor rating-ka:")


@bot.message_handler(func=lambda m: m.chat.id in manual_ratings)
def rating_text(msg):
    chat_id = msg.chat.id
    text = msg.text

    if not text or not text.isdigit():
        bot.send_message(chat_id, "❌ Number sax ah geli")
        return

    rating = int(text)
    price = get_price(rating)

    if price == 0:
        bot.send_message(chat_id, "❌ Rating-kan lama qiimeyn karo")
        manual_ratings.pop(chat_id)
        return

    bot.send_message(chat_id, f"""
🔥 QIIMEYN DHAMEYSTIRAN 🔥

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 Ka iibso:
{WHATSAPP_LINK}
""")

    manual_ratings.pop(chat_id)


# ==============================
# RUN
# ==============================

print("Bot running...")
bot.infinity_polling()
