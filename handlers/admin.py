import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards.inline import get_admin_panel_keyboard, get_back_keyboard
from middleware.auth import require_admin
from middleware.ratelimit import rate_limit, rate_limit_callback
from database import (
    get_all_users, 
    get_user, 
    update_user,
    get_all_countries,
    add_product,
    get_available_stock,
    get_user_orders,
    supabase
)
from services.stock import get_stock_count, add_new_stock
from services.payments import add_wallet_balance
from utils.formatters import format_amount
from utils.validators import validate_phone, is_valid_session_string

logger = logging.getLogger(__name__)

@require_admin
@rate_limit_callback
async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel button"""
    query = update.callback_query
    await query.answer()
    
    text = """
🔧 **Admin Panel**

Welcome to Admin Dashboard!

Select an option from below:
"""
    
    keyboard = get_admin_panel_keyboard()
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@require_admin
@rate_limit
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    await admin_panel_callback(update, context)

@require_admin
@rate_limit_callback
async def admin_add_country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add country button"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "➕ **Add New Country**\n\n"
        "Send country details in this format:\n\n"
        "`/addcountry Name Flag`\n\n"
        "Example: `/addcountry Canada 🇨🇦`\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode='Markdown'
    )
    
    context.user_data['admin_action'] = 'add_country'

@require_admin
@rate_limit
async def addcountry_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addcountry command"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ **Usage:** `/addcountry Name Flag`\n\n"
            "Example: `/addcountry Canada 🇨🇦`",
            parse_mode='Markdown'
        )
        return
    
    name = context.args[0]
    flag = context.args[1]
    
    # Check if country exists
    existing = supabase.table("countries").select("*").eq("name", name).execute()
    if existing.data:
        await update.message.reply_text(f"❌ Country '{name}' already exists!")
        return
    
    # Add country
    result = supabase.table("countries").insert({
        "name": name,
        "flag": flag,
        "is_active": True
    }).execute()
    
    if result.data:
        await update.message.reply_text(f"✅ Country '{name}' {flag} added successfully!")
    else:
        await update.message.reply_text("❌ Failed to add country.")

@require_admin
@rate_limit_callback
async def admin_add_stock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add stock button"""
    query = update.callback_query
    await query.answer()
    
    # Get countries list
    countries = get_all_countries()
    
    if not countries:
        await query.edit_message_text("❌ No countries available. Add countries first.")
        return
    
    text = "📦 **Add Stock**\n\nSelect a country to add stock:\n\n"
    
    keyboard = []
    for country in countries:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{country.get('flag')} {country.get('name')}",
                callback_data=f"admin_stock_country_{country.get('id')}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="↩️ Back", callback_data="admin_panel")
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

@rate_limit_callback
async def admin_stock_country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stock country selection"""
    query = update.callback_query
    await query.answer()
    
    country_id = int(query.data.replace("admin_stock_country_", ""))
    context.user_data['admin_stock_country_id'] = country_id
    
    await query.edit_message_text(
        "📦 **Add Stock**\n\n"
        "Send account details in this format:\n\n"
        "`/addstock phone_number session_string price`\n\n"
        "Example: `/addstock +1234567890 session_data_here 50`\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_back_keyboard("admin_add_stock"),
        parse_mode='Markdown'
    )
    
    context.user_data['admin_action'] = 'add_stock'

@require_admin
@rate_limit
async def addstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addstock command"""
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ **Usage:** `/addstock phone_number session_string price`\n\n"
            "Example: `/addstock +1234567890 session_data_here 50`",
            parse_mode='Markdown'
        )
        return
    
    phone = context.args[0]
    session = context.args[1]
    
    try:
        price = float(context.args[2])
    except:
        await update.message.reply_text("❌ Invalid price. Please enter a number.")
        return
    
    country_id = context.user_data.get('admin_stock_country_id')
    if not country_id:
        await update.message.reply_text("❌ Please select a country first using admin panel.")
        return
    
    success, result = add_new_stock(country_id, phone, session, price, update.effective_user.id)
    
    if success:
        await update.message.reply_text(
            f"✅ **Stock Added!**\n\n"
            f"Phone: `{phone}`\n"
            f"Price: {format_amount(price)}\n\n"
            f"Account added successfully.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ Failed to add stock: {result}")

@require_admin
@rate_limit_callback
async def admin_view_stock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle view stock button"""
    query = update.callback_query
    await query.answer()
    
    stock_data = get_available_stock()
    
    if not stock_data:
        await query.edit_message_text(
            "📦 **Stock Status**\n\nNo stock available.",
            reply_markup=get_back_keyboard("admin_panel"),
            parse_mode='Markdown'
        )
        return
    
    text = "📦 **Stock Status**\n\n"
    for item in stock_data:
        text += f"{item.get('flag', '')} **{item.get('country_name')}**: {item.get('available_count', 0)} accounts\n"
    
    keyboard = get_back_keyboard("admin_panel")
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@require_admin
@rate_limit_callback
async def admin_view_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle view orders button"""
    query = update.callback_query
    await query.answer()
    
    # Get recent orders
    result = supabase.table("orders").select("*").order("created_at", desc=True).limit(20).execute()
    orders = result.data if result.data else []
    
    if not orders:
        await query.edit_message_text(
            "📋 **Recent Orders**\n\nNo orders found.",
            reply_markup=get_back_keyboard("admin_panel"),
            parse_mode='Markdown'
        )
        return
    
    text = "📋 **Recent Orders**\n\n"
    for order in orders[:10]:
        order_id = order.get('order_id', 'N/A')[:8]
        amount = order.get('amount', 0)
        status = order.get('status', 'pending')
        user_id = order.get('user_id', 'N/A')
        
        status_emoji = "✅" if status == "completed" else "⏳"
        text += f"{status_emoji} `{order_id}` - ₹{amount} - User: `{user_id}`\n"
    
    keyboard = get_back_keyboard("admin_panel")
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@require_admin
@rate_limit_callback
async def admin_verify_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verify payment button"""
    query = update.callback_query
    await query.answer()
    
    # Get pending payments
    result = supabase.table("payments").select("*").eq("status", "pending").execute()
    payments = result.data if result.data else []
    
    if not payments:
        await query.edit_message_text(
            "✅ **Pending Payments**\n\nNo pending payments to verify.",
            reply_markup=get_back_keyboard("admin_panel"),
            parse_mode='Markdown'
        )
        return
    
    text = "💰 **Pending Payments**\n\n"
    keyboard = []
    
    for payment in payments[:10]:
        payment_id = payment.get('id')
        user_id = payment.get('user_id')
        amount = payment.get('amount', 0)
        utr = payment.get('utr_number', 'N/A')
        
        text += f"ID: `{payment_id}` | User: `{user_id}` | ₹{amount} | UTR: `{utr}`\n"
        keyboard.append([
            InlineKeyboardButton(
                text=f"✅ Verify Payment #{payment_id}",
                callback_data=f"admin_verify_pay_{payment_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="↩️ Back", callback_data="admin_panel")
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

@rate_limit_callback
async def admin_verify_pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle individual payment verification"""
    query = update.callback_query
    await query.answer()
    
    payment_id = int(query.data.replace("admin_verify_pay_", ""))
    
    # Get payment
    result = supabase.table("payments").select("*").eq("id", payment_id).execute()
    payment = result.data[0] if result.data else None
    
    if not payment:
        await query.edit_message_text("❌ Payment not found.")
        return
    
    user_id = payment.get('user_id')
    amount = payment.get('amount', 0)
    
    # Verify payment
    from services.payments import verify_payment, add_wallet_balance
    
    verified = verify_payment(payment_id, update.effective_user.id)
    
    if verified:
        # Add to wallet
        add_wallet_balance(user_id, amount)
        
        # Update total deposit
        user = get_user(user_id)
        total_deposit = user.get('total_deposit', 0) + amount
        update_user(user_id, {"total_deposit": total_deposit})
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ **Payment Verified!**\n\n"
                     f"Amount: {format_amount(amount)}\n"
                     f"Added to your wallet.\n\n"
                     f"New Balance: {format_amount(user.get('wallet_balance', 0) + amount)}\n\n"
                     f"Use /menu to start shopping!",
                parse_mode='Markdown'
            )
        except:
            pass
        
        await query.edit_message_text(
            f"✅ Payment #{payment_id} verified! ₹{amount} added to user's wallet.",
            reply_markup=get_back_keyboard("admin_verify_payment"),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(f"❌ Failed to verify payment #{payment_id}.")

@require_admin
@rate_limit_callback
async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stats button"""
    query = update.callback_query
    await query.answer()
    
    # Get stats
    users_result = supabase.table("users").select("count", count="exact").execute()
    total_users = users_result.count or 0
    
    orders_result = supabase.table("orders").select("count", count="exact").execute()
    total_orders = orders_result.count or 0
    
    payments_result = supabase.table("payments").select("count", count="exact").execute()
    total_payments = payments_result.count or 0
    
    # Get total revenue
    payments_sum = supabase.table("payments").select("amount").eq("status", "verified").execute()
    total_revenue = sum(p.get('amount', 0) for p in (payments_sum.data or []))
    
    # Get stock count
    stock_result = supabase.table("products").select("count", count="exact").eq("status", "available").execute()
    total_stock = stock_result.count or 0
    
    text = f"""
📊 **Bot Statistics**

👥 **Users:** {total_users}
📦 **Orders:** {total_orders}
💰 **Payments:** {total_payments}
💵 **Total Revenue:** {format_amount(total_revenue)}
📦 **Available Stock:** {total_stock}

**Recent Activity:**
Last 7 days: Coming soon...
"""
    
    keyboard = get_back_keyboard("admin_panel")
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@require_admin
@rate_limit_callback
async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast button"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📢 **Broadcast Message**\n\n"
        "Send the message you want to broadcast to all users.\n\n"
        "Type your message below.\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode='Markdown'
    )
    
    context.user_data['admin_action'] = 'broadcast'

@require_admin
@rate_limit
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message"""
    if update.message.text == "/cancel":
        context.user_data.pop('admin_action', None)
        await update.message.reply_text("❌ Broadcast cancelled.")
        return
    
    message = update.message.text
    users = get_all_users()
    
    if not users:
        await update.message.reply_text("❌ No users found.")
        return
    
    sent = 0
    failed = 0
    
    status_msg = await update.message.reply_text(f"📢 Sending broadcast to {len(users)} users...")
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.get('user_id'),
                text=f"📢 **BROADCAST**\n\n{message}",
                parse_mode='Markdown'
            )
            sent += 1
            await asyncio.sleep(0.05)  # Avoid flood limits
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"Total: {len(users)}\n"
        f"Sent: {sent}\n"
        f"Failed: {failed}",
        parse_mode='Markdown'
    )
    
    context.user_data.pop('admin_action', None)

@require_admin
@rate_limit_callback
async def admin_ban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ban button"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🚫 **Ban User**\n\n"
        "Send the User ID you want to ban/unban.\n\n"
        "Example: `/ban 123456789`\n\n"
        "Send /cancel to cancel.",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode='Markdown'
    )
    
    context.user_data['admin_action'] = 'ban'

@require_admin
@rate_limit
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command"""
    if not context.args:
        await update.message.reply_text("❌ Please provide a User ID.")
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Invalid User ID.")
        return
    
    user = get_user(target_id)
    if not user:
        await update.message.reply_text("❌ User not found.")
        return
    
    is_banned = not user.get('is_banned', False)
    update_user(target_id, {"is_banned": is_banned})
    
    status = "banned" if is_banned else "unbanned"
    await update.message.reply_text(f"✅ User `{target_id}` has been {status} successfully.")

def get_handlers():
    from telegram.ext import CallbackQueryHandler, CommandHandler
    
    return [
        CommandHandler("admin", admin_command),
        CommandHandler("stats", admin_stats_callback),
        CommandHandler("broadcast", admin_broadcast_callback),
        CommandHandler("add_stock", admin_add_stock_callback),
        CommandHandler("pending_payments", admin_verify_payment_callback),
        CommandHandler("addcountry", addcountry_command),
        CommandHandler("addstock", addstock_command),
        CommandHandler("ban", ban_command),
        CallbackQueryHandler(admin_panel_callback, pattern="^admin_panel$"),
        CallbackQueryHandler(admin_add_country_callback, pattern="^admin_add_country$"),
        CallbackQueryHandler(admin_add_stock_callback, pattern="^admin_add_stock$"),
        CallbackQueryHandler(admin_stock_country_callback, pattern="^admin_stock_country_\\d+$"),
        CallbackQueryHandler(admin_view_stock_callback, pattern="^admin_view_stock$"),
        CallbackQueryHandler(admin_view_orders_callback, pattern="^admin_view_orders$"),
        CallbackQueryHandler(admin_verify_payment_callback, pattern="^admin_verify_payment$"),
        CallbackQueryHandler(admin_verify_pay_callback, pattern="^admin_verify_pay_\\d+$"),
        CallbackQueryHandler(admin_stats_callback, pattern="^admin_stats$"),
        CallbackQueryHandler(admin_broadcast_callback, pattern="^admin_broadcast$"),
        CallbackQueryHandler(admin_ban_callback, pattern="^admin_ban$"),
    ]
