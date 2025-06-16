import os
import uuid
import zipfile
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf2docx import Converter
from docx import Document
from docx2pdf import convert
from PIL import Image

TOKEN = 'YOUR_BOT_TOKEN'  # <-- bu yerga o'z tokeningni yoz

# 📁 Fayllar saqlanadigan vaqtinchalik papka
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 🏁 Start buyrug‘i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['PDF ➤ Word', 'Word ➤ PDF'], ['JPG ➤ Word', 'ZIP File']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Fayl konvertatsiya botiga xush kelibsiz!\nFayl turini tanlang:", reply_markup=reply_markup)

# 🖱 Tanlovni eslab qolish
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    context.user_data["choice"] = choice
    await update.message.reply_text(f"Endi faylni yuboring: ({choice})")

# 📄 Fayl kelganda
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        await update.message.reply_text("Iltimos, hujjat faylini yuboring.")
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
            output_path = filepath.replace('.jpg', '.docx').replace('.jpeg', '.docx').replace('.png', '.docx')
            doc = Document()
            doc.add_picture(filepath, width=docx.shared.Inches(6))
            doc.save(output_path)

        elif choice == 'ZIP File':
            output_path = filepath + ".zip"
            with zipfile.ZipFile(output_path, 'w') as zipf:
                zipf.write(filepath, arcname=os.path.basename(filepath))

        else:
            await update.message.reply_text("Tanlov mos emas yoki fayl formati noto‘g‘ri.")
            return

        await update.message.reply_document(document=open(output_path, 'rb'))

    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")

    finally:
        for f in os.listdir(TEMP_DIR):
            os.remove(os.path.join(TEMP_DIR, f))

# 🔧 Botni ishga tushirish
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
