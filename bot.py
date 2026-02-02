import telebot
import requests
import os

# === Telegram ===
#TOKEN = os.getenv("BOT_TOKEN")  # вставляешь свой токен
#ADMIN_ID = int(os.getenv("ADMIN_ID"))  # твой Telegram ID
TOKEN = "8542034986:AAHlph-7hJgQn_AxH2PPXhZLUPUKTkztbiI"  # вставляешь свой токен
ADMIN_ID = 1979125261  # твой Telegram ID

bot = telebot.TeleBot(TOKEN)

# === Google Form ===
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeMNIey07M9Sa8Wotf6UD45EYM05ocIj5oGTOwHEH4kQEbpg/formResponse"

# Здесь твои entry ID
ENTRY_NAME = "entry.1444140936"
ENTRY_PHONE = "entry.404021015"
ENTRY_SERVICE = "entry.913156250"
ENTRY_DATE = "entry.339452627"
ENTRY_NUMBER = "entry.1669580791"

crm = {}
counter = 1

def next_number():
    global counter
    num = str(counter).zfill(6)
    counter += 1
    return num

def send_to_form(data):
    try:
        r = requests.post(FORM_URL, data=data)
        if r.status_code != 200:
            print("Ошибка отправки формы:", r.status_code)
    except Exception as e:
        print("Ошибка:", e)

# === Telegram handlers ===

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(
        m.chat.id,
        "💅 Привет! Я помощник салона.\nПомогу записаться 💖",
        reply_markup=menu()
    )

def menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✨ Подобрать услугу", "📅 Записаться")
    return kb

@bot.message_handler(func=lambda m: m.text == "✨ Подобрать услугу")
def recommend(m):
    bot.send_message(m.chat.id, "Рекомендую: Маникюр + дизайн\nХочешь записаться?")

@bot.message_handler(func=lambda m: m.text == "📅 Записаться")
def ask_name(m):
    crm[m.chat.id] = {}
    bot.send_message(m.chat.id, "Как тебя зовут?")

@bot.message_handler(func=lambda m: m.chat.id in crm and "name" not in crm[m.chat.id])
def get_name(m):
    crm[m.chat.id]["name"] = m.text
    bot.send_message(m.chat.id, "Телефон 📞")

@bot.message_handler(func=lambda m: m.chat.id in crm and "phone" not in crm[m.chat.id])
def get_phone(m):
    crm[m.chat.id]["phone"] = m.text
    bot.send_message(m.chat.id, "Услуга?")

@bot.message_handler(func=lambda m: m.chat.id in crm and "service" not in crm[m.chat.id])
def get_service(m):
    crm[m.chat.id]["service"] = m.text
    bot.send_message(m.chat.id, "Дата?")

@bot.message_handler(func=lambda m: m.chat.id in crm and "date" not in crm[m.chat.id])
def finish(m):
    number = next_number()
    crm[m.chat.id]["date"] = m.text

    data = {
        ENTRY_NAME: crm[m.chat.id]["name"],
        ENTRY_PHONE: crm[m.chat.id]["phone"],
        ENTRY_SERVICE: crm[m.chat.id]["service"],
        ENTRY_DATE: crm[m.chat.id]["date"],
        ENTRY_NUMBER: number
    }

    send_to_form(data)

    bot.send_message(m.chat.id, f"✅ Запись принята! Номер заявки: {number} 💖")
    bot.send_message(
        ADMIN_ID,
        f"🆕 Заявка #{number}\n"
        f"{crm[m.chat.id]['name']} | {crm[m.chat.id]['phone']}\n"
        f"{crm[m.chat.id]['service']} | {crm[m.chat.id]['date']}"
    )

    del crm[m.chat.id]

bot.polling(none_stop=True)
