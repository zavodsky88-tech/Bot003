import telebot
from telebot import types
import requests

# ===================== НАСТРОЙКИ =====================
TOKEN = "8542034986:AAHlph-7hJgQn_AxH2PPXhZLUPUKTkztbiI"  # вставь свой токен
ADMIN_ID = 1979125261  # твой Telegram ID для уведомлений

# Ссылка на Google Form (используем POST-запрос)
GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_QdRSLL99UZUfgC3fvRPhiGCmSGKty_eqe-suR43yWDezzA/formResponse"

ENTRY_NUMBER = "entry.2110379223"
ENTRY_NAME = "entry.1234675755"
ENTRY_PHONE = "entry.1260653739"
ENTRY_SERVICE = "entry.490319395"
ENTRY_DATE = "entry.1667947668"
ENTRY_COMMENT = "entry.2029165293"

# ===================== ПЕРЕМЕННЫЕ =====================
user_data = {}  # временно хранит данные пользователя
last_number = 0  # счетчик заявок

bot = telebot.TeleBot(TOKEN)

# ===================== ФУНКЦИИ =====================

def next_request_number():
    global last_number
    last_number += 1
    return f"{last_number:07d}"  # 0000001, 0000002

def send_to_google_form(data):
    payload = {
        ENTRY_NAME: data.get("name", ""),
        ENTRY_PHONE: data.get("phone", ""),
        ENTRY_SERVICE: data.get("service", ""),
        ENTRY_DATE: data.get("date", ""),
        ENTRY_COMMENT: data.get("comment", ""),
        ENTRY_NUMBER: data.get("number", "")
    }
    requests.post(GOOGLE_FORM_URL, data=payload)

# ===================== МЕНЮ =====================

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✨ Подобрать услугу", "💰 Цены")
    markup.add("📅 Записаться", "📍 Контакты")
    markup.add("❓ Помощь")
    bot.send_message(message.chat.id,
                     "💅 Привет! Я помощник салона.\nПомогу записаться 💖",
                     reply_markup=markup)

# ===================== ОБРАБОТКА КНОПОК =====================

@bot.message_handler(func=lambda m: m.text == "💰 Цены")
def prices(message):
    text = "💅 Наши цены:\n\nМаникюр — от 1000 ₽\nСтрижка — от 800 ₽\nБрови — от 500 ₽"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📍 Контакты")
def contacts(message):
    bot.send_message(message.chat.id, "📍 Наш адрес: г. Москва, ул. Примерная, 1\n📞 Телефон: +7 999 999-99-99")

@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_menu(message):
    bot.send_message(message.chat.id, "Вы можете выбрать услугу, посмотреть цены, записаться или узнать контакты салона.")

# ===================== ПОДБОР УСЛУГИ =====================

@bot.message_handler(func=lambda m: m.text == "✨ Подобрать услугу")
def pick_priority(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💨 Быстро", "✨ Эффектно", "💆‍♀️ Уход")
    markup.add("🔙 В меню")
    bot.send_message(message.chat.id, "Что для тебя важнее сегодня?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["💨 Быстро", "✨ Эффектно", "💆‍♀️ Уход"])
def recommend_service(message):
    priority = message.text
    services = {
        "💨 Быстро": ["Экспресс-маникюр (40 мин)"],
        "✨ Эффектно": ["Маникюр + дизайн", "Стрижка + укладка"],
        "💆‍♀️ Уход": ["Маникюр + SPA-уход", "Макияж"]
    }
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in services[priority]:
        markup.add(s)
    markup.add("🔄 Другая опция", "🔙 В меню")
    bot.send_message(message.chat.id, f"✨ Рекомендую:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["🔄 Другая опция", "🔙 В меню"])
def go_back_or_repeat(message):
    if message.text == "🔙 В меню":
        start(message)
    else:
        pick_priority(message)

# ===================== ЗАПИСЬ НА УСЛУГУ =====================

@bot.message_handler(func=lambda m: True)
def ask_info(message):
    text = message.text
    if text not in ["✨ Подобрать услугу", "💰 Цены", "📅 Записаться", "📍 Контакты", "❓ Помощь",
                    "💨 Быстро", "✨ Эффектно", "💆‍♀️ Уход", "🔄 Другая опция", "🔙 В меню"]:
        if "service" not in user_data:
            user_data["service"] = text
            bot.send_message(message.chat.id, "Как тебя зовут?")
        elif "name" not in user_data:
            user_data["name"] = text
            bot.send_message(message.chat.id, "Оставь номер телефона 📞")
        elif "phone" not in user_data:
            user_data["phone"] = text
            bot.send_message(message.chat.id, "На какую дату хочешь записаться? (например: 5 февраля)")
        elif "date" not in user_data:
            user_data["date"] = text
            bot.send_message(message.chat.id, "Если есть комментарий к записи, напиши его. Если нет — отправь '-'")
        elif "comment" not in user_data:
            user_data["comment"] = text
            user_data["number"] = next_request_number()
            # Отправляем в Google Form
            send_to_google_form(user_data)
            # Уведомляем администратора
            bot.send_message(ADMIN_ID,
                             f"🆕 Новая заявка #{user_data['number']}\n"
                             f"{user_data['name']} | {user_data['phone']}\n"
                             f"{user_data['service']} | {user_data['date']}\n"
                             f"Комментарий: {user_data['comment']}")
            bot.send_message(message.chat.id,
                             f"✅ Запись принята! Номер заявки: {user_data['number']}\nАдминистратор скоро свяжется с тобой 💖")
            user_data.clear()  # очищаем данные после записи

# ===================== ЗАПУСК =====================
bot.infinity_polling()
