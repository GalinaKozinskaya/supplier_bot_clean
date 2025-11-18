<<<<<<< HEAD
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Вставь сюда токен от BotFather
TOKEN = "8240072124:AAHz8TZSCltrxkLx4eyzCh84WgriGK3PfIo"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Загрузи фото стикера, и я постараюсь определить поставщика."
    )

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Фото получено! Скоро я научусь распознавать поставщика 😎"
    )

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Бот запущен...")
    app.run_polling()
=======
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Берём токен из переменной среды
TOKEN = os.getenv("8240072124:AAHz8TZSCltrxkLx4eyzCh84WgriGK3PfIo")

# Проверка: если токен пустой, бот не запустится
if not TOKEN:
    raise ValueError("Не найден токен! Убедись, что переменная среды TELEGRAM_TOKEN установлена.")

# Создаём Updater и Dispatcher
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# Простейшая команда /start
def start(update: Update, context):
    update.message.reply_text("Привет! Я твой бот-помощник для поставщиков.")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# Обработчик текстовых сообщений
def echo(update: Update, context):
    update.message.reply_text(f"Ты написал: {update.message.text}")

echo_handler = MessageHandler(Filters.text & ~Filters.command, echo)
dispatcher.add_handler(echo_handler)

# Запуск бота
print("Бот запущен...")
updater.start_polling()
updater.idle()
>>>>>>> add05ee7 (Первый коммит с bot.py и requirements.txt)
