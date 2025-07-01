import os
import uuid
import zipfile
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf2docx import Converter
from docx import Document
from docx.shared import Inches
from PIL import Image

# TOKEN from environment
TOKEN = os.environ.get("TOKEN")

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['PDF ➤ Word', 'Word ➤ PDF'], ['JPG ➤ Word', 'ZIP File']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Fayl konvertatsiya botına xosh kelibsiz!\nFayl túrin tańlań:",
        reply_markup=reply_markup
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    context.user_data["choice"] = choice
    await update.message.reply_text(f"Endi fayldı jiberiń: ({choice})")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        await update.message.reply_text("Iltimas, fayl jiberiń.")
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
            # ⚠️ docx2pdf requires Windows/macOS, comment out if on Linux
            from docx2pdf import convert
            convert(filepath, output_path)

        elif choice == 'JPG ➤ Word' and ext in ['jpg', 'jpeg', 'png']:
            output_path = filepath.rsplit('.', 1)[0] + '.docx'
            docx_file = Document()
            docx_file.add_picture(filepath, width=Inches(6))
            docx_file.save(output_path)

        elif choice == 'ZIP File':
            output_path = filepath + ".zip"
            with zipfile.ZipFile(output_path, 'w') as zipf:
                zipf.write(filepath, arcname=os.path.basename(filepath))

        else:
            await update.message.reply_text("Fayl túri yaki tańlaw nadurıs.")
            return

        with open(output_path, 'rb') as f:
            await update.message.reply_document(document=f)

    except Exception as e:
        await update.message.reply_text(f"Qátelik júz berdi: {e}")

    finally:
        for f in os.listdir(TEMP_DIR):
            os.remove(os.path.join(TEMP_DIR, f))

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot iske tústi...")
    app.run_polling()

if __name__ == "__main__":
    main()
