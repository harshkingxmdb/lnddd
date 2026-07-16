from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_reply_keyboard():
    """Main menu reply keyboard"""
    keyboard = [
        [KeyboardButton("🛒 Buy Accounts"), KeyboardButton("💰 Add Funds")],
        [KeyboardButton("🎁 Earn Money"), KeyboardButton("👤 My Profile")],
        [KeyboardButton("🆘 Support"), KeyboardButton("ℹ️ How to Use")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_reply_keyboard():
    """Cancel/Back reply keyboard"""
    keyboard = [
        [KeyboardButton("↩️ Back to Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_reply_keyboard():
    """Admin reply keyboard"""
    keyboard = [
        [KeyboardButton("📦 Add Stock"), KeyboardButton("➕ Add Country")],
        [KeyboardButton("👁️ View Stock"), KeyboardButton("📋 View Orders")],
        [KeyboardButton("✅ Verify Payment"), KeyboardButton("📊 Stats")],
        [KeyboardButton("📢 Broadcast"), KeyboardButton("🚫 Ban User")],
        [KeyboardButton("↩️ Back to Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_remove_keyboard():
    """Remove custom keyboard"""
    from telegram import ReplyKeyboardRemove
    return ReplyKeyboardRemove()
