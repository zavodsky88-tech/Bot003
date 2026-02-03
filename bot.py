import logging
import os
import re
import requests
from datetime import datetime, timedelta
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
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
MAIN_MENU = ReplyKeyboardMarkup(
    [["✨ Записаться"]],
    resize_keyboard=True
)

SERVICES_MENU = ReplyKeyboardMarkup(
    [
        ["💇‍♀️ Стрижка женская", "💇‍♂️ Стрижка мужская"],
        ["💅 Маникюр", "🦶 Педикюр"],
        ["👁️ Брови"]
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
    return str(new).zfill(6)

def is_phone(text: str) -> bool:
    return bool(re.fullmatch(r"\+?\d{10,15}", text))

def is_name(text: str) -> bool:
    return bool(re.fullmatch(r"[А-Яа-яЁё\s\-]+", text.strip()))

def send_to_google_form(data: dict):
    payload = {FORM_FIELDS[k]: data.get(k, "") for k in FORM_FIELDS}
    try:
        requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)
    except Exception as e:
        logging.error(f"Ошибка отправки формы: {e}")

# ================= КАЛЕНДАРЬ =================
MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

def get_calendar(year: int, month: int):
    """Возвращает InlineKeyboardMarkup календаря на указанный месяц"""
    first_day = datetime(year, month, 1)
    start_day = first_day.weekday()  # Пн=0
    days_in_month = (first_day.replace(month=month % 12 + 1, day=1) - timedelta(days=1)).day

    keyboard = []

    # Заголовок с месяцем
    keyboard.append([InlineKeyboardButton(f"{MONTHS[month-1]} {year}", callback_data="ignore")])

    # Дни недели
    keyboard.append([
        InlineKeyboardButton(d, callback_data="ignore") for d in ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
    ])

    # Пустые дни перед 1 числом
    week = [InlineKeyboardButton(" ", callback_data="ignore")] * start_day

    for day in range(1, days_in_month +1):
        week.append(InlineKeyboardButton(str(day), callback_data=f"date-{year}-{month}-{day}"))
        if len(week) == 7:
            keyboard.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(" ", callback_data="ignore"))
        keyboard.append(week)

    # Навигация
    prev_month = month -1 or 12
    prev_year = year-1 if month ==1 else year
    next_month = month +1 if month<12 else 1
    next_year = year+1 if month==12 else year
    keyboard.append([
        InlineKeyboardButton("⬅️", callback_data=f"month-{prev_year}-{prev_month}"),
        InlineKeyboardButton("➡️", callback_data=f"month-{next_year}-{next_month}")
    ])
    return InlineKeyboardMarkup(keyboard)

# ================= ХЭНДЛЕРЫ =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = "service"

    await update.message.reply_text(
        "Привет! 💖\nДавай запишемся ✨\nКакую услугу хочешь?",
        reply_markup=SERVICES_MENU
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = context.user_data
    step = data.get("step")

    SERVICES = [
        "💇‍♀️ Стрижка женская", "💇‍♂️ Стрижка мужская",
        "💅 Маникюр", "🦶 Педикюр", "👁️ Брови"
    ]

    if step != "service" and text in SERVICES:
        await update.message.reply_text("⚠️ Сначала закончим текущую запись 🙂")
        return

    if step == "service":
        if text not in SERVICES:
            await update.message.reply_text("❌ Выберите услугу кнопкой")
            return
        data["service"] = text
        data["step"] = "name"
        await update.message.reply_text("Как тебя зовут?")
        return

    if step == "name":
        if not is_name(text):
            await update.message.reply_text("❌ Введи имя буквами")
            return
        data["name"] = text
        data["step"] = "phone"
        await update.message.reply_text("Номер телефона 📞\nФормат: +79991234567")
        return

    if step == "phone":
        if not is_phone(text):
            await update.message.reply_text("❌ Некорректный номер, попробуй ещё раз")
            return
        data["phone"] = text
        data["step"] = "date"
        now = datetime.now()
        await update.message.reply_text(
            "Выбери дату:",
            reply_markup=get_calendar(now.year, now.month)
        )
        return

    if step == "comment":
        data["comment"] = text
        order_id = next_order_id()
        data["order_id"] = order_id
        send_to_google_form(data)

        await update.message.reply_text(
            f"✅ Заявка #{order_id} принята!\n"
            f"{data['name']} | {data['phone']}\n"
            f"{data['service']} — {data['date']}",
            reply_markup=MAIN_MENU
        )
        clean_data = {k: v for k, v in data.items() if k != "step"}
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 Новая заявка #{order_id}\n{clean_data}")
        data.clear()
        return

# Обработка нажатий на календарь
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data

    if query.data.startswith("date-"):
        _, y, m, d = query.data.split("-")
        data["date"] = f"{int(d)} {MONTHS[int(m)-1]} {y}"
        data["step"] = "comment"
        await query.message.edit_text("Комментарий? Если нет — '-'")
        return

    if query.data.startswith("month-"):
        _, y, m = query.data.split("-")
        await query.message.edit_text(
            "Выбери дату:",
            reply_markup=get_calendar(int(y), int(m))
        )
        return

    if query.data == "ignore":
        pass

# ================= ЗАПУСК =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
