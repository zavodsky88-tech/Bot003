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
TOKEN = "8542034986:AAHlph-7hJgQn_AxH2PPXhZLUPUKTkztbiI"
ADMIN_ID = 1979125261

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_QdRSLL99UZUfgC3fvRPhiGCmSGKty_eqe-suR43yWDezzA/formResponse"

FORM_FIELDS = {
    "name": "entry.2110379223",
    "phone": "entry.1234675755",
    "service": "entry.1260653739",
    "date": "entry.490319395",
    "comment": "entry.1667947668",
    "order_id": "entry.2029165293"
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
    [
        ["💨 Быстро", "💆‍♀️ Уход"],
        ["✨ Эффектно"],
        ["📋 Показать все услуги"],
        ["🔙 Назад"]
    ],
    resize_keyboard=True
)

FAST = ReplyKeyboardMarkup(
    [
        ["💅 Маникюр экспресс"],
        ["🎨 Снятие + покрытие"],
        ["🔙 Назад"]
    ],
    resize_keyboard=True
)

CARE = ReplyKeyboardMarkup(
    [
        ["💆‍♀️ Маникюр + SPA-уход"],
        ["🫧 Парафинотерапия"],
        ["🔙 Назад"]
    ],
    resize_keyboard=True
)

EFFECT = ReplyKeyboardMarkup(
    [
        ["✨ Маникюр + дизайн"],
        ["💎 Авторский дизайн"],
        ["🔙 Назад"]
    ],
    resize_keyboard=True
)

UPSELL = ReplyKeyboardMarkup(
    [
        ["➕ Добавить дизайн"],
        ["➕ Добавить уход"],
        ["❌ Без допов"]
    ],
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
    payload = {}
    for key, form_key in FORM_FIELDS.items():
        payload[form_key] = data.get(key, "")

    try:
        requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)
        logging.info(f"Заявка #{data.get('order_id')} отправлена в Google Form")
    except Exception as e:
        logging.error(f"Ошибка отправки формы: {e}")


def upsell_text(service: str) -> str:
    if "дизайн" not in service.lower():
        return "💎 Хочешь добавить дизайн? Маникюр будет выглядеть эффектнее ✨"
    return "🫧 Добавим уход? Кожа станет мягче и результат продержится дольше 💖"


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! 💖\nЯ помогу подобрать услугу и записаться к мастеру ✨",
        reply_markup=MAIN
    )


# ================= ОСНОВНОЙ ХЭНДЛЕР =================
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
                "📍 Москва, ул. Примерная, 12\n📞 +7 999 123-45-67\n🕒 10:00–21:00",
                reply_markup=MAIN
            )

        elif text == "❓ Помощь":
            await update.message.reply_text(
                "❓ Я могу:\n• Подобрать услугу\n• Записать к мастеру\n• Рассказать цены",
                reply_markup=MAIN
            )

        else:
            await update.message.reply_text("Выбери категорию 👇", reply_markup=CATEGORIES)

        return

    # --- Категории ---
    if text in ["💨 Быстро", "💆‍♀️ Уход", "✨ Эффектно"]:
        if text == "💨 Быстро":
            await update.message.reply_text("Быстрые услуги ⚡", reply_markup=FAST)
        elif text == "💆‍♀️ Уход":
            await update.message.reply_text("Уходовые процедуры 💖", reply_markup=CARE)
        else:
            await update.message.reply_text("Эффектные услуги ✨", reply_markup=EFFECT)
        return

    # --- Выбор услуги ---
    if "service" not in user_data and any(w in text.lower() for w in ["маникюр", "снятие", "парафино", "дизайн"]):
        user_data["service"] = text
        user_data["awaiting_upsell"] = True
        await update.message.reply_text(upsell_text(text), reply_markup=UPSELL)
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
        await update.message.reply_text("На какую дату хочешь записаться?")
        return

    # --- Дата ---
    if "date" not in user_data:
        user_data["date"] = text
        await update.message.reply_text("Комментарий? Если нет — отправь '-'")
        return

    # --- Финал ---
    if "comment" not in user_data:
        user_data["comment"] = text
        user_data["order_id"] = next_order_id()

        send_to_google_form(user_data)

        await update.message.reply_text(
            f"🆕 Заявка #{user_data['order_id']}\n"
            f"{user_data['name']} | {user_data['phone']}\n"
            f"{user_data['service']}\n"
            f"Дата: {user_data['date']}\n\n"
            "✅ Запись принята! Администратор скоро свяжется 💖",
            reply_markup=MAIN
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 Новая заявка #{user_data['order_id']}\n{user_data}"
        )

        user_data.clear()


# ================= ЗАПУСК =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
