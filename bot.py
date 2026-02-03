import logging
import os
import re
import requests
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

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
MAIN_MENU = ReplyKeyboardMarkup([["✨ Записаться"]], resize_keyboard=True)

SERVICES = ["💅 Маникюр", "✨ Маникюр + дизайн", "✂️ Стрижка женская", "✂️ Стрижка мужская", "🦶 Педикюр", "👁️ Брови"]
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

def send_to_google_form(data: dict):
    payload = {FORM_FIELDS[k]: data.get(k, "") for k in FORM_FIELDS}
    try:
        requests.post(GOOGLE_FORM_URL, data=payload, timeout=10)
    except Exception as e:
        logging.error(f"Ошибка отправки формы: {e}")

# ================= КАЛЕНДАРЬ =================
def build_calendar(year: int, month: int):
    keyboard = []
    first_day = datetime(year, month, 1)
    start_weekday = first_day.weekday()  # понедельник=0

    # Заголовок месяца
    keyboard.append([InlineKeyboardButton(f"{first_day.strftime('%B %Y')}", callback_data='ignore')])

    # Дни недели
    week_days = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс']
    keyboard.append([InlineKeyboardButton(d, callback_data='ignore') for d in week_days])

    # Кнопки дней
    days_buttons = []
    day_num = 1
    last_day = (first_day.replace(month=month % 12 + 1, day=1) - timedelta(days=1)).day
    week = []
    for _ in range(start_weekday):
        week.append(InlineKeyboardButton(' ', callback_data='ignore'))
    while day_num <= last_day:
        week.append(InlineKeyboardButton(f"{day_num}", callback_data=f"date:{year}-{month:02d}-{day_num:02d}"))
        if len(week) == 7:
            keyboard.append(week)
            week = []
        day_num += 1
    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(' ', callback_data='ignore'))
        keyboard.append(week)

    # Листание месяцев
    prev_month = first_day - timedelta(days=1)
    next_month = first_day + timedelta(days=31)
    keyboard.append([
        InlineKeyboardButton('⬅️', callback_data=f'month:{prev_month.year}-{prev_month.month}'),
        InlineKeyboardButton('➡️', callback_data=f'month:{next_month.year}-{next_month.month}')
    ])

    return InlineKeyboardMarkup(keyboard)

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['step'] = 'service'
    context.user_data['page'] = 0
    await show_services(update, context, 0)

async def show_services(update, context, page: int):
    context.user_data['page'] = page
    start_idx = page * SERVICES_PER_PAGE
    end_idx = start_idx + SERVICES_PER_PAGE
    buttons = [[s] for s in SERVICES[start_idx:end_idx]]
    nav_buttons = []
    if page > 0:
        nav_buttons.append('⬅️ Назад')
    if end_idx < len(SERVICES):
        nav_buttons.append('➡️ Вперед')
    if nav_buttons:
        buttons.append(nav_buttons)
    await update.message.reply_text('Выбирай услугу:', reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

# ================= ОБРАБОТЧИК МЕССЕДЖЕЙ =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = context.user_data
    step = data.get('step')

    # Листание услуг
    if text == '➡️ Вперед':
        await show_services(update, context, data.get('page',0)+1)
        return
    if text == '⬅️ Назад':
        await show_services(update, context, data.get('page',0)-1)
        return

    if step == 'service':
        if text not in SERVICES:
            await update.message.reply_text('Выбери услугу кнопкой ниже')
            return
        data['service'] = text
        data['step'] = 'name'
        await update.message.reply_text('Как тебя зовут?', reply_markup=ReplyKeyboardMarkup([["⬅️ Назад в услуги"]], resize_keyboard=True))
        return

    if step == 'name':
        if text == '⬅️ Назад в услуги':
            data['step'] = 'service'
            await show_services(update, context, data.get('page',0))
            return
        data['name'] = text
        data['step'] = 'phone'
        await update.message.reply_text('Номер телефона 📞
Формат: +79991234567')
        return

    if step == 'phone':
        if not is_phone(text):
            await update.message.reply_text('❌ Некорректный номер, попробуй ещё раз')
            return
        data['phone'] = text
        data['step'] = 'date'
        now = datetime.now()
        await update.message.reply_text('Выбери дату:', reply_markup=build_calendar(now.year, now.month))
        return

    if step == 'comment':
        data['comment'] = text
        order_id = next_order_id()
        data['order_id'] = order_id
        send_to_google_form(data)
        await update.message.reply_text(f'✅ Заявка #{order_id} принята!
{data["name"]} | {data["phone"]}
{data["service"]} — {data["date"]}', reply_markup=MAIN_MENU)
        clean_data = {k:v for k,v in data.items() if k != 'step'}
        await context.bot.send_message(chat_id=ADMIN_ID, text=f'📥 Новая заявка #{order_id}\n{clean_data}')
        data.clear()

# ================= CALLBACK ДЛЯ КАЛЕНДАРЯ =================
async def calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('ignore'):
        return

    if data.startswith('month:'):
        parts = data.split(':')[1].split('-')
        year, month = int(parts[0]), int(parts[1])
        await query.edit_message_reply_markup(reply_markup=build_calendar(year, month))
        return

    if data.startswith('date:'):
        date_str = data.split(':')[1]
        context.user_data['date'] = date_str
        context.user_data['step'] = 'comment'
        await query.message.reply_text('Комментарий? Если нет — '-'')
        await query.message.delete()

# ================= ЗАПУСК =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(calendar_callback))
    app.run_polling()

if __name__ == '__main__':
    main()
