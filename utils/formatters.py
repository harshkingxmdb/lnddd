import re
from datetime import datetime
from utils.emojis import get_emoji, get_status_emoji

def format_block_quote(text):
    """Format text as block quote for Telegram"""
    lines = text.split('\n')
    quoted_lines = [f"> {line}" for line in lines]
    return '\n'.join(quoted_lines)

def format_spoiler(text):
    """Format text as spoiler (hidden until tapped)"""
    return f"||{text}||"

def format_bold(text):
    """Format text as bold"""
    return f"*{text}*"

def format_italic(text):
    """Format text as italic"""
    return f"_{text}_"

def format_code(text):
    """Format text as code"""
    return f"`{text}`"

def format_pre(text):
    """Format text as pre-formatted"""
    return f"```\n{text}\n```"

def format_link(text, url):
    """Format text as link"""
    return f'<a href="{url}">{text}</a>'

def format_mono(text):
    """Format text as monospace"""
    return f"<code>{text}</code>"

def format_utr(utr_number):
    """Format UTR number with spoiler"""
    return format_spoiler(utr_number)

def format_order_id(order_id):
    """Format order ID (show first 8 chars)"""
    if len(order_id) > 8:
        return order_id[:8] + "..."
    return order_id

def format_phone_number(phone):
    """Format phone number with spoiler for privacy"""
    if len(phone) > 6:
        hidden_part = "*" * (len(phone) - 6)
        visible_part = phone[:3] + phone[-3:]
        return f"{visible_part}{hidden_part}"
    return format_spoiler(phone)

def format_amount(amount):
    """Format amount with rupee symbol"""
    return f"₹{amount:,.2f}"

def format_date(date_str):
    """Format date string to readable format"""
    if isinstance(date_str, str):
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%d %b %Y, %I:%M %p")
        except:
            return date_str
    return str(date_str)

def format_wallet_balance(balance):
    """Format wallet balance with emoji"""
    emoji = get_emoji("wallet")
    return f"{emoji} Balance: ₹{balance:,.2f}"

def format_order_summary(order):
    """Format order summary for display"""
    order_id = format_order_id(order.get('order_id', 'N/A'))
    amount = order.get('amount', 0)
    status = order.get('status', 'pending')
    status_emoji = get_status_emoji(status)
    date = format_date(order.get('created_at', ''))
    
    summary = f"""
{get_emoji('orders')} **Order #{order_id}**
{get_emoji('payment')} Amount: ₹{amount:,.2f}
{status_emoji} Status: {status.upper()}
{get_emoji('info')} Date: {date}
"""
    return summary

def format_payment_summary(payment):
    """Format payment summary for display"""
    txn_id = payment.get('txn_id', 'N/A')
    amount = payment.get('amount', 0)
    status = payment.get('status', 'pending')
    status_emoji = get_status_emoji(status)
    date = format_date(payment.get('created_at', ''))
    utr = payment.get('utr_number', 'N/A')
    
    summary = f"""
{get_emoji('payment')} **Payment #{txn_id}**
{get_emoji('payment')} Amount: ₹{amount:,.2f}
{status_emoji} Status: {status.upper()}
{get_emoji('info')} Date: {date}
{get_emoji('lock')} UTR: {format_spoiler(utr)}
"""
    return summary

def format_account_details(phone, session_string):
    """Format account details for delivery"""
    details = f"""
{get_emoji('success')} **Account Delivered!**

{get_emoji('profile')} **Phone Number:**
{format_code(phone)}

{get_emoji('lock')} **Session String:**
{format_pre(session_string)}

{get_emoji('warning')} **Instructions:**
1. Use Telegram X or official app
2. Use fresh IP/Proxy for login
3. Save session string safely

{get_emoji('support')} Contact @ToxicStoreSupport if any issues.
"""
    return details

def format_terms():
    """Format terms and conditions with block quotes"""
    terms = format_block_quote("⚠️ TERMS AND CONDITIONS\n\nPlease read and accept our terms to use this bot:")
    
    terms += "\n\n" + format_block_quote(
        "📌 Account Policy\n"
        "• These accounts are for testing/educational purposes\n"
        "• We are NOT responsible for any ban/freeze after login\n"
        "• Use Telegram X or official apps for best stability"
    )
    
    terms += "\n\n" + format_block_quote(
        "📌 Refund Policy\n"
        "• NO REFUNDS under any circumstances except 'No OTP Received'\n"
        "• All sales are final. Buy at your own risk"
    )
    
    terms += "\n\n" + format_block_quote(
        "📌 Misuse\n"
        "• Any illegal activity will result in a ban"
    )
    
    terms += "\n\n✅ By clicking 'Accept', you agree to all the terms"
    
    return terms

def format_how_to_use():
    """Format how to use guide"""
    guide = f"""
{get_emoji('rocket')} **Quick User Guide**

{get_emoji('payment')} **1. Deposit Funds**
   • Use UPI (Auto) or Crypto
   • Send UTR number for verification

{get_emoji('cart')} **2. Buy Account**
   • Select country
   • Choose quantity
   • Complete payment

{get_emoji('unlock')} **3. Get Account**
   • Account delivered instantly
   • Check 'My Orders' for details

{get_emoji('shield')} **4. Safety Tips**
   • Always use fresh IPs/Proxy
   • Don't share session strings
   • Contact support for issues

{get_emoji('support')} Need help? Contact @ToxicStoreSupport
"""
    return guide

def format_referral_info(referral_link, bonus_amount=20, threshold=1000):
    """Format referral information"""
    info = f"""
{get_emoji('gift')} **Earn Money & Rewards**

Invite friends and earn bonus balance!

{get_emoji('info')} **How it works?**
1. Share your link with friends
2. When your friend deposits total ₹{threshold:,}
3. You instantly get ₹{bonus_amount} Bonus!

{get_emoji('link')} **Your Referral Link:**
{format_code(referral_link)}

{get_emoji('ticket')} Have a Coupon? Use /redeem CODE
"""
    return info
