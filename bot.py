#!/usr/bin/env python3
"""
Sparsh Store Bot - Main Entry Point
Telegram Bot for selling accounts with payment integration
"""

import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

from config import BOT_TOKEN, LOG_LEVEL, OWNER_ID
from database import init_supabase

# Import all handlers
from handlers.start import start_command, get_handlers as get_start_handlers
from handlers.menu import menu_command, get_handlers as get_menu_handlers
from handlers.buy import get_handlers as get_buy_handlers
from handlers.payment import get_handlers as get_payment_handlers
from handlers.profile import get_handlers as get_profile_handlers
from handlers.referral import get_handlers as get_referral_handlers
from handlers.support import get_handlers as get_support_handlers
from handlers.admin import get_handlers as get_admin_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

# Global variables for conversation states
SELECTING_COUNTRY, SELECTING_PRODUCT, SELECTING_QUANTITY, CONFIRM_PURCHASE = range(4)

async def error_handler(update, context):
    """Handle errors gracefully"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Send error message to user
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Something went wrong. Please try again later.\n\n"
                 "If issue persists, contact @ToxicStoreSupport"
        )
    
    # Also notify owner
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"⚠️ **Bot Error**\n\n"
                 f"Error: {str(context.error)[:200]}\n"
                 f"Update: {update}\n"
                 f"User: {update.effective_user.id if update else 'Unknown'}",
            parse_mode='Markdown'
        )
    except:
        pass

async def post_init(application: Application):
    """Post initialization setup"""
    logger.info("Bot started successfully!")
    
    # Notify owner that bot is running
    try:
        await application.bot.send_message(
            chat_id=OWNER_ID,
            text="✅ **Toxic Store Bot is now ONLINE!**\n\n"
                 "Bot is ready to serve users.\n\n"
                 f"Version: 1.0.0",
            parse_mode='Markdown'
        )
    except:
        pass

async def shutdown(application: Application):
    """Shutdown handler"""
    logger.info("Bot is shutting down...")
    
    # Notify owner
    try:
        await application.bot.send_message(
            chat_id=OWNER_ID,
            text="⚠️ **Toxic Store Bot is shutting down...**"
        )
    except:
        pass

def main():
    """Main function to run the bot"""
    
    # Initialize Supabase
    init_supabase()
    logger.info("Database initialized")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # Add all callback handlers from modules
    all_handlers = []
    all_handlers.extend(get_start_handlers())
    all_handlers.extend(get_menu_handlers())
    all_handlers.extend(get_buy_handlers())
    all_handlers.extend(get_payment_handlers())
    all_handlers.extend(get_profile_handlers())
    all_handlers.extend(get_referral_handlers())
    all_handlers.extend(get_support_handlers())
    all_handlers.extend(get_admin_handlers())
    
    for handler in all_handlers:
        application.add_handler(handler)
    
    # Add message handler for text messages (for UTR, amount, etc.)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Setup post init and shutdown
    application.post_init = post_init
    application.post_shutdown = shutdown
    
    # Run the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=["message", "callback_query"])

async def handle_text_messages(update, context):
    """Handle text messages that are not commands"""
    from handlers.payment import handle_utr_message, handle_amount_message, handle_crypto_amount

    
    # Check if waiting for specific input
    if context.user_data.get('waiting_for_utr'):
        await handle_utr_message(update, context)
    elif context.user_data.get('waiting_for_amount'):
        await handle_amount_message(update, context)
    elif context.user_data.get('waiting_for_crypto_amount'):
        await handle_crypto_amount(update, context)
    elif context.user_data.get('admin_action') == 'broadcast':
        from handlers.admin import broadcast_command
        await broadcast_command(update, context)
    else:
        # Default response
        await update.message.reply_text(
            "❓ Unknown command.\n\n"
            "Use /menu to see available options."
        )

if __name__ == "__main__":
    main()
