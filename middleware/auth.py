import logging
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from database import get_user, create_user, accept_terms
from utils.formatters import format_block_quote
from keyboards.inline import get_terms_keyboard

logger = logging.getLogger(__name__)

# User data storage for caching (optional)
user_cache = {}

def get_user_safe(user_id):
    """Get user with caching"""
    if user_id in user_cache:
        return user_cache[user_id]
    
    user = get_user(user_id)
    if user:
        user_cache[user_id] = user
    return user

def clear_user_cache(user_id):
    """Clear user from cache"""
    if user_id in user_cache:
        del user_cache[user_id]

async def check_user_exists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user exists in database, if not create"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name
    
    user = get_user(user_id)
    
    if not user:
        # Create new user
        user = create_user(user_id, username, full_name)
        if user:
            logger.info(f"New user created: {user_id} ({username})")
    
    # Store user in context
    context.user_data['user'] = user
    
    return user

async def check_terms_accepted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user has accepted terms"""
    user = context.user_data.get('user')
    
    if not user:
        user = await check_user_exists(update, context)
    
    if user and user.get('terms_accepted'):
        return True
    
    # User hasn't accepted terms, show terms
    await show_terms(update, context)
    return False

async def show_terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show terms and conditions with block quotes"""
    
    terms_text = format_block_quote(
        "⚠️ TERMS AND CONDITIONS\n\n"
        "Please read and accept our terms to use this bot:"
    )
    
    terms_text += "\n\n" + format_block_quote(
        "📌 Account Policy\n"
        "• These accounts are for testing/educational purposes\n"
        "• We are NOT responsible for any ban/freeze after login\n"
        "• Use Telegram X or official apps for best stability"
    )
    
    terms_text += "\n\n" + format_block_quote(
        "📌 Refund Policy\n"
        "• NO REFUNDS under any circumstances except 'No OTP Received'\n"
        "• All sales are final. Buy at your own risk"
    )
    
    terms_text += "\n\n" + format_block_quote(
        "📌 Misuse\n"
        "• Any illegal activity will result in a ban"
    )
    
    terms_text += "\n\n✅ By clicking 'Accept', you agree to all the terms"
    
    keyboard = get_terms_keyboard()
    
    # Check if it's a callback query or message
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            terms_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            terms_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

async def accept_terms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle terms acceptance"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Update database
    user = accept_terms(user_id)
    
    if user:
        context.user_data['user'] = user
        clear_user_cache(user_id)
        
        await query.edit_message_text(
            "✅ **Terms Accepted!**\n\nWelcome to Toxic Store Bot!\n\nUse /menu to get started.",
            parse_mode='Markdown'
        )
        
        # Show menu after terms acceptance
        from handlers.menu import show_main_menu
        await show_main_menu(update, context)
    else:
        await query.edit_message_text(
            "❌ Something went wrong. Please try again with /start"
        )

async def decline_terms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle terms decline"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "❌ **Terms Declined**\n\n"
            "You must accept the terms and conditions to use this bot.\n\n"
            "Type /start to try again.",
            parse_mode='Markdown'
        )
    elif update.message:
        await update.message.reply_text(
            "❌ **Terms Declined**\n\n"
            "You must accept the terms and conditions to use this bot.\n\n"
            "Type /start to try again.",
            parse_mode='Markdown'
        )

async def check_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is banned"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if user and user.get('is_banned'):
        await update.message.reply_text(
            "🚫 **You are banned from using this bot.**\n\n"
            "Contact support for more information.",
            parse_mode='Markdown'
        )
        return True
    
    return False

def require_auth(func):
    """Decorator to require user authentication"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Check if user is banned
        if await check_banned(update, context):
            return
        
        # Check if user exists
        user = await check_user_exists(update, context)
        if not user:
            await update.message.reply_text("❌ Error loading your profile. Please try /start again.")
            return
        
        # Check if terms accepted
        if not user.get('terms_accepted'):
            await show_terms(update, context)
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def require_admin(func):
    """Decorator to require admin access"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        from config import ADMIN_IDS
        if user_id not in ADMIN_IDS:
            if update.callback_query:
                await update.callback_query.answer("🚫 Access Denied!", show_alert=True)
            else:
                await update.message.reply_text("🚫 **Access Denied!**\n\nYou don't have permission to use this command.", parse_mode='Markdown')
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper
