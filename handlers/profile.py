import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.inline import get_profile_keyboard, get_orders_keyboard, get_payments_keyboard, get_back_keyboard
from middleware.auth import require_auth
from middleware.ratelimit import rate_limit, rate_limit_callback
from database import get_user, get_user_orders
from services.payments import get_wallet_balance, get_user_payments
from services.orders import get_user_active_orders
from utils.formatters import format_amount, format_order_summary, format_payment_summary, format_spoiler
from utils.helpers import format_time_ago

logger = logging.getLogger(__name__)

@require_auth
@rate_limit_callback
async def my_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle my profile button"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await query.edit_message_text("❌ User not found. Please /start again.")
        return
    
    balance = user.get('wallet_balance', 0)
    total_deposit = user.get('total_deposit', 0)
    terms_accepted = user.get('terms_accepted', False)
    created_at = user.get('created_at', '')
    
    profile_text = f"""
👤 **ACCOUNT DASHBOARD**

**User ID:** `{user_id}`
**Name:** {user.get('full_name', 'N/A')}

💰 **WALLET DETAILS**
• Balance: {format_amount(balance)}
• Total Deposit: {format_amount(total_deposit)}

📋 **ACCOUNT STATUS**
• Terms: {'✓ Accepted' if terms_accepted else '✗ Pending'}

📅 Joined: {format_time_ago(created_at)}
"""
    
    keyboard = get_profile_keyboard()
    
    await query.edit_message_text(
        profile_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def my_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle my orders button"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    orders = get_user_orders(user_id, limit=20)
    
    if not orders:
        await query.edit_message_text(
            "📦 **No Orders Found**\n\nYou haven't made any purchases yet.\n\nUse /menu to buy accounts!",
            reply_markup=get_back_keyboard("my_profile"),
            parse_mode='Markdown'
        )
        return
    
    # Show last 10 orders
    recent_orders = orders[:10]
    
    orders_text = "📦 **Your Orders**\n\n"
    for order in recent_orders:
        order_id = order.get('order_id', 'N/A')[:8]
        amount = order.get('amount', 0)
        status = order.get('status', 'pending')
        status_emoji = "✅" if status == "completed" else "⏳"
        date = format_time_ago(order.get('created_at', ''))
        
        orders_text += f"{status_emoji} `{order_id}` - {format_amount(amount)} ({date})\n"
    
    keyboard = get_orders_keyboard(recent_orders)
    
    await query.edit_message_text(
        orders_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def order_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle order detail view"""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace("order_detail_", "")
    
    from services.orders import get_order_details
    order = get_order_details(order_id)
    
    if not order:
        await query.edit_message_text("❌ Order not found.")
        return
    
    order_summary = format_order_summary(order)
    
    # Add product details if available
    if order.get('phone_number'):
        phone = order.get('phone_number')
        hidden_phone = phone[:3] + "****" + phone[-3:] if len(phone) > 6 else phone
        order_summary += f"\n📱 **Phone:** `{hidden_phone}`"
    
    if order.get('session_string'):
        session = order.get('session_string', '')[:50] + "..."
        order_summary += f"\n🔑 **Session:** `{session}`"
    
    order_summary += "\n\n" + format_spoiler("Contact support if you need OTP")
    
    keyboard = get_back_keyboard("my_orders")
    
    await query.edit_message_text(
        order_summary,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def my_payments_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle my payments button"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    payments = get_user_payments(user_id, limit=20)
    
    if not payments:
        await query.edit_message_text(
            "💸 **No Payment History Found!**\n\nYou haven't made any deposits yet.\n\nUse /menu to add funds!",
            reply_markup=get_back_keyboard("my_profile"),
            parse_mode='Markdown'
        )
        return
    
    payments_text = "💸 **Your Payment History**\n\n"
    for payment in payments[:10]:
        txn_id = payment.get('txn_id', 'N/A')[:8]
        amount = payment.get('amount', 0)
        status = payment.get('status', 'pending')
        status_emoji = "✅" if status == "verified" else "⏳"
        date = format_time_ago(payment.get('created_at', ''))
        
        payments_text += f"{status_emoji} `{txn_id}` - {format_amount(amount)} ({date})\n"
    
    keyboard = get_payments_keyboard(payments[:10])
    
    await query.edit_message_text(
        payments_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def payment_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment detail view"""
    query = update.callback_query
    await query.answer()
    
    payment_id = int(query.data.replace("payment_detail_", ""))
    
    from database import supabase
    result = supabase.table("payments").select("*").eq("id", payment_id).execute()
    payment = result.data[0] if result.data else None
    
    if not payment:
        await query.edit_message_text("❌ Payment not found.")
        return
    
    payment_summary = format_payment_summary(payment)
    
    keyboard = get_back_keyboard("my_payments")
    
    await query.edit_message_text(
        payment_summary,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def get_otp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle get OTP button"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user's active orders with accounts
    active_orders = get_user_active_orders(user_id)
    
    if not active_orders:
        await query.edit_message_text(
            "🔑 **No Active Orders**\n\n"
            "You don't have any active accounts that need OTP.\n\n"
            "Buy an account first to get OTP.",
            reply_markup=get_back_keyboard("my_profile"),
            parse_mode='Markdown'
        )
        return
    
    # Show list of orders to get OTP for
    text = "🔑 **Select Account to Get OTP**\n\n"
    keyboard = []
    
    for order in active_orders[:10]:
        order_id = order.get('order_id', 'N/A')[:8]
        phone = order.get('phone_number', 'N/A')
        hidden_phone = phone[:3] + "****" + phone[-3:] if len(phone) > 6 else phone
        
        text += f"• Order `{order_id}` - {hidden_phone}\n"
        keyboard.append([
            InlineKeyboardButton(
                text=f"📱 {hidden_phone}",
                callback_data=f"request_otp_{order.get('order_id')}",
                color="primary"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="↩️ Back to Profile", callback_data="my_profile", color="secondary")
    ])
    

    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

@rate_limit_callback
async def request_otp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle request OTP for specific order"""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace("request_otp_", "")
    
    from services.orders import get_order_details
    order = get_order_details(order_id)
    
    if not order or not order.get('phone_number'):
        await query.edit_message_text("❌ Order not found or no phone number available.")
        return
    
    phone_number = order.get('phone_number')
    
    # Simulate OTP request (in production, integrate with actual service)
    await query.edit_message_text(
        f"📱 **OTP Requested**\n\n"
        f"Phone: `{phone_number}`\n\n"
        f"Please check your Telegram for OTP from Telegram.\n\n"
        f"When you receive the OTP, enter it here:\n\n"
        f"Type: `/otp {order_id} <code>`\n\n"
        f"Example: `/otp {order_id[:8]} 12345`",
        reply_markup=get_back_keyboard("get_otp"),
        parse_mode='Markdown'
    )
    
    # Store OTP waiting state
    context.user_data['waiting_for_otp'] = True
    context.user_data['otp_order_id'] = order_id

@rate_limit
async def handle_otp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OTP submission via command"""
    if not context.user_data.get('waiting_for_otp'):
        await update.message.reply_text(
            "❌ No OTP request active. Use 'Get OTP' from profile first."
        )
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/otp <order_id> <code>`\n\n"
            "Example: `/otp ORD12345 123456`",
            parse_mode='Markdown'
        )
        return
    
    order_id_input = args[0]
    otp_code = args[1]
    
    stored_order_id = context.user_data.get('otp_order_id', '')
    
    if not stored_order_id.startswith(order_id_input):
        await update.message.reply_text("❌ Invalid order ID.")
        return
    
    await update.message.reply_text(
        f"✅ **OTP Received!**\n\n"
        f"OTP Code: `{otp_code}`\n\n"
        f"Use this OTP to complete login.\n\n"
        f"Need help? Contact @shonaStoreSupport",
        parse_mode='Markdown'
    )
    
    # Clear OTP waiting state
    context.user_data.pop('waiting_for_otp', None)
    context.user_data.pop('otp_order_id', None)

# Export handlers
def get_handlers():
    from telegram.ext import CallbackQueryHandler, CommandHandler
    
    return [
        CallbackQueryHandler(my_profile_callback, pattern="^my_profile$"),
        CallbackQueryHandler(my_orders_callback, pattern="^my_orders$"),
        CallbackQueryHandler(order_detail_callback, pattern="^order_detail_"),
        CallbackQueryHandler(my_payments_callback, pattern="^my_payments$"),
        CallbackQueryHandler(payment_detail_callback, pattern="^payment_detail_"),
        CallbackQueryHandler(get_otp_callback, pattern="^get_otp$"),
        CallbackQueryHandler(request_otp_callback, pattern="^request_otp_"),
        CommandHandler("otp", handle_otp_command),
    ]
