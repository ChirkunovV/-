from datetime import date

import pandas as pd #нужен для работы с эксель файлом  (открыть,считать инфу,вывести что-то, и тд.)
from telegram import Update # все что ниже просто для бота надо
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

TOKEN = "8511875679:AAGTo8CGvtmyZPH7UCYxMoZXjmXOO9t2Kik"

GROUP_RECORDING = 123 # состояние просто в виде циферок
WEEKDAYS_RU = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]

n_group= {} # в качестве ключа - ID пользователя, а value - номер группы

EXCEL_PATH = "rasp.xlsx"


def format_today(df: pd.DataFrame):
    day_col = WEEKDAYS_RU[date.today().weekday()] # определяет расписание на сегодня 

    if day_col not in df.columns:
        return f"В таблице нет столбца «{day_col}»"

    lines = []
    for _, row in df.iterrows():
        num = row.get("№", "")
        time = row.get("Время", "")
        subj = row.get(day_col, "")

        if pd.isna(subj) or str(subj).strip() == "":
            subj = "НЕТ ПАР"

        if (pd.isna(num) or str(num).strip() == "") and (pd.isna(time) or str(time).strip() == ""):
            continue

        num = "" if pd.isna(num) else str(num).strip()
        time = "" if pd.isna(time) else str(time).strip()
        lines.append(f"{num}) {time} — {subj}")

    if not lines:
        return "Нет данных"

    if all(line.endswith("НЕТ ПАР") for line in lines):
        return "Сегодня НЕТ ПАР ✅"

    return "\n".join(lines)


def normalize_sheet_name(text: str) -> str:
    return text.strip() # даже если пользователь ввел номер группы криво (лишние пробелы) то бот бы все равно считал информацию правильно


def available_sheets() -> list[str]: # считывает эксель файл, и возращает листы 
    xls = pd.ExcelFile(EXCEL_PATH) 
    return xls.sheet_names


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! 👋\n"
        "Я бот с расписанием.\n\n"
        "Команды:\n"
        "/today — показать расписание на сегодня\n"
        "Если ты запускаешь /today впервые, я спрошу номер группы."
    )


async def raspisanietd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    sheet = n_group.get(user_id)

    if sheet is None:
        await update.message.reply_text("Сначала укажи группу командой /today")
        return ConversationHandler.END

    sheets = available_sheets()

    if sheet not in ["1","2","3"]:
        await update.message.reply_text(
            f"Нет листа «{sheet}».\nДоступные группы: {', '.join(sheets)}"
        )
        return ConversationHandler.END

    rasp = pd.read_excel(EXCEL_PATH, sheet_name=sheet)

    text = f"📅 {WEEKDAYS_RU[date.today().weekday()]} • группа {sheet}\n" + format_today(rasp)
    await update.message.reply_text(text)

    return ConversationHandler.END


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if user_id not in n_group:
        await update.message.reply_text("В какой ты группе? (например: 1 или 2 или 3)")
        return GROUP_RECORDING

    return await raspisanietd(update, context)


async def group_recording(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    group_text = update.message.text

    n_group[user_id] = normalize_sheet_name(group_text)

    return await raspisanietd(update, context)



bot = Application.builder().token(TOKEN).build()

job = CommandHandler("start", start)

bot.add_handler(job)

con = ConversationHandler(
    entry_points=[CommandHandler("today", today)],
    states={
        GROUP_RECORDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_recording)],
    },
    fallbacks=[],
)

bot.add_handler(con)
bot.run_polling()