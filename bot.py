import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

DB_FILE = "database.json"

# Загружаем базу или создаём пустую
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
else:
    db = {}

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Не найден токен! Убедись, что переменная среды TELEGRAM_TOKEN установлена.")

# Утилиты для работы с базой
def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def find_supplier_by_text(text):
    results = []
    for supplier, items in db.items():
        for item in items:
            if text.lower() in item["text"].lower():
                results.append((supplier, item))
    return results

def find_supplier_by_photo(file_id):
    results = []
    for supplier, items in db.items():
        for item in items:
            if "file_id" in item and item["file_id"] == file_id:
                results.append((supplier, item))
    return results

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Загрузи фото или напиши название поставщика, а я постараюсь найти совпадения.\n"
        "Если нового нет — я попрошу сохранить фото и текст."
    )

# Обработка текстового сообщения
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    results = find_supplier_by_text(text)
    if results:
        response = ""
        for supplier, item in results:
            response += f"Поставщик: {supplier}\nОписание: {item['text']}\n\n"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            f"Не нашёл такого текста 😅. Отправь вместе с фото, чтобы я добавил нового поставщика."
        )

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]  # берём фото наибольшего размера
    file_id = photo.file_id

    results = find_supplier_by_photo(file_id)
    if results:
        response = ""
        for supplier, item in results:
            response += f"Поставщик: {supplier}\nОписание: {item['text']}\n\n"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            "Новое фото! Как зовут поставщика и что за текст на коробке/стикере?"
        )
        context.user_data["new_file_id"] = file_id  # запомним фото для добавления
        context.user_data["awaiting_text"] = True

# Сохранение нового фото+текста
async def handle_text_for_new_supplier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_text"):
        supplier_info = update.message.text.strip()
        file_id = context.user_data.pop("new_file_id")
        context.user_data["awaiting_text"] = False

        # Разделяем название поставщика и текст
        if " " in supplier_info:
            supplier_name, text_description = supplier_info.split(" ", 1)
        else:
            supplier_name = supplier_info
            text_description = supplier_info

        if supplier_name not in db:
            db[supplier_name] = []

        db[supplier_name].append({"file_id": file_id, "text": text_description})
        save_db()

        await update.message.reply_text(f"Сохранил! Поставщик: {supplier_name}, текст: {text_description} 😎")
    else:
        await handle_text(update, context)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_for_new_supplier))
    print("Бот запущен...")
    app.run_polling()