import logging
import os
import re
import requests

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= НАСТРОЙКИ =================
TOKEN = "8542034986:AAHlph-7hJgQn_AxH2PPXhZLUPUKTkztbiI"
ADMIN_ID = 1979125261

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_QdRSLL99UZUfgC3fvRPhiGCmSGKty_eqe-suR43yWDezzA/formResponse"

FORM_FIELDS = {
    "order_id": "entry.2029165293",
    "name": "entry.2110379223",
    "phone": "entry.1234675755",
    "service": "entry.1260653739",
    "date": "entry.490319395",
    "comment": "entry.1667947668",
}

ID_FILE = "order_id.txt"

logging.basicConfig(level=logging.INFO)

# ================= КНОПКИ =================
MAIN = ReplyKeyboardMarkup(
    [["✨ Записаться"]],
    resize_keyboard=True
)

SERVICES = ReplyKeyboardMarkup(
    [
        ["💅 Маникюр", "✨ Маникюр + дизайн"],
        ["💆‍♀️ Уход"],
    ],
    resize_keyboard=True
)

SERVICE_BUTTONS = {
    "💅 Маникюр",
    "✨ Маникюр + дизайн",
    "💆‍♀️ Уход",
}

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

    return str(new).zfill(6)


def is_phone(text: str) -> bool:
    return bool(re.fullmatch(r"\+?\d{10,15}", text))


def is_name(text: str) -> bool:
    return bool(re.fullmatch(r"[А-Яа-яA-Za-z\s\-]{2,30}", text))


def send_to_google_form(data: dict):
    payload = {FORM_FIELDS[k]: data.get(k, "") for k in FORM_FIELDS}
    requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)


# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = "service"

    await update.message.reply_text(
        "Привет! 💖\nДавай запишемся ✨\nКакую услугу хочешь?",
        reply_markup=SERVICES
    )


# ================= ОСНОВНОЙ ХЭНДЛЕР =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = context.user_data
    step = data.get("step")

    # --- защита от кнопок вне шага услуги ---
    if text in SERVICE_BUTTONS and step != "service":
        await update.message.reply_text("⚠️ Сначала закончим текущую запись 🙂")
        return

    # --- ШАГ: услуга ---
    if step == "service":
        if text not in SERVICE_BUTTONS:
            await update.message.reply_text("Пожалуйста, выбери услугу кнопкой 👇")
            return

        data["service"] = text
        data["step"] = "name"

        await update.message.reply_text(
            "Как тебя зовут?",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # --- ШАГ: имя ---
    if step == "name":
        if not is_name(text):
            await update.message.reply_text("❌ Введи имя буквами")
            return

        data["name"] = text
        data["step"] = "phone"

        await update.message.reply_text(
            "Номер телефона 📞\nФормат: +79991234567"
        )
        return

    # --- ШАГ: телефон ---
    if step == "phone":
        if not is_phone(text):
            await update.message.reply_text("❌ Некорректный номер, попробуй ещё раз")
            return

        data["phone"] = text
        data["step"] = "date"

        await update.message.reply_text("На какую дату?")
        return

    # --- ШАГ: дата ---
    if step == "date":
        data["date"] = text
        data["step"] = "comment"

        await update.message.reply_text("Комментарий? Если нет — '-'")
        return

    # --- ШАГ: комментарий / финал ---
    if step == "comment":
        data["comment"] = text
        data["order_id"] = next_order_id()

        send_to_google_form(data)

        await update.message.reply_text(
            f"✅ Заявка #{data['order_id']} принята!\n"
            f"{data['name']} | {data['phone']}\n"
            f"{data['service']} — {data['date']}",
            reply_markup=MAIN
        )

        clean_data = {k: v for k, v in data.items() if k != "step"}

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 Новая заявка #{data['order_id']}\n{clean_data}"
        )

        data.clear()
        return

    # --- если FSM сломан ---
    await update.message.reply_text("Нажми /start 🙂")


# ================= ЗАПУСК =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
