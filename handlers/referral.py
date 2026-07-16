import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.inline import get_back_keyboard
from middleware.auth import require_auth
from middleware.ratelimit import rate_limit, rate_limit_callback
from services.referral import (
    get_user_referral_code,
    get_referral_link,
    get_referral_stats,
    get_referral_earnings
)
from utils.helpers import get_bot_username
from utils.formatters import format_code, format_amount
from utils.emojis import get_emoji

logger = logging.getLogger(__name__)

@require_auth
@rate_limit_callback
async def earn_money_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle earn money button"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    bot_username = get_bot_username(context)
    
    # Get referral code and link
    referral_code = get_user_referral_code(user_id)
    referral_link = get_referral_link(user_id, bot_username)
    
    # Get referral stats
    stats = get_referral_stats(user_id)
    total_bonus = get_referral_earnings(user_id)
    
    text = f"""
{get_emoji('gift')} **EARN MONEY & REWARDS** {get_emoji('gift')}

Invite friends and earn bonus balance!

{get_emoji('info')} **How it works?**
1. Share your link with friends
2. When your friend deposits total ₹{stats.get('threshold', 1000):,}
3. You instantly get ₹{stats.get('bonus_amount', 20)} Bonus!

{get_emoji('link')} **Your Referral Link:**
{format_code(referral_link)}

📊 **Your Stats:**
• Total Referrals: {stats.get('total_referrals', 0)}
• Total Bonus Earned: {format_amount(total_bonus)}
• Pending Bonus: {format_amount(stats.get('pending_bonus', 0))}

{get_emoji('ticket')} Have a Coupon? Use /redeem CODE
"""
    
    keyboard = get_back_keyboard("back_to_menu")
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@require_auth
@rate_limit
async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /redeem command for coupon codes"""
    user_id = update.effective_user.id
    
    # Check if coupon code provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ **Usage:** `/redeem CODE`\n\n"
            "Example: `/redeem WELCOME50`\n\n"
            "Contact support for coupon codes.",
            parse_mode='Markdown'
        )
        return
    
    coupon_code = context.args[0].upper()
    
    # Coupon validation (in production, store coupons in database)
    # For now, hardcoded coupons
    coupons = {
        "WELCOME10": {"amount": 10, "description": "Welcome Bonus"},
        "FIRST50": {"amount": 50, "description": "First Purchase Bonus"},
        "VIP100": {"amount": 100, "description": "VIP Special"},
    }
    
    if coupon_code in coupons:
        coupon = coupons[coupon_code]
        amount = coupon.get('amount', 0)
        
        # Check if user already used this coupon
        used_coupons = context.user_data.get('used_coupons', [])
        if coupon_code in used_coupons:
            await update.message.reply_text(
                f"❌ Coupon `{coupon_code}` has already been used!",
                parse_mode='Markdown'
            )
            return
        
        # Add to wallet
        from services.payments import add_wallet_balance
        success, result = add_wallet_balance(user_id, amount)
        
        if success:
            # Mark as used
            used_coupons.append(coupon_code)
            context.user_data['used_coupons'] = used_coupons
            
            await update.message.reply_text(
                f"✅ **Coupon Redeemed Successfully!**\n\n"
                f"Code: `{coupon_code}`\n"
                f"Description: {coupon.get('description')}\n"
                f"Amount: {format_amount(amount)}\n\n"
                f"Amount added to your wallet!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Failed to add bonus. Please try again.",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            f"❌ Invalid coupon code: `{coupon_code}`\n\n"
            f"Please check and try again.",
            parse_mode='Markdown'
        )

@require_auth
@rate_limit
async def referral_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /referral command to show referral stats"""
    user_id = update.effective_user.id
    
    stats = get_referral_stats(user_id)
    total_bonus = get_referral_earnings(user_id)
    
    text = f"""
📊 **Referral Statistics**

{get_emoji('users')} Total Referrals: {stats.get('total_referrals', 0)}
{get_emoji('coin')} Total Bonus Earned: {format_amount(total_bonus)}
{get_emoji('pending')} Pending Bonus: {format_amount(stats.get('pending_bonus', 0))}

{get_emoji('info')} **Referral Bonus:**
• Friend deposits ₹{stats.get('threshold', 1000):,}
• You get ₹{stats.get('bonus_amount', 20)} bonus

Use /menu to get your referral link!
"""
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown'
    )

# Export handlers
def get_handlers():
    from telegram.ext import CallbackQueryHandler, CommandHandler
    
    return [
        CallbackQueryHandler(earn_money_callback, pattern="^earn_money$"),
        CommandHandler("redeem", redeem_command),
        CommandHandler("referral", referral_stats_command),
    ]
