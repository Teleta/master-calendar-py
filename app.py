"""Точка входа приложения. Собирает Application и регистрирует хэндлеры."""
import logging
import config
from telegram.ext import Application
import handlers

logging.basicConfig(level=logging.INFO)

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    handlers.register_handlers(app)
    app.run_polling()

if __name__ == '__main__':
    main()
