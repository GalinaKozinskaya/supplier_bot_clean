import os
import sqlite3
from PIL import Image
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

DB_FILE = "supplier_bot.db"

# База данных
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    photo BLOB
)
""")
conn.commit()

# Токен из переменной среды
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Не найден токен! Убедись, что переменная среды TELEGRAM_TOKEN установлена.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Загрузи фото стикера, и я спрошу название фирмы 😎"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Сравнение с уже сохранёнными фото
    cursor.execute("SELECT id, name, photo FROM items")
    all_items = cursor.fetchall()
    for item_id, name, saved_photo in all_items:
        if saved_photo == photo_bytes:
            await update.message.reply_text(
                f"О! Я уже знаю это фото — фирма: {name}. Не повторяемся 😉"
            )
            return
    
    # Новый фото — спрашиваем название фирмы
    await update.message.reply_text("Нового фото! Как называется фирма?")
    # Сохраняем временно в контексте
    context.user_data["new_photo"] = photo_bytes

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "new_photo" in context.user_data:
        name = update.message.text
        photo_bytes = context.user_data.pop("new_photo")
        cursor.execute("INSERT INTO items (name, photo) VALUES (?, ?)", (name, photo_bytes))
        conn.commit()
        await update.message.reply_text(f"Записал фирму '{name}' 😎👍")
    else:
        await update.message.reply_text(
            "Напиши /start и загрузи фото, прежде чем называть фирму 😉"
        )

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Бот запущен...")
    app.run_polling()