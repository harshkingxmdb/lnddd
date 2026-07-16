import logging
from telegram import Update
from telegram.ext import ContextTypes
from middleware.auth import check_user_exists, show_terms, accept_terms_handler, decline_terms_handler
from middleware.ratelimit import rate_limit, rate_limit_callback
from utils.premium import handle_premium_user
from database import log_activity

logger = logging.getLogger(__name__)

@rate_limit
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    # Check for referral code in start parameter
    if context.args and len(context.args) > 0:
        start_param = context.args[0]
        if start_param.startswith("ref_"):
            referral_code = start_param.replace("ref_", "")
            context.user_data['referral_code'] = referral_code
    
    # Check if user exists, if not create
    db_user = await check_user_exists(update, context)
    
    # Check premium status
    is_premium = await handle_premium_user(update, context, user)
    context.user_data['is_premium'] = is_premium
    
    # Log activity
    log_activity(user_id, "start_command", {"username": user.username})
    
    # Check if terms already accepted
    if db_user and db_user.get('terms_accepted'):
        from handlers.menu import show_main_menu
        await show_main_menu(update, context)
    else:
        await show_terms(update, context)

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
    ]
