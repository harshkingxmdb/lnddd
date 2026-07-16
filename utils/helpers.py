import random
import string
import uuid
from datetime import datetime
from utils.emojis import get_emoji

def generate_order_id():
    """Generate unique order ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{timestamp}{random_part}"

def generate_referral_code(user_id):
    """Generate unique referral code for user"""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"REF{user_id}{random_part}"[:20]

def generate_txn_id():
    """Generate unique transaction ID"""
    return str(uuid.uuid4())[:8]

def calculate_total(price, quantity):
    """Calculate total amount"""
    return price * quantity

def get_referral_link(bot_username, referral_code):
    """Generate referral link"""
    return f"https://t.me/{bot_username}?start=ref_{referral_code}"

def truncate_text(text, max_length=50):
    """Truncate text to max length"""
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text

def escape_markdown(text):
    """Escape markdown special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_time_ago(timestamp):
    """Format timestamp as time ago"""
    if not timestamp:
        return "Unknown"
    
    try:
        if isinstance(timestamp, str):
            from dateutil import parser
            dt = parser.parse(timestamp)
        else:
            dt = timestamp
        
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365} years ago"
        elif diff.days > 30:
            return f"{diff.days // 30} months ago"
        elif diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hours ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minutes ago"
        else:
            return "Just now"
    except:
        return "Recently"

def split_list(data, chunk_size):
    """Split list into chunks"""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def format_number(num):
    """Format number with K/M/B suffixes"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)

def get_bot_username(context):
    """Get bot username from context"""
    try:
        return context.bot.username
    except:
        return "ToxicStoreBot"
