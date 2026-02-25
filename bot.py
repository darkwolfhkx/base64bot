import base64
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

def is_base64(s):
    try:
        return base64.b64encode(base64.b64decode(s)).decode() == s
    except:
        return False

async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    if is_base64(text):

        try:
            decoded = base64.b64decode(text).decode()
            await update.message.reply_text(f"Decoded:\n{decoded}")

        except:
            await update.message.reply_text("Invalid Base64")

    else:

        encoded = base64.b64encode(text.encode()).decode()

        await update.message.reply_text(f"Encoded:\n{encoded}")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, auto))

app.run_polling()
