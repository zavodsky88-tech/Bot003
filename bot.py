import logging
import os
import re
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= НАСТРОЙКИ =================

TOKEN = "8542034986:AAHlph-7hJgQn_AxH2PPXhZLUPUKTkztbiI"  # токен бота
ADMIN_ID = 1979125261  # твой Telegram ID

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1Qj4hWyDn_fw0YyWYA2Igdr9Fyi5Sn0p4XHdcrdSXlJQ/formResponse"

FORM_FIELDS = {
    "name": "entry.2110379223",
    "phone": "entry.1234675755",
    "service": "entry.1260653739",
    "date": "entry.490319395",
    "comment": "entry.1667947668",
}

ID_FILE = "order_id.txt"

# ================= ЛОГИ =================

logging.basicConfig(level=logging.INFO)

# ================= КНОПКИ =================

MAIN = ReplyKeyboardMarkup(
    [
        ["✨ Подобрать услугу", "📅 Записаться"],
        ["💰 Цены", "📍 Контакты"],
        ["❓ Помощь"]
    ],
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
    payload = {
        FORM_FIELDS["name"]: data["name"],
        FORM_FIELDS["phone"]: data["phone"],
        FORM_FIELDS["service"]: data["service"],
        FORM_FIELDS["date"]: data["date"],
        FORM_FIELDS["comment"]: data["comment"],
    }
    try:
        requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)
    except Exception as e:
        logging.error(f"Ошибка отправки формы: {e}")


def upsell_text(service: str) -> str:
    if "дизайн" not in service.lower():
        return "💎 Хочешь добавить дизайн? Маникюр будет выглядеть эффектнее ✨"
    return "🫧 Добавим уход? Кожа станет мягче и результат продержится дольше 💖"

# ================= ХЭНДЛЕРЫ =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "💅 Привет! Я помощник салона.\nПомогу записаться 💖",
        reply_markup=MAIN
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ===== СТАТИЧЕСКИЕ РАЗДЕЛЫ =====
    if text == "💰 Цены":
        await update.message.reply_text(
            "💰 Прайс-лист:\n\n"
            "💅 Маникюр — от 1500₽\n"
            "✨ Маникюр + дизайн — от 2000₽\n"
            "💆‍♀️ SPA-уход — от 800₽\n\n"
            "Точная стоимость зависит от сложности 💖",
            reply_markup=MAIN
        )
        return
    
    if text == "📍 Контакты":
        await update.message.reply_text(
            "📍 Мы находимся:\n"
            "г. Москва, ул. Примерная, 12\n\n"
            "📞 +7 999 123-45-67\n"
            "🕒 Ежедневно с 10:00 до 21:00",
            reply_markup=MAIN
        )
        return
    
    if text == "❓ Помощь":
        await update.message.reply_text(
            "❓ Чем я могу помочь:\n\n"
            "• Подобрать услугу\n"
            "• Записать к мастеру\n"
            "• Рассказать цены\n"
            "• Передать заявку администратору\n\n"
            "Просто нажми нужную кнопку 👇",
            reply_markup=MAIN
        )
        return
    
    if text == "📅 Записаться" or text == "✨ Подобрать услугу":
        await update.message.reply_text(
            "Что для тебя важнее сегодня?", reply_markup=CATEGORIES
        )
        return

    if text == "📋 Показать все услуги":
        await update.message.reply_text("Выбери категорию 👇", reply_markup=CATEGORIES)
        return

    if text == "🔙 Назад":
        await update.message.reply_text("Главное меню", reply_markup=MAIN)
        return

    # --- Категории ---
    if text == "💨 Быстро":
        await update.message.reply_text("Быстрые услуги ⚡", reply_markup=FAST)
        return

    if text == "💆‍♀️ Уход":
        await update.message.reply_text("Уходовые процедуры 💖", reply_markup=CARE)
        return

    if text == "✨ Эффектно":
        await update.message.reply_text("Эффектные услуги ✨", reply_markup=EFFECT)
        return

    # --- Выбор услуги ---
    if any(word in text for word in ["Маникюр", "Снятие", "Парафино", "дизайн"]):
        context.user_data["service"] = text
        await update.message.reply_text(upsell_text(text), reply_markup=UPSELL)
        return

    # --- Апселл ---
    if text in ["➕ Добавить дизайн", "➕ Добавить уход"]:
        context.user_data["service"] += f" + {text.replace('➕ ', '')}"
        await update.message.reply_text("Как тебя зовут?")
        return

    if text == "❌ Без допов":
        await update.message.reply_text("Как тебя зовут?")
        return

    # --- Имя ---
    if "name" not in context.user_data:
        context.user_data["name"] = text
        await update.message.reply_text("Оставь номер телефона 📞\nФормат: +79991234567")
        return

    # --- Телефон ---
    if "phone" not in context.user_data:
        if not is_phone(text):
            await update.message.reply_text("❌ Номер некорректный. Попробуй ещё раз")
            return
        context.user_data["phone"] = text
        await update.message.reply_text("На какую дату хочешь записаться? (например: 5 февраля)")
        return

    # --- Дата ---
    if "date" not in context.user_data:
        context.user_data["date"] = text
        await update.message.reply_text("Комментарий к записи? Если нет — отправь '-'")
        return

    # --- Комментарий / финал ---
    context.user_data["comment"] = text
    order_id = next_order_id()

    send_to_google_form(context.user_data)

    # Отправка пользователю
    await update.message.reply_text(
        f"🆕 Новая заявка #{order_id}\n\n"
        f"{context.user_data['name']} | {context.user_data['phone']}\n"
        f"{context.user_data['service']}\n"
        f"Дата: {context.user_data['date']}\n"
        f"Комментарий: {context.user_data['comment']}\n\n"
        f"✅ Запись принята! Администратор скоро свяжется 💖",
        reply_markup=MAIN
    )

    # Администратору
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 Заявка #{order_id}\n{context.user_data}"
    )

    context.user_data.clear()

# ================= ЗАПУСК =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
