import logging
from datetime import datetime, timedelta
import os
import re
import requests

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================= НАСТРОЙКИ =================
TOKEN = "8542034986:AAHlph-7hJgQn_AxH2PPXhZLUPUKTkztbiI"
ADMIN_ID = 1979125261
GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_QdRSLL99UZUfgC3fvRPhiGCmSGKty_eqe-suR43yWDezzAformResponse"

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
    return bool(re.fullmatch(r"[А-Яа-яA-Za-z\- ]{2,}", text.strip()))

def send_to_google_form(data: dict):
    payload = {FORM_FIELDS[k]: data.get(k, "") for k in FORM_FIELDS}
    try:
        requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)
    except Exception as e:
        logging.error(f"Ошибка отправки формы: {e}")

# ================= УСЛУГИ =================
SERVICES = [
    ["💅 Маникюр", "✨ Маникюр + дизайн"],
    ["💆‍♀️ Уход", "💇‍♀️ Стрижка женская"],
    ["💇‍♂️ Стрижка мужская", "💅 Педикюр", "👁️ Брови"]
]

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = "service"
    await update.message.reply_text(
        "Привет! 💖\nДавай запишемся ✨\nВыбери услугу:",
        reply_markup=ReplyKeyboardMarkup(SERVICES, resize_keyboard=True)
    )

# ================= КАЛЕНДАРЬ =================
RUS_MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]

def get_calendar_buttons(start_date=None):
    start_date = start_date or datetime.today()
    keyboard = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        text = f"{day.day} {RUS_MONTHS[day.month-1]}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"date_{day.strftime('%Y-%m-%d')}")])
    keyboard.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="prev_week"),
        InlineKeyboardButton("➡️ Вперёд", callback_data="next_week")
    ])
    return InlineKeyboardMarkup(keyboard)

# ================= ХЭНДЛЕР ТЕКСТА =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = context.user_data
    step = data.get("step")

    # --- Выбор услуги ---
    if step == "service" and text in sum(SERVICES, []):
        data["service"] = text
        data["step"] = "name"
        await update.message.reply_text("Как тебя зовут?", reply_markup=ReplyKeyboardRemove())
        return

    # --- Имя ---
    if step == "name":
        if not is_name(text):
            await update.message.reply_text("❌ Введи имя буквами")
            return
        data["name"] = text
        data["step"] = "phone"
        await update.message.reply_text("Номер телефона 📞\nФормат: +79991234567")
        return

    # --- Телефон ---
    if step == "phone":
        if not is_phone(text):
            await update.message.reply_text("❌ Некорректный номер, попробуй ещё раз")
            return
        data["phone"] = text
        data["step"] = "date"
        data["calendar_start"] = datetime.today()
        await update.message.reply_text("Выбери дату:", reply_markup=get_calendar_buttons())
        return

    # --- Комментарий ---
    if step == "comment":
        data["comment"] = text
        order_id = next_order_id()
        data["order_id"] = order_id
        send_to_google_form(data)
        clean_data = {k: v for k, v in data.items() if k != "step"}
        await update.message.reply_text(
            f"✅ Заявка #{order_id} принята!\n"
            f"{data['name']} | {data['phone']}\n"
            f"{data['service']} — {data['date']}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 Новая заявка #{order_id}\n{clean_data}")
        data.clear()

# ================= CALLBACK ДЛЯ КАЛЕНДАРЯ =================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data

    if query.data.startswith("date_"):
        selected_date = query.data.split("_")[1]
        data["date"] = selected_date
        data["step"] = "comment"
        await query.message.reply_text("Комментарий? Если нет — '-'")
        return
    elif query.data == "next_week":
        data["calendar_start"] += timedelta(days=7)
        await query.message.edit_reply_markup(reply_markup=get_calendar_buttons(data["calendar_start"]))
    elif query.data == "prev_week":
        data["calendar_start"] -= timedelta(days=7)
        await query.message.edit_reply_markup(reply_markup=get_calendar_buttons(data["calendar_start"]))

# ================= ЗАПУСК =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
