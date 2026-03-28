import telebot
from telebot.types import ReplyKeyboardMarkup
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
            "invited": 0,
            "date": datetime.utcnow().date().isoformat()
        })

def get_user(chat_id):
    return users_col.find_one({"chat_id": chat_id})

# ==============================
# FREE SHAX
# ==============================
def set_free(photo, rating):
    free_col.delete_many({})
    free_col.insert_one({"photo": photo, "rating": rating})

def get_free():
    return free_col.find_one() or {}

def delete_free():
    free_col.delete_many({})

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
# START
# ==============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    username = msg.from_user.username
    is_admin = (msg.from_user.id == ADMIN_ID)

    add_user(chat_id, username)
    user = get_user(chat_id)

    args = msg.text.split()
    if len(args) > 1:
        try:
            ref = int(args[1])
            owner = users_col.find_one({"ref": ref})
            if owner and owner["chat_id"] != chat_id:
    users_col.update_one({"ref": ref}, {"$inc": {"invited": 1}})

    # soo qaado user-ka updated
    updated_user = users_col.find_one({"ref": ref})

    invited = updated_user.get("invited", 0)

    # marka uu gaaro 20
    if invited == 20:
        try:
            bot.send_message(owner["chat_id"], """
🎉 Hambalyo!

Waxaad gaartay heerkii aad ku qaadan lahayd SHAX FREE 🆓

📩 Fadlan nala soo xiriir:
@Manager_efootball_shop
""")
        except:
            pass

    bot.reply_to(msg, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")
    main_menu(chat_id, is_admin)

# ==============================
# MENUS
# ==============================
def main_menu(chat_id, is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📈 Shaxda Suuqa Maanta", "🎁 SHAXAHA FREE")
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
# HANDLER
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

    # ADMIN PANEL
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

        if text == "🔍 Checker":
            bot.send_message(chat_id, "Gali ref number:")
            admin_state[chat_id] = "check"
            return

        if text == "🎁 Add Free Shax":
            bot.send_message(chat_id, "Dir sawir:")
            admin_state[chat_id] = "free_photo"
            return

        if text == "❌ Delete Free Shax":
            delete_free()
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

        if text == "Gali Shax Cusub":
            bot.send_message(chat_id, "Dir sawirka:")
            admin_state[chat_id] = "market_photo"
            return

        if text == "Delete Shaxda Maanta":
            reset_today_market()
            bot.send_message(chat_id, "✅ Waa la tirtiray")
            return

        if text == "Broadcast Text":
            bot.send_message(chat_id, "Qor fariin:")
            admin_state[chat_id] = "text"
            return

        if text == "Broadcast Photo":
            bot.send_message(chat_id, "Dir sawir:")
            admin_state[chat_id] = "photo"
            return

        if text == "Broadcast Video":
            bot.send_message(chat_id, "Dir video:")
            admin_state[chat_id] = "video"
            return

    # STATES
    state = admin_state.get(chat_id)

    if state == "check":
        try:
            ref = int(msg.text)
            u = users_col.find_one({"ref": ref})
            if u:
                bot.send_message(chat_id,
                    f"👤 @{u.get('username')}\n👥 Invited: {u.get('invited',0)}")
            else:
                bot.send_message(chat_id, "❌ lama helin")
        except:
            bot.send_message(chat_id, "❌ Error")
        admin_state.pop(chat_id)
        return

    if state == "free_photo" and msg.content_type == "photo":
        admin_state["photo"] = msg.photo[-1].file_id
        admin_state[chat_id] = "free_rating"
        bot.send_message(chat_id, "Qor rating:")
        return

    if state == "free_rating":
        set_free(admin_state["photo"], int(msg.text))
        bot.send_message(chat_id, "✅ Free shax waa la dhigay")
        admin_state.pop(chat_id)
        return

    if state == "market_photo" and msg.content_type == "photo":
        admin_state["m_photo"] = msg.photo[-1].file_id
        admin_state[chat_id] = "market_rating"
        bot.send_message(chat_id, "Qor rating:")
        return

    if state == "market_rating":
        admin_state["m_rating"] = int(msg.text)
        admin_state[chat_id] = "market_price"
        bot.send_message(chat_id, "Qor price:")
        return

    if state == "market_price":
        set_today_market(
            admin_state["m_photo"],
            admin_state["m_rating"],
            int(msg.text)
        )
        bot.send_message(chat_id, "✅ Suuqa waa la dhigay")
        admin_state.pop(chat_id)
        return

    if state in ["text","photo","video"]:
        for u in get_all_users():
            try:
                if state == "text":
                    bot.send_message(u, msg.text)
                elif state == "photo":
                    bot.send_photo(u, msg.photo[-1].file_id)
                elif state == "video":
                    bot.send_video(u, msg.video.file_id)
            except:
                pass
        bot.send_message(chat_id, "✅ Broadcast Done")
        admin_state.pop(chat_id)
        return

    # USER FEATURES
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
                caption=f"📊 Rating: {today['rating']}\n💰 Price: ${today['price']}")
        else:
            bot.send_message(chat_id, "❌ Wali lama dhigin")
        return

    # USER RATING
    if chat_id in admin_state:
        return

    if msg.content_type == "photo":
        manual_ratings[chat_id] = True
        bot.reply_to(msg, "📊 Fadlan qor rating-ka:")
        return

    if chat_id in manual_ratings and msg.content_type == "text":

        if not text or not text.isdigit():
            bot.send_message(chat_id, "❌ Fadlan number sax ah geli")
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
        return

# ==============================
# RUN
# ==============================
print("Bot running...")
bot.infinity_polling()
