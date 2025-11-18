import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
import pyttsx3
import tempfile

# Токен от BotFather
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Не найден токен! Убедись, что переменная среды TELEGRAM_TOKEN установлена.")

# Подключение к локальной SQLite базе (она будет храниться в облаке вместе с ботом)
conn = sqlite3.connect("supplier_bot.db")
cursor = conn.cursor()

# Создаем таблицу, если нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_id TEXT UNIQUE,
    description TEXT
)
""")
conn.commit()

# Голосовой движок (локально на сервере)
engine = pyttsx3.init()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Загрузи фото поставщика или сделай снимок, а потом напиши или скажи его название. 🚀"
    )

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id

    # Проверка базы по photo_id
    cursor.execute("SELECT description FROM suppliers WHERE photo_id=?", (file_id,))
    result = cursor.fetchone()

    if result:
        text = f"Уже есть в базе: {result[0]} 😎"
        await update.message.reply_text(text)
        speak(text)
    else:
        await update.message.reply_text("Новое фото! Напиши или скажи название поставщика.")
        # Сохраняем временно в контексте, чтобы добавить текст позже
        context.user_data["new_photo_id"] = file_id

# Обработка текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "new_photo_id" in context.user_data:
        photo_id = context.user_data.pop("new_photo_id")
        cursor.execute(
            "INSERT OR IGNORE INTO suppliers (photo_id, description) VALUES (?, ?)",
            (photo_id, text)
        )
        conn.commit()
        reply = f"Сохранили нового поставщика: {text} 🎉"
        await update.message.reply_text(reply)
        speak(reply)
    else:
        # Поиск по тексту
        cursor.execute("SELECT photo_id FROM suppliers WHERE description LIKE ?", (f"%{text}%",))
        results = cursor.fetchall()
        if results:
            reply = f"Нашёл поставщика по тексту: {text} 👍"
            await update.message.reply_text(reply)
            speak(reply)
        else:
            await update.message.reply_text("Не найдено! Загрузи фото для нового поставщика.")

# Функция озвучки
def speak(text):
    try:
        # pyttsx3 — локальная озвучка
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("Ошибка озвучки:", e)

# Основной запуск
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Бот запущен...")
    app.run_polling()