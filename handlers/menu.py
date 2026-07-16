import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.inline import get_main_menu_keyboard
from middleware.auth import require_auth
from middleware.ratelimit import rate_limit, rate_limit_callback
from database import get_user
from utils.formatters import format_wallet_balance
from utils.emojis import get_emoji

logger = logging.getLogger(__name__)

@require_auth
@rate_limit
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command"""
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu to user"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await start_command(update, context)
        return
    
    balance = user.get('wallet_balance', 0)
    is_premium = context.user_data.get('is_premium', False)
    
    welcome_text = f"""
{get_emoji('star')} **Welcome to Toxic Store Bot!** {get_emoji('star')}

{get_emoji('wallet')} {format_wallet_balance(balance)}

{get_emoji('rocket')} **High-Quality Telegram Accounts & Sessions**
{get_emoji('lightning')} Instant Delivery • Auto-Replacement

Select a service from the keyboard below:
"""
    
    if is_premium:
        welcome_text += f"\n{get_emoji('crown')} **Premium User Benefits Active!**"
    
    keyboard = get_main_menu_keyboard()
    
    # Check if it's a callback query or message
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await query.answer()
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

@rate_limit_callback
async def back_to_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to menu button"""
    query = update.callback_query
    await query.answer()
    await show_main_menu(update, context)

@rate_limit_callback
async def how_to_use_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle how to use button"""
    query = update.callback_query
    await query.answer()
    
    from utils.formatters import format_how_to_use
    from keyboards.inline import get_back_keyboard
    
    how_to_text = format_how_to_use()
    
    await query.edit_message_text(
        how_to_text,
        reply_markup=get_back_keyboard("back_to_menu"),
        parse_mode='Markdown'
    )

# Export handlers
def get_handlers():
    from telegram.ext import CallbackQueryHandler, CommandHandler
    
    return [
        CommandHandler("menu", menu_command),
        CallbackQueryHandler(back_to_menu_callback, pattern="^back_to_menu$"),
        CallbackQueryHandler(how_to_use_callback, pattern="^how_to_use$"),
    ]
