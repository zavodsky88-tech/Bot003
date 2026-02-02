import logging
import os
import re
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= НАСТРОЙКИ =================
TOKEN = "8542034986:AAHlph-7hJgQn_AxH2PPXhZLUPUKTkztbiI"
ADMIN_ID = 1979125261
GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_QdRSLL99UZUfgC3fvRPhiGCmSGKty_eqe-suR43yWDezzA/formResponse"

FORM_FIELDS = {
    "name": "entry.2110379223",
    "phone": "entry.1234675755",
    "service": "entry.1260653739",
    "date": "entry.490319395",
    "comment": "entry.1667947668",
    # Можно добавить ещё поля, если нужно
    "order_id": "entry.2029165293"
}

def send_to_google_form(data: dict):
    """
    Отправляет данные пользователя в Google Form
    """
    payload = {
        FORM_FIELDS["name"]: data.get("name", "-"),
        FORM_FIELDS["phone"]: data.get("phone", "-"),
        FORM_FIELDS["service"]: data.get("service", "-"),
        FORM_FIELDS["date"]: data.get("date", "-"),
        FORM_FIELDS["comment"]: data.get("comment", "-"),
        FORM_FIELDS["order_id"]: data.get("order_id", "-")
    }

    try:
        response = requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)
        if response.status_code == 200:
            logging.info("Заявка успешно отправлена в Google Form")
        else:
            logging.error("Ошибка при отправке в Google Form: %s", response.status_code)
    except requests.exceptions.RequestException as e:
        logging.error("Ошибка при соединении с Google Form: %s", e)

ID_FILE = "order_id.txt"

# ================= ЛОГИ =================
logging.basicConfig(level=logging.INFO)

# ================= КНОПКИ =================
MAIN = ReplyKeyboardMarkup(
    [["✨ Подобрать услугу", "📅 Записаться"],
     ["💰 Цены", "📍 Контакты"],
     ["❓ Помощь"]],
    resize_keyboard=True
)

CATEGORIES = ReplyKeyboardMarkup(
    [["💨 Быстро", "💆‍♀️ Уход"],
     ["✨ Эффектно"],
     ["📋 Показать все услуги"],
     ["🔙 Назад"]],
    resize_keyboard=True
)

FAST = ReplyKeyboardMarkup(
    [["💅 Маникюр экспресс"],
     ["🎨 Снятие + покрытие"],
     ["🔙 Назад"]],
    resize_keyboard=True
)

CARE = ReplyKeyboardMarkup(
    [["💆‍♀️ Маникюр + SPA-уход"],
     ["🫧 Парафинотерапия"],
     ["🔙 Назад"]],
    resize_keyboard=True
)

EFFECT = ReplyKeyboardMarkup(
    [["✨ Маникюр + дизайн"],
     ["💎 Авторский дизайн"],
     ["🔙 Назад"]],
    resize_keyboard=True
)

UPSELL = ReplyKeyboardMarkup(
    [["➕ Добавить дизайн"],
     ["➕ Добавить уход"],
     ["❌ Без допов"]],
    resize_keyboard=True
)

# ================= УТИЛИТЫ =================
def next_order_id():
    if not os.path.exists(ID_FILE):
        with open(ID_FILE, "w") as f:
            f.write("0")
    with open(ID_FILE, "r+") as f:
        last = int(f.read())
        new = last + 1
        f.seek(0)
        f.write(str(new))
        f.truncate()
    return str(new).zfill(7)

def is_phone(text: str) -> bool:
    return bool(re.fullmatch(r"\+?\d{10,15}", text))

def send_to_google_form(data: dict):
    payload = {FORM_FIELDS[k]: data[k] for k in FORM_FIELDS}
    try:
        requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)
    except Exception as e:
        logging.error(f"Ошибка отправки формы: {e}")

def upsell_text(service: str) -> str:
    if "дизайн" not in service.lower():
        return "💎 Хочешь добавить дизайн? Маникюр будет выглядеть эффектнее ✨"
    return "🫧 Добавим уход? Кожа станет мягче и результат продержится дольше 💖"

# ================= ХЭНДЛЕР =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    # --- Главное меню ---
    if text in ["💰 Цены", "📍 Контакты", "❓ Помощь", "✨ Подобрать услугу", "📅 Записаться", "📋 Показать все услуги", "🔙 Назад"]:
        user_data.clear()
        if text == "💰 Цены":
            await update.message.reply_text(
                "💅 Маникюр — от 1500₽\n✨ Маникюр + дизайн — от 2000₽\n💆‍♀️ SPA-уход — от 800₽",
                reply_markup=MAIN
            )
        elif text == "📍 Контакты":
            await update.message.reply_text(
                "📍 Мы находимся:\nг. Москва, ул. Примерная, 12\n📞 +7 999 123-45-67\n🕒 10:00-21:00",
                reply_markup=MAIN
            )
        elif text == "❓ Помощь":
            await update.message.reply_text(
                "❓ Я могу помочь:\n• Подобрать услугу\n• Записать к мастеру\n• Рассказать цены\n• Передать заявку админу",
                reply_markup=MAIN
            )
        else:
            await update.message.reply_text("Выбери категорию 👇", reply_markup=CATEGORIES)
        return

    # --- Категории ---
    if text in ["💨 Быстро", "💆‍♀️ Уход", "✨ Эффектно"]:
        user_data["category"] = text
        if text == "💨 Быстро":
            await update.message.reply_text("Быстрые услуги ⚡", reply_markup=FAST)
        elif text == "💆‍♀️ Уход":
            await update.message.reply_text("Уходовые процедуры 💖", reply_markup=CARE)
        elif text == "✨ Эффектно":
            await update.message.reply_text("Эффектные услуги ✨", reply_markup=EFFECT)
        return

    # --- Выбор услуги ---
    if "service" not in user_data and any(word in text for word in ["Маникюр", "Снятие", "Парафино", "дизайн"]):
        user_data["service"] = text
        await update.message.reply_text(upsell_text(text), reply_markup=UPSELL)
        user_data["awaiting_upsell"] = True
        return

    # --- Апселл ---
    if user_data.get("awaiting_upsell"):
        if text in ["➕ Добавить дизайн", "➕ Добавить уход"]:
            user_data["service"] += f" + {text.replace('➕ ', '')}"
        user_data.pop("awaiting_upsell")
        await update.message.reply_text("Как тебя зовут?")
        return

    # --- Имя ---
    if "name" not in user_data:
        user_data["name"] = text
        await update.message.reply_text("Оставь номер телефона 📞\nФормат: +79991234567")
        return

    # --- Телефон ---
    if "phone" not in user_data:
        if not is_phone(text):
            await update.message.reply_text("❌ Номер некорректный. Попробуй ещё раз")
            return
        user_data["phone"] = text
        await update.message.reply_text("На какую дату хочешь записаться? (например: 5 февраля)")
        return

    # --- Дата ---
    if "date" not in user_data:
        user_data["date"] = text
        await update.message.reply_text("Комментарий к записи? Если нет — отправь '-'")
        return

    # --- Комментарий / финал ---
    if "comment" not in user_data:
        user_data["comment"] = text
        order_id = next_order_id()
        user_data["order_id"] = order_id

        send_to_google_form(user_data)

        # Ответ пользователю
        await update.message.reply_text(
            f"🆕 Заявка #{order_id}\n"
            f"{user_data['name']} | {user_data['phone']}\n"
            f"{user_data['service']}\n"
            f"Дата: {user_data['date']}\n"
            f"Комментарий: {user_data['comment']}\n\n"
            "✅ Запись принята! Администратор скоро свяжется 💖",
            reply_markup=MAIN
        )

        # Уведомление админу
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 Заявка #{order_id}\n{user_data}")

        user_data.clear()

# ================= ОБРАБОТЧИКИ СТАТИЧЕСКИХ РАЗДЕЛОВ И КАТЕГОРИЙ =================
async def handle_static_sections(update, context, text):
    if text == "💰 Цены":
        await update.message.reply_text(
            "💰 Прайс-лист:\n💅 Маникюр — от 1500₽\n✨ Маникюр + дизайн — от 2000₽\n💆‍♀️ SPA-уход — от 800₽",
            reply_markup=MAIN)
    elif text == "📍 Контакты":
        await update.message.reply_text("📍 Москва, ул. Примерная, 12\n📞 +7 999 123-45-67\n🕒 10:00-21:00", reply_markup=MAIN)
    elif text == "❓ Помощь":
        await update.message.reply_text("Помощь:\n• Подобрать услугу\n• Записать к мастеру\n• Передать заявку", reply_markup=MAIN)
    elif text in ["📅 Записаться", "✨ Подобрать услугу", "📋 Показать все услуги"]:
        await update.message.reply_text("Выбери категорию 👇", reply_markup=CATEGORIES)
    elif text == "🔙 Назад":
        await update.message.reply_text("Главное меню", reply_markup=MAIN)

async def handle_categories(update, context, text):
    if text == "💨 Быстро":
        await update.message.reply_text("Быстрые услуги ⚡", reply_markup=FAST)
    elif text == "💆‍♀️ Уход":
        await update.message.reply_text("Уходовые процедуры 💖", reply_markup=CARE)
    elif text == "✨ Эффектно":
        await update.message.reply_text("Эффектные услуги ✨", reply_markup=EFFECT)

# ================= ЗАПУСК =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
