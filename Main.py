import telebot
from telebot.types import ReplyKeyboardMarkup
import random
from pymongo import MongoClient
from datetime import datetime

# ==============================
# CONFIG
# ==============================
TOKEN = "PUT_YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # PUT YOUR TELEGRAM ID
MONGO_URI = "PUT_YOUR_MONGO_URI"

bot = telebot.TeleBot(TOKEN)

WHATSAPP_LINK = "https://chat.whatsapp.com/Ka7EPQNrU6oG844VjiHek9?mode=gi_t"
BOT_LINK = "https://t.me/Efootball_seller_bot?start="

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
        "❌ Delete Free Shax"
    )
    markup.add(
        "🔍 Checker",
        "Broadcast Text",
        "Broadcast Photo",
        "Broadcast Video"
    )
    markup.add("⬅️ Back")
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
    user = get_user(chat_id)

    args = msg.text.split()
    if len(args) > 1:
        try:
            ref = int(args[1])
            owner = users_col.find_one({"ref": ref})
            if owner and owner["chat_id"] != chat_id:
                users_col.update_one({"ref": ref}, {"$inc": {"invited": 1}})
        except:
            pass

    bot.send_message(chat_id, "👋 Soo dir sawirka shaxda eFootball si loo qiimeeyo 💰")
    main_menu(chat_id, is_admin)

# ==============================
# HANDLER
# ==============================
@bot.message_handler(func=lambda m: True, content_types=['text','photo','video'])
def handle(msg):
    chat_id = msg.chat.id
    text = msg.text if msg.content_type == 'text' else None
    is_admin = (msg.from_user.id == ADMIN_ID)

    add_user(chat_id, msg.from_user.username)
    user = get_user(chat_id)

    # USER RATING
    if msg.content_type == "photo":
        manual_ratings[chat_id] = True
        bot.reply_to(msg, "Qor rating:")
        return

    if msg.content_type == "text" and chat_id in manual_ratings:
        if not text.isdigit():
            bot.send_message(chat_id, "❌ Geli number sax ah")
            return

        rating = int(text)
        price = get_price(rating)

        bot.send_message(chat_id,
f"""🔥 QIIMEYN DHAMEYSTIRAN

📊 Rating: {rating}
💰 Qiimaha: ${price}

📢 Ka iibso:
{WHATSAPP_LINK}
""")
        manual_ratings.pop(chat_id)
        return

    # ADMIN PANEL
    if text == "🛠️ Admin Panel" and is_admin:
        admin_panel(chat_id)
        return

    if text == "⬅️ Back":
        main_menu(chat_id, is_admin)
        return

    # ADMIN ACTIONS
    if is_admin:
        if text == "📊 Stats":
            bot.send_message(chat_id, f"Users: {get_total_users()}\nToday: {get_today_users()}")
            return

        if text == "❌ Delete Free Shax":
            delete_free()
            bot.send_message(chat_id, "Deleted")
            return

    # USER FEATURES
    if text == "🎁 SHAXAHA FREE":
        data = get_free()
        if not data:
            bot.send_message(chat_id, "❌ Free ma jiro")
            return

        bot.send_photo(chat_id, data["photo"],
                       caption=f"Rating: {data['rating']}\nLink:\n{BOT_LINK}{user['ref']}")
        return

    if text == "📈 Shaxda Suuqa Maanta":
        data = get_today_market()
        if "photo_file_id" in data:
            bot.send_photo(chat_id, data['photo_file_id'],
                           caption=f"Rating: {data['rating']}\nPrice: ${data['price']}")
        else:
            bot.send_message(chat_id, "❌ lama dhigin")
        return

# ==============================
# RUN
# ==============================
print("Bot running...")
bot.infinity_polling()
