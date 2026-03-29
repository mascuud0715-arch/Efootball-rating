import threading
import main
import marketbot

def run_main():
    main.bot.infinity_polling()

def run_market():
    marketbot.bot.infinity_polling()

t1 = threading.Thread(target=run_main)
t2 = threading.Thread(target=run_market)

t1.start()
t2.start()
