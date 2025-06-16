import os
import uuid
import zipfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from pdf2docx import Converter
from docx2pdf import convert
from docx import Document

user_actions = {}

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📄 PDF ➡️ Word", callback_data="pdf2word")],
        [InlineKeyboardButton("📝 Word ➡️ PDF", callback_data="word2pdf")],
        [InlineKeyboardButton("🗂 ZIP qılıw", callback_data="zip")],
        [InlineKeyboardButton("🖼 JPG ➡️ Word", callback_data="jpg2word")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Konvert qılıw túrin tanlan:", reply_markup=reply_markup)

# Tugmani bosganda
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    user_actions[user_id] = query.data
    await query.edit_message_text("Endi fayldı jiberin.")

# Fayl yuborilganda
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document or update.message.photo[-1]
    user_id = str(update.message.from_user.id)
    action = user_actions.get(user_id)

    if not action:
        await update.message.reply_text("Iltimas, /start basip, ameldi tanlan.")
        return

    file_path = f"{uuid.uuid4()}"
    if update.message.document:
        filename = update.message.document.file_name
        ext = os.path.splitext(filename)[1]
        file_path += ext
    else:
        file_path += ".jpg"

    tg_file = await file.get_file()
    await tg_file.download_to_drive(file_path)

    try:
        if action == "pdf2word" and file_path.endswith(".pdf"):
            output_path = file_path.replace(".pdf", ".docx")
            cv = Converter(file_path)
            cv.convert(output_path)
            cv.close()
            await update.message.reply_document(open(output_path, "rb"))

        elif action == "word2pdf" and file_path.endswith(".docx"):
            output_path = file_path.replace(".docx", ".pdf")
            convert(file_path, output_path)
            await update.message.reply_document(open(output_path, "rb"))

        elif action == "zip":
            output_path = file_path + ".zip"
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, arcname=os.path.basename(file_path))
            await update.message.reply_document(open(output_path, "rb"))

        elif action == "jpg2word" and file_path.endswith(".jpg"):
            output_path = file_path.replace(".jpg", ".docx")
            doc = Document()
            doc.add_picture(file_path)
            doc.save(output_path)
            await update.message.reply_document(open(output_path, "rb"))
        else:
            await update.message.reply_text("Fayl formatı nadurıs yaki tanlan?an amel nadurıs.")
    except Exception as e:
        await update.message.reply_text(f"Qátelik: {e}")
    finally:
        for f in [file_path, 
                  file_path.replace(".pdf", ".docx"), 
                  file_path.replace(".docx", ".pdf"), 
                  file_path + ".zip", 
                  file_path.replace(".jpg", ".docx")]:
            if os.path.exists(f):
                os.remove(f)

# Asosiy bot funksiyasi
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("⚠️ BOT_TOKEN topilmadi! Render Environment'da BOT_TOKEN ni qo‘shganingga ishonch hosil qil.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))

    print("✅ Bot ishga tushdi...")
    await app.run_polling()

# Botni ishga tushurish
if name == "main":
    import asyncio
    asyncio.run(main())
