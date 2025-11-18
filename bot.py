import os
import sqlite3
import hashlib
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
import playsound
from io import BytesIO
from PIL import Image

# Получаем токен из переменной среды
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Не найден токен! Убедись, что переменная среды TELEGRAM_TOKEN установлена.")

# Подключаем базу
conn = sqlite3.connect("suppliers.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS items
             (id INTEGER PRIMARY KEY, text TEXT, image_hash TEXT, image BLOB)''')
conn.commit()

# Юморные ответы
jokes = [
    "Ого, я вижу нового поставщика! 😎",
    "Хм, похоже на что-то знакомое… или нет? 🤔",
    "Добавляю в мою суперсекретную базу! 🔒",
    "Еще один стикер! База растет! 📈"
]

def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Загрузи фото или назови поставщика, и я всё проверю 😎")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        bio = BytesIO()
        await photo_file.download(out=bio)
        bio.seek(0)
        img_hash = get_image_hash(bio.getvalue())
        c.execute("SELECT text FROM items WHERE image_hash=?", (img_hash,))
        row = c.fetchone()
        if row:
            await update.message.reply_text(f"Такое фото уже есть! Текст: {row[0]}")
        else:
            await update.message.reply_text("Фото новое! Напиши, кто это или что за поставщик.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Пустой текст не сохраняем 😏")
        return

    c.execute("SELECT id, text FROM items WHERE text=?", (text,))
    row = c.fetchone()
    if row:
        await update.message.reply_text(f"Такой поставщик уже есть! {row[1]}")
    else:
        if context.user_data.get("last_photo"):
            img_bytes = context.user_data["last_photo"]
            img_hash = get_image_hash(img_bytes)
            c.execute("INSERT INTO items (text, image_hash, image) VALUES (?, ?, ?)",
                      (text, img_hash, img_bytes))
            conn.commit()
            await update.message.reply_text(f"{text} сохранено! {jokes[hash(text) % len(jokes)]}")
            # Голосовой ответ
            tts = gTTS(text=f"{text} сохранено!")
            tts.save("temp.mp3")
            playsound.playsound("temp.mp3")
        else:
            await update.message.reply_text("Сначала загрузи фото, иначе не сохраню 😜")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Бот запущен...")
    app.run_polling()