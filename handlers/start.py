import logging
from telegram import Update
from telegram.ext import ContextTypes
from middleware.auth import check_user_exists, show_terms, accept_terms_handler, decline_terms_handler
from middleware.ratelimit import rate_limit, rate_limit_callback
from database import log_activity

logger = logging.getLogger(__name__)

async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user has joined mandatory channels"""
    from config import MANDATORY_CHANNELS
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    user_id = update.effective_user.id
    not_joined = []
    
    for channel in MANDATORY_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel['id'], user_id=user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except Exception as e:
            # If bot is not admin in channel, skip check
            logger.error(f"Error checking channel {channel['name']}: {e}")
            continue
            
    if not_joined:
        keyboard = []
        for channel in not_joined:
            keyboard.append([InlineKeyboardButton(f"🔗 Join {channel['name']}", url=channel['url'])])
        
        keyboard.append([InlineKeyboardButton("🔄 Check Again", callback_data="check_join")])
        
        text = "⚠️ **Access Restricted!**\n\nYou must join our mandatory channels before using the bot:\n\n"
        for i, channel in enumerate(MANDATORY_CHANNELS, 1):
            text += f"{i}. {channel['name']}\n"
        
        text += "\nClick 'Check Again' after joining!"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return False
    return True

@rate_limit
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    # 1. Check Force Join
    if not await check_force_join(update, context):
        return
    
    # Check for referral code in start parameter
    if context.args and len(context.args) > 0:
        start_param = context.args[0]
        if start_param.startswith("ref_"):
            referral_code = start_param.replace("ref_", "")
            context.user_data['referral_code'] = referral_code
    
    # Check if user exists, if not create
    db_user = await check_user_exists(update, context)
    
    # Log activity
    log_activity(user_id, "start_command", {"username": user.username})
    
    # Skip terms and show main menu directly
    from handlers.menu import show_main_menu
    await show_main_menu(update, context)

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle check join button"""
    query = update.callback_query
    await query.answer("Checking...")
    
    if await check_force_join(update, context):
        await start_command(update, context)

async def start_with_referral(update: Update, context: ContextTypes.DEFAULT_TYPE, referral_code: str):
    """Handle start with referral code"""
    user_id = update.effective_user.id
    
    from services.referral import track_referral
    success, result = track_referral(user_id, referral_code)
    
    if success:
        await update.message.reply_text(
            "🎁 **Referral Tracked!**\n\n"
            "You were referred by someone. When you deposit ₹1000+, "
            "they will get ₹20 bonus!",
            parse_mode='Markdown'
        )
    else:
        # Invalid or self referral, ignore
        pass
    
    # Continue with normal start
    await start_command(update, context)

# Export handlers for registration
def get_handlers():
    from telegram.ext import CallbackQueryHandler
    
    return [
        CallbackQueryHandler(accept_terms_handler, pattern="^accept_terms$"),
        CallbackQueryHandler(decline_terms_handler, pattern="^decline_terms$"),
        CallbackQueryHandler(check_join_callback, pattern="^check_join$"),
    ]
