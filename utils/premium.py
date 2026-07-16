import logging
from telegram import Update, User
from database import get_user, update_user

logger = logging.getLogger(__name__)

# Cache for premium status (to avoid too many API calls)
premium_cache = {}

async def check_premium_user(user: User) -> bool:
    """
    Check if a user has Telegram Premium
    Uses the premium field from Telegram User object
    """
    try:
        # Telegram Bot API v6.1+ has 'is_premium' field
        if hasattr(user, 'is_premium') and user.is_premium:
            return True
        
        # Also check in cache if we have it stored
        if user.id in premium_cache:
            return premium_cache[user.id]
        
        return False
    except Exception as e:
        logger.error(f"Error checking premium status for user {user.id}: {e}")
        return False

async def get_premium_status(user_id: int, context) -> bool:
    """
    Get premium status by making API call
    """
    try:
        # Try to get chat member info (works for bots as well)
        chat_member = await context.bot.get_chat_member(chat_id=user_id, user_id=user_id)
        
        # Check if user has premium status from Telegram
        # Note: Bot API might not directly expose this, so we rely on user object
        if hasattr(chat_member.user, 'is_premium') and chat_member.user.is_premium:
            premium_cache[user_id] = True
            return True
        
        premium_cache[user_id] = False
        return False
    except Exception as e:
        logger.error(f"Error getting premium status: {e}")
        return False

def is_premium_user_from_context(context, user_id: int) -> bool:
    """
    Check if user is premium from stored context data
    """
    if 'premium_users' not in context.bot_data:
        return False
    
    premium_users = context.bot_data.get('premium_users', {})
    return premium_users.get(user_id, False)

async def update_premium_status_in_db(user_id: int, is_premium: bool):
    """
    Update premium status in database
    """
    try:
        update_user(user_id, {"is_premium": is_premium})
    except Exception as e:
        logger.error(f"Error updating premium status in DB: {e}")

async def store_premium_status(context, user_id: int, is_premium: bool):
    """
    Store premium status in context.bot_data
    """
    if 'premium_users' not in context.bot_data:
        context.bot_data['premium_users'] = {}
    
    context.bot_data['premium_users'][user_id] = is_premium

def get_premium_emoji(is_premium: bool) -> str:
    """
    Get premium badge emoji for user
    """
    if is_premium:
        return "👑"  # Crown for premium users
    return "👤"  # Normal user icon

def get_premium_badge(is_premium: bool) -> str:
    """
    Get premium badge text
    """
    if is_premium:
        return "⭐️ **Premium User** ⭐️"
    return ""

def get_premium_features(is_premium: bool) -> list:
    """
    Get list of features available to user based on premium status
    """
    common_features = [
        "• Buy Telegram accounts",
        "• Wallet system",
        "• Referral earnings",
        "• 24/7 support"
    ]
    
    premium_features = [
        "• Priority support ⚡",
        "• Early access to new accounts 🔥",
        "• Special discounts 💎",
        "• VIP account categories 👑",
        "• Bulk purchase benefits 📦"
    ]
    
    if is_premium:
        return common_features + premium_features
    return common_features

def get_premium_upgrade_message(is_premium: bool) -> str:
    """
    Get premium upgrade message for non-premium users
    """
    if is_premium:
        return "✨ You are already a Premium user! Enjoy exclusive benefits."
    
    message = """
🌟 **Upgrade to Telegram Premium!**

Get exclusive benefits on our bot:
• Priority support
• Early access to new accounts
• Special discounts
• VIP account categories
• Bulk purchase benefits

**Note:** This bot recognizes Telegram Premium users and provides extra features automatically.
"""
    return message

def format_user_display(user_id: int, username: str = None, is_premium: bool = False) -> str:
    """
    Format user display with premium badge
    """
    badge = get_premium_emoji(is_premium)
    
    if username:
        display = f"{badge} @{username}"
    else:
        display = f"{badge} User #{user_id}"
    
    if is_premium:
        display += " ⭐️"
    
    return display

async def handle_premium_user(update: Update, context, user: User) -> bool:
    """
    Main handler for premium user detection and processing
    Call this when user starts the bot
    """
    try:
        is_premium = await check_premium_user(user)
        
        # Store in context for quick access
        await store_premium_status(context, user.id, is_premium)
        
        # Update in database
        await update_premium_status_in_db(user.id, is_premium)
        
        # Log premium status
        if is_premium:
            logger.info(f"Premium user detected: {user.id} ({user.username})")
        else:
            logger.info(f"Regular user: {user.id} ({user.username})")
        
        return is_premium
    except Exception as e:
        logger.error(f"Error in handle_premium_user: {e}")
        return False

def get_premium_discount(is_premium: bool, base_price: float) -> float:
    """
    Calculate premium discount (5% off for premium users)
    """
    if is_premium:
        discount = base_price * 0.05  # 5% discount
        return round(base_price - discount, 2)
    return base_price

def get_premium_welcome_message(is_premium: bool, username: str = None) -> str:
    """
    Get personalized welcome message based on premium status
    """
    if is_premium:
        return f"""
👑 **Welcome Premium User {username or 'VIP'}!** 👑

You get exclusive benefits:
• ⚡ Priority support
• 💎 Special discounts on all accounts
• 🔥 Early access to new stock
• 📦 Bulk purchase benefits

Use /menu to start shopping!
"""
    else:
        return f"""
✨ **Welcome {username or 'User'}!** ✨

Upgrade to Telegram Premium for exclusive benefits:
• Priority support
• Special discounts
• VIP account access

Use /menu to start shopping!
"""
