# Конфигурация проекта
import os

DB_PATH = os.getenv("MC_DB", "./mc_data.sqlite")
# Планировочные часы по умолчанию (можно изменить командой /set_hours)
DEFAULT_START_HOUR = int(os.getenv("MC_DEFAULT_START_HOUR", "8"))
DEFAULT_END_HOUR = int(os.getenv("MC_DEFAULT_END_HOUR", "17"))

# Telegram token читается из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")