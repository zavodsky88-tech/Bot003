import logging
import os
import re
import requests
from datetime import datetime, timedelta
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
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

SERVICES = [
    "💅 Маникюр",
    "✨ Маникюр + дизайн",
    "✂️ Стрижка женская",
    "✂️ Стрижка мужская",
    "🦶 Педикюр",
    "👁️ Брови"
]

SERVICES_PER_PAGE = 3

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
    return bool(re.fullmatch(r"[А-Яа-яЁё\s\-]+", text))


def send_to_google_form(data: dict):
    payload = {FORM_FIELDS[k]: data.get(k, "") for k in FORM_FIELDS}
    try:
        requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)
    except Exception as e:
        logging.error(e)

# ================= КАЛЕНДАРЬ =================
MONTHS_RU = [
    "Январь","Февраль","Март","Апрель","Май","Июнь",
    "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"
]

def build_calendar(year: int, month: int):
    keyboard = []

    now = datetime.now()
    first_day = datetime(year, month, 1)
    start_weekday = first_day.weekday()

    title = f"📅 {MONTHS_RU[month-1]} {year}"
    keyboard.append([InlineKeyboardButton(title, callback_data="ignore")])

    days = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
    keyboard.append([InlineKeyboardButton(d, callback_data="ignore") for d in days])

    last_day = (first_day.replace(month=month % 12 + 1, day=1) - timedelta(days=1)).day
    week = []

    for _ in range(start_weekday):
        week.append(InlineKeyboardButton(" ", callback_data="ignore"))

    for day in range(1, last_day + 1):
        label = f"🔹{day}"
        if day == now.day and month == now.month and year == now.year:
            label = f"🔥{day}"

        week.append(
            InlineKeyboardButton(label, callback_data=f"date:{year}-{month:02d}-{day:02d}")
        )

        if len(week) == 7:
            keyboard.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(" ", callback_data="ignore"))
        keyboard.append(week)

    prev_month = first_day - timedelta(days=1)
    next_month = first_day + timedelta(days=31)

    keyboard.append([
        InlineKeyboardButton("⬅️", callback_data=f"month:{prev_month.year}-{prev_month.month}"),
        InlineKeyboardButton("➡️", callback_data=f"month:{next_month.year}-{next_month.month}")
    ])

    return InlineKeyboardMarkup(keyboard)

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! 💖\nЯ помогу тебе записаться в салон ✨",
        reply_markup=MAIN_MENU
    )

# ================= ПОКАЗ УСЛУГ =================
async def show_services(update, context, page):
    context.user_data["page"] = page
    start = page * SERVICES_PER_PAGE
    end = start + SERVICES_PER_PAGE

    buttons = [[s] for s in SERVICES[start:end]]
    nav = []

    if page > 0:
        nav.append("⬅️ Назад")
    if end < len(SERVICES):
        nav.append("➡️ Вперед")

    if nav:
        buttons.append(nav)

    await update.message.reply_text(
        "Выбери услугу 💅",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

# ================= ОБРАБОТКА СООБЩЕНИЙ =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = context.user_data
    step = data.get("step")

    # КНОПКА ЗАПИСАТЬСЯ
    if text == "✨ Записаться":
        data.clear()
        data["step"] = "service"
        await show_services(update, context, 0)
        return

    # НАВИГАЦИЯ
    if text == "➡️ Вперед":
        await show_services(update, context, data.get("page", 0) + 1)
        return

    if text == "⬅️ Назад":
        await show_services(update, context, data.get("page", 0) - 1)
        return

    # ВЫБОР УСЛУГИ
    if step == "service":
        if text not in SERVICES:
            return
        data["service"] = text
        data["step"] = "name"
        await update.message.reply_text(
            "Как тебя зовут? 😊",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # ИМЯ
    if step == "name":
        if not is_name(text):
            await update.message.reply_text("❌ Введи имя буквами")
            return
        data["name"] = text
        data["step"] = "phone"
        await update.message.reply_text("Номер телефона 📞\nФормат: +79991234567")
        return

    # ТЕЛЕФОН
    if step == "phone":
        if not is_phone(text):
            await update.message.reply_text("❌ Неверный номер")
            return
        data["phone"] = text
        data["step"] = "date"
        now = datetime.now()
        await update.message.reply_text(
            "📅 Выбери дату:",
            reply_markup=build_calendar(now.year, now.month)
        )
        return

    # КОММЕНТАРИЙ
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

        await context.bot.send_message(
            ADMIN_ID,
            f"📥 Новая заявка #{order_id}\n{data}"
        )

        data.clear()

# ================= CALLBACK КАЛЕНДАРЯ =================
async def calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "ignore":
        return

    if data.startswith("month:"):
        y, m = map(int, data.split(":")[1].split("-"))
        await query.edit_message_reply_markup(build_calendar(y, m))
        return

    if data.startswith("date:"):
        date = data.split(":")[1]
        context.user_data["date"] = date
        context.user_data["step"] = "comment"
        await query.message.delete()
        await query.message.reply_text("✏️ Добавь комментарий или отправь '-'")

# ================= ЗАПУСК =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(calendar_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
