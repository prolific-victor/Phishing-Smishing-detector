import os
import sys
import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Add parent directory to path to allow importing from backend if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup your Telegram bot token here
# Get one from @BotFather on Telegram
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
API_BASE = "http://127.0.0.1:8000/api"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "🛡️ Welcome to CyberGuard AI Assistant!\n\n"
        "I can help you detect phishing links and suspicious messages.\n"
        "Just send me any URL or text message, and I'll analyze the risk for you."
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_message = (
        "How to use me:\n"
        "1. Send a standalone link (e.g., http://example.com) to perform a URL scan.\n"
        "2. Forward or send a suspicious SMS/WhatsApp message to perform a deep text analysis.\n"
        "3. Wait a few seconds for my risk assessment."
    )
    await update.message.reply_text(help_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and URLs."""
    text = update.message.text
    
    # Send a typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        # Simple heuristic to determine if it's purely a URL
        url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        urls = re.findall(url_regex, text)
        
        endpoint = "/scan/message"
        payload = text
        
        # If the message is exactly a URL, or starts with "Check this link"
        if urls and text.strip() == urls[0][0]:
            endpoint = "/scan/url"
            payload = urls[0][0]
        elif urls and "check" in text.lower():
            endpoint = "/scan/url"
            payload = urls[0][0]
            
        # Call the FastAPI backend
        response = requests.post(
            f"{API_BASE}{endpoint}", 
            json={"content": payload},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Format the output for Telegram
            risk_emoji = "✅"
            if result['risk_level'] == 'Suspicious': risk_emoji = "⚠️"
            if result['risk_level'] == 'Phishing': risk_emoji = "🚨"
            
            indicators_text = ""
            if result['indicators']:
                indicators_text = "\nIndicators:\n- " + "\n- ".join(result['indicators'])
                
            reply = (
                f"{risk_emoji} {result['risk_level']} Alert\n\n"
                f"Risk Score: {result['risk_score']}%\n"
                f"{indicators_text}\n\n"
                f"Recommendation: {result['recommendation']}"
            )
            
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("❌ Error: The AI backend is currently unreachable. Please try again later.")
            
    except Exception as e:
        print(f"Error handling message: {e}")
        await update.message.reply_text("❌ An error occurred while analyzing the message. Ensure the backend server is running.")

def main() -> None:
    """Start the bot."""
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("WARNING: Please set your actual TELEGRAM_TOKEN in bot/telegram_bot.py")
        print("You can get one from @BotFather on Telegram.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    print("Telegram Bot is running...")
    application.run_polling(allowed_updates=Update.ALL)

if __name__ == "__main__":
    main()
