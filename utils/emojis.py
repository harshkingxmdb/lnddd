# Premium Emojis for the bot
# These emojis work for all users, but premium users get special treatment

# Standard premium emojis (visible to everyone)
PREMIUM_EMOJIS = {
    "coin": "🪙",           # Payment/Add Funds
    "gift": "🎁",           # Referral bonus/Rewards
    "crown": "👑",          # VIP/Premium user
    "lightning": "⚡",       # Fast delivery/Instant
    "shield": "🛡️",         # Security/Verified
    "gem": "💎",            # Premium accounts
    "fire": "🔥",           # Hot deals/Special offers
    "star": "⭐",           # Rating/Favorite
    "rocket": "🚀",         # Success/Launch
    "sparkles": "✨",        # New/Special
    "lock": "🔒",           # Secure/Private
    "unlock": "🔓",         # Access granted
    "check": "✅",           # Success/Verified
    "warning": "⚠️",         # Alert/Warning
    "info": "ℹ️",           # Information
    "question": "❓",        # Help/Question
    "cart": "🛒",           # Shopping/Buy
    "wallet": "💰",          # Wallet/Balance
    "profile": "👤",         # User profile
    "support": "🆘",         # Customer support
    "menu": "📋",           # Menu
    "orders": "📦",         # Orders
    "payment": "💳",         # Payment
    "crypto": "🪙",          # Cryptocurrency
    "uparrow": "🔼",         # Increase
    "downarrow": "🔽",       # Decrease
    "back": "↩️",            # Back button
    "next": "▶️",           # Next button
    "previous": "◀️",        # Previous button
    "cancel": "❌",          # Cancel/Decline
    "accept": "✅",          # Accept/Confirm
    "pending": "⏳",         # Pending status
    "success": "✅",         # Success status
    "failed": "❌",          # Failed status
    "warning_sign": "⚠️",     # Warning
    "ban": "🚫",             # Banned
    "admin": "🔧",           # Admin panel
    "stats": "📊",           # Statistics
    "broadcast": "📢",       # Broadcast message
}

def get_emoji(key):
    """Get emoji by key"""
    return PREMIUM_EMOJIS.get(key, "📌")

def format_with_emoji(text, emoji_key):
    """Format text with emoji prefix"""
    emoji = get_emoji(emoji_key)
    return f"{emoji} {text}"

def get_status_emoji(status):
    """Get emoji for order/payment status"""
    status_emojis = {
        "pending": "⏳",
        "completed": "✅",
        "verified": "✅",
        "failed": "❌",
        "cancelled": "❌",
        "refunded": "🔄",
        "available": "✅",
        "sold": "❌",
        "blocked": "🚫"
    }
    return status_emojis.get(status.lower(), "📌")

def get_button_emoji(button_type):
    """Get emoji for button type"""
    button_emojis = {
        "buy": "🛒",
        "funds": "💰",
        "earn": "🎁",
        "profile": "👤",
        "support": "🆘",
        "howto": "ℹ️",
        "back": "↩️",
        "confirm": "✅",
        "cancel": "❌",
        "delete": "🗑️",
        "edit": "✏️",
        "add": "➕",
        "remove": "➖",
        "next": "▶️",
        "previous": "◀️"
    }
    return button_emojis.get(button_type, "📌")
