import os
import json
import hashlib
import random
import sqlite3
from io import BytesIO
from PIL import Image
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

DB_PATH = "suppliers.db"

# Получаем токен
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Не найден токен! Убедись, что переменная среды TELEGRAM_TOKEN установлена.")

# Подключение к базе
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    photo_hash TEXT,
    photo BLOB,
    description TEXT
)
""")
conn.commit()

# Юморные ответы бота
JOKES = [
    "Ого, похожее уже есть! Добавим новые данные?",
    "Кажется, я это уже видел 😉",
    "Ставим клеймо уникальности или дополняем?",
]

# Хэш фото для сравнения
def hash_image(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

# Проверка, есть ли похожее фото
def photo_exists(photo_bytes):
    h = hash_image(photo_bytes)
    cursor.execute("SELECT id FROM suppliers WHERE photo_hash=?", (h,))
    result = cursor.fetchone()
    return result[0] if result else None

# Поиск по названию поставщика
def find_supplier(name):
    cursor.execute("SELECT id, photo, description FROM suppliers WHERE name LIKE ?", (f"%{name}%",))
    return cursor.fetchall()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Загрузи фото поставщика или введи его название. "
        "Я проверю, есть ли уже запись и покажу, что знаю 😉"
    )

# Обработка текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    results = find_supplier(text)
    if results:
        reply = ""
        for r in results:
            img_bytes = r[1]
            bio = BytesIO(img_bytes)
            bio.name = "photo.jpg"
            bio.seek(0)
            await update.message.reply_photo(photo=bio, caption=r[2])
        return
    else:
        await update.message.reply_text(
            f"Я не нашёл '{text}' 😅. Отправь фото и текст поставщика, чтобы сохранить его."
        )

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    existing_id = photo_exists(photo_bytes)
    
    if existing_id:
        await update.message.reply_text(random.choice(JOKES))
        return
    
    # Ждём текста после фото
    context.user_data['pending_photo'] = photo_bytes
    await update.message.reply_text("Фото получено! Теперь пришли название поставщика.")

# Сохранение нового поставщика после текста
async def save_supplier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'pending_photo' not in context.user_data:
        await handle_text(update, context)
        return
    
    photo_bytes = context.user_data.pop('pending_photo')
    name = update.message.text.strip()
    photo_hash = hash_image(photo_bytes)
    
    cursor.execute(
        "INSERT INTO suppliers (name, photo_hash, photo, description) VALUES (?, ?, ?, ?)",
        (name, photo_hash, photo_bytes, f"Поставщик {name}")
    )
    conn.commit()
    
    await update.message.reply_text(f"Запись для '{name}' сохранена! 😎")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_supplier))
    
    print("Бот запущен...")
    app.run_polling()