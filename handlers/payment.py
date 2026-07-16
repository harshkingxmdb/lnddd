import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.inline import get_payment_methods_keyboard, get_back_keyboard
from middleware.auth import require_auth
from middleware.ratelimit import rate_limit, rate_limit_callback
from services.payments import create_payment_record, get_wallet_balance, add_wallet_balance
from database import get_user, update_user
from config import UPI_IDS, CRYPTO_USDT_ADDRESS
from utils.validators import validate_utr
from utils.formatters import format_amount, format_spoiler

logger = logging.getLogger(__name__)

# Store pending payment context
pending_payments = {}

@require_auth
@rate_limit_callback
async def add_funds_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add funds button"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    balance = get_wallet_balance(user_id)
    
    text = f"""
💰 **ADD FUNDS**

{format_amount(balance)} - Wallet Balance

Select Payment Method:
"""
    
    keyboard = get_payment_methods_keyboard()
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def payment_upi_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle UPI payment selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get first UPI ID
    upi_id = UPI_IDS[0] if UPI_IDS else "BHARATPE.8T0B1B2E2Z16787@fbpe"
    
    # QR code path
    qr_path = "assets/qr.jpg"
    
    text = f"""
💳 **UPI PAYMENT (Auto-Verify)**

**UPI ID:** `{upi_id}`

**STEPS TO PAY:**
1. Scan QR or Copy UPI ID
2. Pay any amount you want
3. Send the 12-Digit UTR / Ref No. here

Bot is listening for UTR...
"""
    
    # Try to send QR photo
    try:
        import os
        if os.path.exists(qr_path):
            with open(qr_path, 'rb') as qr_file:
                await query.message.reply_photo(
                    photo=qr_file,
                    caption=text,
                    parse_mode='Markdown'
                )
            await query.delete_message()
        else:
            await query.edit_message_text(
                text,
                reply_markup=get_back_keyboard("back_to_funds"),
                parse_mode='Markdown'
            )
    except:
        await query.edit_message_text(
            text,
            reply_markup=get_back_keyboard("back_to_funds"),
            parse_mode='Markdown'
        )
    
    # Set waiting for UTR
    context.user_data['waiting_for_utr'] = True
    context.user_data['payment_method'] = 'upi'

@rate_limit_callback
async def payment_crypto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Crypto payment selection"""
    query = update.callback_query
    await query.answer()
    
    crypto_address = CRYPTO_USDT_ADDRESS
    
    text = f"""
🪙 **CRYPTO DEPOSIT (USDT)**

**Binance Pay ID:** `1200101076`

**USDT TRC20 Address:**
`{crypto_address}`

⚠️ Min Deposit: $1
📌 After payment, upload screenshot below.

Send screenshot after payment to complete verification.
"""
    
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard("back_to_funds"),
        parse_mode='Markdown'
    )
    
    # Set waiting for crypto screenshot
    context.user_data['waiting_for_crypto'] = True
    context.user_data['payment_method'] = 'crypto'

@rate_limit
async def handle_utr_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle UTR number from user"""
    if not context.user_data.get('waiting_for_utr'):
        return
    
    user_id = update.effective_user.id
    utr_number = update.message.text.strip()
    
    # Validate UTR
    is_valid, message = validate_utr(utr_number)
    
    if not is_valid:
        await update.message.reply_text(f"❌ {message}\n\nPlease send a valid 12-digit UTR number.")
        return
    
    # Ask for amount
    context.user_data['pending_utr'] = utr_number
    context.user_data['waiting_for_utr'] = False
    context.user_data['waiting_for_amount'] = True
    
    await update.message.reply_text(
        f"✅ UTR Received: {format_spoiler(utr_number)}\n\n"
        f"Now please enter the amount you paid (in INR):",
        parse_mode='Markdown'
    )

@rate_limit
async def handle_amount_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount from user"""
    if not context.user_data.get('waiting_for_amount'):
        return
    
    user_id = update.effective_user.id
    amount_text = update.message.text.strip()
    
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ Please enter a valid amount (e.g., 100)")
        return
    
    utr_number = context.user_data.get('pending_utr')
    payment_method = context.user_data.get('payment_method', 'upi')
    
    # Process payment
    success, result = create_payment_record(user_id, amount, utr_number, payment_method)
    
    if success:
        # Get updated balance
        new_balance = get_wallet_balance(user_id)
        
        await update.message.reply_text(
            f"✅ **Payment Verified Successfully!**\n\n"
            f"Amount: {format_amount(amount)}\n"
            f"UTR: {format_spoiler(utr_number)}\n"
            f"New Balance: {format_amount(new_balance)}\n\n"
            f"Use /menu to continue shopping.",
            parse_mode='Markdown'
        )
        
        # Check for referral bonus
        from services.payments import check_referral_bonus
        check_referral_bonus(user_id, amount)
    else:
        await update.message.reply_text(
            f"❌ Payment verification failed: {result}\n\n"
            f"Please contact support @ToxicStoreSupport",
            parse_mode='Markdown'
        )
    
    # Clear context
    context.user_data.pop('waiting_for_amount', None)
    context.user_data.pop('pending_utr', None)
    context.user_data.pop('payment_method', None)

@rate_limit
async def handle_crypto_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto payment screenshot"""
    if not context.user_data.get('waiting_for_crypto'):
        return
    
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a screenshot of your payment.")
        return
    
    # Get the largest photo
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    # Ask for amount
    context.user_data['pending_crypto_screenshot'] = file_id
    context.user_data['waiting_for_crypto'] = False
    context.user_data['waiting_for_crypto_amount'] = True
    
    await update.message.reply_text(
        "✅ Screenshot received!\n\n"
        "Now please enter the amount you paid (in USD):"
    )

@rate_limit
async def handle_crypto_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto amount"""
    if not context.user_data.get('waiting_for_crypto_amount'):
        return
    
    user_id = update.effective_user.id
    amount_text = update.message.text.strip()
    
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ Please enter a valid amount (e.g., 10)")
        return
    
    screenshot_file_id = context.user_data.get('pending_crypto_screenshot')
    payment_method = context.user_data.get('payment_method', 'crypto')
    
    # For crypto, we need manual verification
    # Create pending payment record
    from services.payments import create_crypto_payment_record
    success, result = create_crypto_payment_record(user_id, amount, screenshot_file_id)
    
    if success:
        await update.message.reply_text(
            f"✅ **Crypto Payment Recorded!**\n\n"
            f"Amount: ${amount}\n"
            f"Status: Pending Verification\n\n"
            f"Your payment will be verified by admin within 24 hours.\n\n"
            f"You will receive a confirmation once verified.",
            parse_mode='Markdown'
        )
        
        # Notify admin
        from config import ADMIN_IDS
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **New Crypto Payment Pending**\n\n"
                         f"User: {user_id}\n"
                         f"Amount: ${amount}\n"
                         f"Payment ID: {result.get('id') if result else 'N/A'}\n\n"
                         f"Use /verify to confirm.",
                    parse_mode='Markdown'
                )
            except:
                pass
    else:
        await update.message.reply_text(
            f"❌ Failed to record payment: {result}\n\n"
            f"Please contact support @shonaStoreSupport"
        )
    
    # Clear context
    context.user_data.pop('waiting_for_crypto_amount', None)
    context.user_data.pop('pending_crypto_screenshot', None)
    context.user_data.pop('payment_method', None)

@rate_limit_callback
async def back_to_funds_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to funds button"""
    query = update.callback_query
    await query.answer()
    
    # Clear waiting states
    context.user_data.pop('waiting_for_utr', None)
    context.user_data.pop('waiting_for_amount', None)
    context.user_data.pop('waiting_for_crypto', None)
    context.user_data.pop('waiting_for_crypto_amount', None)
    
    await add_funds_callback(update, context)

# Export handlers
def get_handlers():
    from telegram.ext import CallbackQueryHandler, MessageHandler, filters
    
    return [
        CallbackQueryHandler(add_funds_callback, pattern="^add_funds$"),
        CallbackQueryHandler(payment_upi_callback, pattern="^payment_upi$"),
        CallbackQueryHandler(payment_crypto_callback, pattern="^payment_crypto$"),
        CallbackQueryHandler(back_to_funds_callback, pattern="^back_to_funds$"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_utr_message),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_message),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_crypto_amount),
        MessageHandler(filters.PHOTO, handle_crypto_screenshot),
    ]
