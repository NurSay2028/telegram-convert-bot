Нұрсұлтан Халмуратов, [17.06.2025 10:23]
import os
import uuid
import zipfile
import threading
import time
import requests
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from pdf2docx import Converter
from docx import Document
from docx.shared import Inches
from docx2pdf import convert
from PIL import Image

# 🎯 Tokenni o‘zgartirmaymiz — aynan sen berganing qoladi
TOKEN = '8184845398:AAEXBTaU054xZAjlFLUUVSsxmvcrCeuiL8k'
WEBHOOK_URL = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"

# 📁 Fayllar saqlanadigan vaqtinchalik papka
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ⚙️ Flask ilova
flask_app = Flask(name)
telegram_app = Application.builder().token(TOKEN).build()

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['PDF ➤ Word', 'Word ➤ PDF'], ['JPG ➤ Word', 'ZIP File']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Fayl konvertatsiya botına xosh kelibsiz!\nFayl turin tańlań:", reply_markup=reply_markup)

# Tanlovni saqlash
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    context.user_data["choice"] = choice
    await update.message.reply_text(f"Endi fayldı jiberiń: ({choice})")

# Faylni qabul qilish va konvertatsiya
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        await update.message.reply_text("Iltimas, hujjet faylın jiberiń.")
        return

    file = await doc.get_file()
    filename = doc.file_name
    ext = filename.split('.')[-1].lower()
    uid = str(uuid.uuid4())
    filepath = os.path.join(TEMP_DIR, f"{uid}_{filename}")
    await file.download_to_drive(filepath)

    choice = context.user_data.get("choice", "")
    output_path = ""

    try:
        if choice == 'PDF ➤ Word' and ext == 'pdf':
            output_path = filepath.replace('.pdf', '.docx')
            cv = Converter(filepath)
            cv.convert(output_path)
            cv.close()

        elif choice == 'Word ➤ PDF' and ext == 'docx':
            output_path = filepath.replace('.docx', '.pdf')
            convert(filepath, output_path)

        elif choice == 'JPG ➤ Word' and ext in ['jpg', 'jpeg', 'png']:
            output_path = filepath.rsplit('.', 1)[0] + '.docx'
            docx_doc = Document()
            docx_doc.add_picture(filepath, width=Inches(6))
            docx_doc.save(output_path)

        elif choice == 'ZIP File':
            output_path = filepath + ".zip"
            with zipfile.ZipFile(output_path, 'w') as zipf:
                zipf.write(filepath, arcname=os.path.basename(filepath))

        else:
            await update.message.reply_text("Tańlaw durıs emes yamasa fayl formatı nadurıs.")
            return

        await update.message.reply_document(document=open(output_path, 'rb'))

    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")

    finally:
        for f in os.listdir(TEMP_DIR):
            os.remove(os.path.join(TEMP_DIR, f))

# 💤 Bot uxlab qolmasligi uchun ping-funktsiya
def keep_awake():
    while True:
        try:
            requests.get(f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/")
        except:
            pass
        time.sleep(600)

threading.Thread(target=keep_awake, daemon=True).start()

# Handlerlar
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
telegram_app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

# Webhook route
@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "ok"

# Health check
@flask_app.route("/", methods=["GET"])
def health():
    return "Bot is alive!", 200

Нұрсұлтан Халмуратов, [17.06.2025 10:23]
# Botni ishga tushurish
if __name__ == "__main__":
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=WEBHOOK_URL
    )
