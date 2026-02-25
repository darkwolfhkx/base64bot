import base64
import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Flask app for health checks (Render ke liye zaroori)
app = Flask(__name__)

# Logging set karein
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variable se token lein
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable set nahi hai!")

PORT = int(os.environ.get('PORT', 8080))

# Bot application banayein
application = Application.builder().token(TOKEN).build()
bot = Bot(token=TOKEN)

# Flask ka health check endpoint
@app.route('/health')
@app.route('/')
def health():
    return "Bot is running!", 200

# Flask webhook endpoint (Telegram yahan messages bhejega)
@app.route(f'/webhook', methods=['POST'])
def webhook():
    """Telegram se aane wale updates handle karein"""
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        asyncio.run(application.process_update(update))
        return 'OK', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Base64 Encoder/Decoder Bot mein khush amdeed!\n\n"
        "• Normal text bhejein → Base64 mein encode ho ga\n"
        "• Base64 text bhejein → decode ho ga\n\n"
        "Bas text likh kar bhej dein!"
    )

# Check karein ke text Base64 hai ya nahi
def is_base64(text):
    try:
        if len(text) % 4 != 0:
            return False
        decoded = base64.b64decode(text).decode('utf-8')
        re_encoded = base64.b64encode(decoded.encode()).decode()
        return re_encoded == text
    except:
        return False

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    try:
        if is_base64(user_text):
            decoded = base64.b64decode(user_text).decode('utf-8')
            await update.message.reply_text(f"🔓 **Decoded:**\n`{decoded}`", parse_mode='Markdown')
        else:
            encoded = base64.b64encode(user_text.encode()).decode()
            await update.message.reply_text(f"🔒 **Encoded (Base64):**\n`{encoded}`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Webhook setup function
async def setup_webhook():
    """Bot ko webhook set karne ka function"""
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    
    # Current webhook info check karein
    webhook_info = await bot.get_webhook_info()
    
    if webhook_info.url != webhook_url:
        # Naya webhook set karein
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=['message', 'callback_query']
        )
        logger.info(f"Webhook set to: {webhook_url}")
    else:
        logger.info("Webhook already configured correctly")

# Main function jo Flask app chalay gi
if __name__ == '__main__':
    try:
        # Handlers register karein
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Bot initialize karein
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Webhook setup async function chalayein
        loop.run_until_complete(setup_webhook())
        
        # Flask app start karein
        app.run(host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"Startup error: {e}")
