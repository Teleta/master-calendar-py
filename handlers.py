"""Хэндлеры для команд Telegram. Модульная организация.
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from datetime import datetime, timedelta
import db
import scheduler

# Состояния
(BUSY_SELECT_START_DATE, BUSY_SELECT_END_DATE, BUSY_SELECT_START_TIME, BUSY_SELECT_END_TIME, BUSY_ENTER_LABEL, BUSY_CONFIRM) = range(6)
(TASK_ENTER_LABEL, TASK_ENTER_DURATION) = range(2)
(SET_HOURS_WAIT) = range(1)

# --- Команды ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я MC — помогаю составлять недельное расписание.\n"
        "Команды: /busy /task /schedule /my_busy /my_tasks /set_hours /help"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)

# --- Busy flow ---
async def busy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.clear()
    context.user_data["conversation_state"] = {"step": BUSY_SELECT_START_DATE}

    # Выбор даты начала через InlineKeyboard
    today = datetime.now().date()
    keyboard = [
        [InlineKeyboardButton((today + timedelta(days=i)).strftime("%Y-%m-%d"), callback_data=f"date_{(today + timedelta(days=i))}")]
        for i in range(7)
    ]
    await update.message.reply_text("Выберите дату начала:", reply_markup=InlineKeyboardMarkup(keyboard))
    return BUSY_SELECT_START_DATE

async def busy_calendar_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    cur_step = context.user_data["conversation_state"]["step"]
    selected_date = datetime.strptime(data.split("_")[1], "%Y-%m-%d").date()

    if cur_step == BUSY_SELECT_START_DATE:
        context.user_data["busy_start_date"] = selected_date
        context.user_data["conversation_state"]["step"] = BUSY_SELECT_END_DATE

        # Кнопки выбора даты окончания
        today = datetime.now().date()
        keyboard = [
            [InlineKeyboardButton((today + timedelta(days=i)).strftime("%Y-%m-%d"), callback_data=f"date_{(today + timedelta(days=i))}")]
            for i in range(7)
        ]
        await query.edit_message_text("Теперь выберите дату окончания:", reply_markup=InlineKeyboardMarkup(keyboard))
        return BUSY_SELECT_END_DATE

    elif cur_step == BUSY_SELECT_END_DATE:
        context.user_data["busy_end_date"] = selected_date

        # Кнопки выбора времени начала
        keyboard = [[InlineKeyboardButton(f"{h:02d}:00", callback_data=f"time_{h}")] for h in range(24)]
        await query.edit_message_text("Выберите время начала:", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data["conversation_state"]["step"] = BUSY_SELECT_START_TIME
        return BUSY_SELECT_START_TIME

    return ConversationHandler.END

async def busy_time_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    hour = int(query.data.split("_")[1])
    cur_step = context.user_data["conversation_state"]["step"]

    if cur_step == BUSY_SELECT_START_TIME:
        context.user_data["busy_start_time"] = hour
        keyboard = [[InlineKeyboardButton(f"{h:02d}:00", callback_data=f"time_{h}")] for h in range(24)]
        await query.edit_message_text("Выберите время окончания:", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data["conversation_state"]["step"] = BUSY_SELECT_END_TIME
        return BUSY_SELECT_END_TIME

    elif cur_step == BUSY_SELECT_END_TIME:
        context.user_data["busy_end_time"] = hour
        await query.edit_message_text("Введите название события:")
        return BUSY_ENTER_LABEL

    return ConversationHandler.END

async def busy_enter_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    label = update.message.text.strip()
    sd = context.user_data["busy_start_date"]
    ed = context.user_data["busy_end_date"]
    sh = context.user_data["busy_start_time"]
    eh = context.user_data["busy_end_time"]
    start_dt = datetime(sd.year, sd.month, sd.day, sh)
    end_dt = datetime(ed.year, ed.month, ed.day, eh)

    if start_dt >= end_dt:
        await update.message.reply_text("Время конца должно быть позже времени начала. Повторите /busy.")
        return ConversationHandler.END

    # Сохраним во временный pending и спросим подтверждение
    context.user_data["pending_busy"] = {
        "label": label,
        "start_ts": int(start_dt.timestamp()),
        "end_ts": int(end_dt.timestamp()),
    }

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Сохранить", callback_data="save_busy_yes"),
         InlineKeyboardButton("❌ Отмена", callback_data="save_busy_no")]
    ])
    msg = f"Подтвердите событие:\n{sd} {sh:02d}:00 - {ed} {eh:02d}:00\n{label}"
    await update.message.reply_text(msg, reply_markup=kb)
    return BUSY_CONFIRM

async def busy_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "save_busy_yes":
        p = context.user_data.get("pending_busy")
        if not p:
            await query.edit_message_text("Нет данных для сохранения.")
            return ConversationHandler.END
        user_id = query.from_user.id
        db.add_busy(user_id, p["label"], p["start_ts"], p["end_ts"])
        await query.edit_message_text("Событие сохранено ✅")
    else:
        await query.edit_message_text("Сохранение отменено ❌")
    return ConversationHandler.END

# --- Tasks ---
async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название задачи:")
    return TASK_ENTER_LABEL

async def task_enter_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_label"] = update.message.text.strip()
    await update.message.reply_text("Введите длительность в часах (например 2.5):")
    return TASK_ENTER_DURATION

async def task_enter_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        dur = float(update.message.text.strip())
        if dur <= 0:
            raise ValueError()
        label = context.user_data.get("task_label")
        db.add_task(user_id, label, dur, None)
        await update.message.reply_text(f"Задача '{label}' ({dur} ч) сохранена ✅")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректная длительность. Введите число.")
        return TASK_ENTER_DURATION

# --- Просмотр ---
async def my_busy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rows = db.get_busy(user_id)
    if not rows:
        await update.message.reply_text("У вас нет сохранённых занятостей.")
        return
    msg = "<b>Ваши занятости:</b>\n"
    for r in rows:
        sd = datetime.fromtimestamp(r["start_ts"])
        ed = datetime.fromtimestamp(r["end_ts"])
        msg += f"• <b>{r['label']}</b>: {sd.strftime('%Y-%m-%d %H:%M')} - {ed.strftime('%Y-%m-%d %H:%M')}\n"
    await update.message.reply_text(msg, parse_mode="HTML")

async def my_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rows = db.get_tasks(user_id)
    if not rows:
        await update.message.reply_text("У вас нет задач.")
        return
    msg = "<b>Ваши задачи:</b>\n"
    for r in rows:
        msg += f"• <b>{r['label']}</b>: {r['duration_hours']} часов\n"
    await update.message.reply_text(msg, parse_mode="HTML")

# --- Schedule ---
async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    schedule = scheduler.build_week_schedule(user_id)
    today = datetime.now().date()
    msg = "<b>Недельное расписание:</b>\n\n"
    for i in range(7):
        d = today + timedelta(days=i)
        msg += f"<b>{d.strftime('%A, %Y-%m-%d')}</b>:\n"
        items = sorted(schedule.get(d, []), key=lambda x: x['start'])
        if not items:
            msg += "  - Свободно\n"
        for it in items:
            msg += f"  - {it['start'].strftime('%H:%M')}-{it['end'].strftime('%H:%M')}: {it['label']} ({it['type']})\n"
        msg += "\n"
    await update.message.reply_text(msg, parse_mode="HTML")

# --- Set hours ---
async def set_hours_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите рабочие часы в формате: `start end` (например: 8 17)")
    return SET_HOURS_WAIT

async def set_hours_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("Неправильный формат. Попробуйте снова: два числа, например `8 17`")
        return SET_HOURS_WAIT
    try:
        sh = int(parts[0])
        eh = int(parts[1])
        if not (0 <= sh < 24 and 0 < eh <= 24 and sh < eh):
            raise ValueError()
        db.set_user_hours(user_id, sh, eh)
        await update.message.reply_text(f"Рабочие часы обновлены: {sh}:00 - {eh}:00")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Неправильные числа. Попробуйте снова.")
        return SET_HOURS_WAIT

# --- Регистрация хэндлеров для Application ---
def register_handlers(application):
    # Простые команды
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('my_busy', my_busy_command))
    application.add_handler(CommandHandler('my_tasks', my_tasks_command))
    application.add_handler(CommandHandler('schedule', schedule_command))
    application.add_handler(CommandHandler('set_hours', set_hours_command))

    # Busy conversation
    busy_conv = ConversationHandler(
        entry_points=[CommandHandler('busy', busy_command)],
        states={
            BUSY_SELECT_START_DATE: [CallbackQueryHandler(busy_calendar_select, pattern='^date')],
            BUSY_SELECT_END_DATE: [CallbackQueryHandler(busy_calendar_select, pattern='^date')],
            BUSY_SELECT_START_TIME: [CallbackQueryHandler(busy_time_select, pattern='^time')],
            BUSY_SELECT_END_TIME: [CallbackQueryHandler(busy_time_select, pattern='^time')],
            BUSY_ENTER_LABEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, busy_enter_label)],
            BUSY_CONFIRM: [CallbackQueryHandler(busy_confirm_callback, pattern='^save_busy_')],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    application.add_handler(busy_conv)

    # Task conversation
    task_conv = ConversationHandler(
        entry_points=[CommandHandler('task', task_command)],
        states={
            TASK_ENTER_LABEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_enter_label)],
            TASK_ENTER_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_enter_duration)],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    application.add_handler(task_conv)

    # Set hours conversation
    sethours_conv = ConversationHandler(
        entry_points=[CommandHandler('set_hours', set_hours_command)],
        states={SET_HOURS_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_hours_handle)]},
        fallbacks=[],
        allow_reentry=True,
    )
    application.add_handler(sethours_conv)
