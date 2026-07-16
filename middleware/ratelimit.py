import time
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Store user request timestamps
user_requests = {}

# Configuration
MAX_REQUESTS_PER_MINUTE = 30
REQUEST_WINDOW = 60  # seconds

def clean_old_requests(user_id):
    """Clean requests older than window"""
    if user_id not in user_requests:
        return
    
    current_time = time.time()
    user_requests[user_id] = [
        req_time for req_time in user_requests[user_id]
        if current_time - req_time < REQUEST_WINDOW
    ]
    
    if not user_requests[user_id]:
        del user_requests[user_id]

def is_rate_limited(user_id):
    """Check if user is rate limited"""
    clean_old_requests(user_id)
    
    if user_id not in user_requests:
        user_requests[user_id] = []
        return False
    
    if len(user_requests[user_id]) >= MAX_REQUESTS_PER_MINUTE:
        return True
    
    return False

def add_request(user_id):
    """Add a request timestamp for user"""
    if user_id not in user_requests:
        user_requests[user_id] = []
    
    user_requests[user_id].append(time.time())

def rate_limit(func):
    """Decorator to apply rate limiting"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if is_rate_limited(user_id):
            # Send rate limit message
            await update.message.reply_text(
                "⏳ **Slow down!**\n\n"
                f"You are sending too many requests. Please wait {REQUEST_WINDOW} seconds before trying again.\n\n"
                f"Limit: {MAX_REQUESTS_PER_MINUTE} requests per minute.",
                parse_mode='Markdown'
            )
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return
        
        add_request(user_id)
        return await func(update, context, *args, **kwargs)
    return wrapper

def rate_limit_callback(func):
    """Decorator for callback queries rate limiting"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if is_rate_limited(user_id):
            query = update.callback_query
            await query.answer("⏳ Slow down! Please wait a moment.", show_alert=True)
            return
        
        add_request(user_id)
        return await func(update, context, *args, **kwargs)
    return wrapper

def get_user_stats(user_id):
    """Get rate limit stats for a user"""
    clean_old_requests(user_id)
    
    if user_id not in user_requests:
        return {"count": 0, "limit": MAX_REQUESTS_PER_MINUTE, "remaining": MAX_REQUESTS_PER_MINUTE}
    
    count = len(user_requests[user_id])
    remaining = max(0, MAX_REQUESTS_PER_MINUTE - count)
    
    return {
        "count": count,
        "limit": MAX_REQUESTS_PER_MINUTE,
        "remaining": remaining
    }

def reset_user_limits(user_id):
    """Reset rate limits for a user"""
    if user_id in user_requests:
        del user_requests[user_id]
        return True
    return False
