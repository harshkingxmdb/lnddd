import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.inline import get_back_keyboard
from middleware.auth import require_auth
from middleware.ratelimit import rate_limit, rate_limit_callback
from database import log_activity
from utils.emojis import get_emoji
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Store support tickets
support_tickets = {}

@require_auth
@rate_limit_callback
async def support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle support button"""
    query = update.callback_query
    await query.answer()
    
    text = f"""
{get_emoji('support')} **Customer Support** {get_emoji('support')}

**Contact Options:**

📩 **Direct Support:** @shonaStoreSupport

📋 **Common Issues:**
• Payment not verified
• Account not working
• OTP not received
• Login issues
• Bulk orders

**How to get help:**
1. Click the support link above
2. Send your Order ID (if applicable)
3. Describe your issue clearly
4. Attach screenshots if needed

**Response Time:** Usually within 24 hours

**⚠️ Note:** Never share your password or sensitive info with anyone.
"""
    
    keyboard = get_back_keyboard("back_to_menu")
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@require_auth
@rate_limit
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support command"""
    await support_callback(update, context)

@require_auth
@rate_limit
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command for reporting issues"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ **Usage:** `/report <issue description>`\n\n"
            "Example: `/report Account not working - Order ID ORD12345`\n\n"
            "Your report will be sent to admin.",
            parse_mode='Markdown'
        )
        return
    
    issue = ' '.join(context.args)
    
    # Create ticket
    ticket_id = len(support_tickets) + 1
    support_tickets[ticket_id] = {
        'user_id': user_id,
        'username': username,
        'issue': issue,
        'status': 'open',
        'created_at': str(update.message.date)
    }
    
    # Log activity
    log_activity(user_id, "report_submitted", {"ticket_id": ticket_id, "issue": issue[:100]})
    
    # Notify user
    await update.message.reply_text(
        f"✅ **Report Submitted!**\n\n"
        f"Ticket ID: `TKT{ticket_id:06d}`\n\n"
        f"Support team will contact you soon.\n\n"
        f"Response time: Usually within 24 hours.\n\n"
        f"For urgent help, contact: @shonaStoreSupport",
        parse_mode='Markdown'
    )
    
    # Notify all admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🔔 **New Support Ticket**\n\n"
                     f"Ticket: `TKT{ticket_id:06d}`\n"
                     f"User: @{username} (`{user_id}`)\n"
                     f"Issue: {issue}\n\n"
                     f"Use `/resolve {ticket_id}` to close.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

@rate_limit
async def ticket_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ticket command to check ticket status"""
    user_id = update.effective_user.id
    
    # Find user's tickets
    user_tickets = [
        {'id': tid, **data} 
        for tid, data in support_tickets.items() 
        if data.get('user_id') == user_id
    ]
    
    if not user_tickets:
        await update.message.reply_text(
            "📋 **No Tickets Found**\n\n"
            "You haven't submitted any support tickets yet.\n\n"
            "Use `/report <issue>` to create a ticket.",
            parse_mode='Markdown'
        )
        return
    
    text = "📋 **Your Support Tickets**\n\n"
    for ticket in user_tickets[-5:]:  # Last 5 tickets
        status_emoji = "🟢" if ticket.get('status') == 'open' else "🔴"
        text += f"{status_emoji} `TKT{ticket['id']:06d}` - {ticket.get('status', 'unknown').upper()}\n"
    
    text += "\nUse `/ticket <id>` for details."
    
    await update.message.reply_text(text, parse_mode='Markdown')

@rate_limit
async def ticket_detail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ticket <id> command for ticket details"""
    user_id = update.effective_user.id
    
    if not context.args or len(context.args) == 0:
        await ticket_status_command(update, context)
        return
    
    try:
        ticket_num = int(context.args[0].replace('TKT', '').replace('tkt', ''))
    except:
        await update.message.reply_text("❌ Invalid ticket ID. Use number like: `/ticket 123`", parse_mode='Markdown')
        return
    
    if ticket_num not in support_tickets:
        await update.message.reply_text("❌ Ticket not found.")
        return
    
    ticket = support_tickets[ticket_num]
    
    if ticket.get('user_id') != user_id and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You don't have permission to view this ticket.")
        return
    
    text = f"""
📋 **Ticket Details**

ID: `TKT{ticket_num:06d}`
Status: {ticket.get('status', 'unknown').upper()}
Created: {ticket.get('created_at', 'Unknown')}

**Issue:**
{ticket.get('issue', 'No description')}

**Response:**
{ticket.get('response', 'Not yet responded')}
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

# Admin commands for support
@rate_limit
async def resolve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to resolve ticket"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ **Usage:** `/resolve <ticket_id> [response]`\n\n"
            "Example: `/resolve 123 Your issue has been fixed.`",
            parse_mode='Markdown'
        )
        return
    
    try:
        ticket_num = int(context.args[0].replace('TKT', '').replace('tkt', ''))
    except:
        await update.message.reply_text("❌ Invalid ticket ID.")
        return
    
    if ticket_num not in support_tickets:
        await update.message.reply_text("❌ Ticket not found.")
        return
    
    response = ' '.join(context.args[1:]) if len(context.args) > 1 else "Issue resolved."
    
    ticket = support_tickets[ticket_num]
    ticket['status'] = 'resolved'
    ticket['response'] = response
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=ticket['user_id'],
            text=f"✅ **Ticket #{ticket_num:06d} Resolved**\n\n"
                 f"Response: {response}\n\n"
                 f"Thank you for contacting support!",
            parse_mode='Markdown'
        )
    except:
        pass
    
    await update.message.reply_text(f"✅ Ticket #{ticket_num:06d} resolved and user notified.")

# Export handlers
def get_handlers():
    from telegram.ext import CallbackQueryHandler, CommandHandler
    
    return [
        CallbackQueryHandler(support_callback, pattern="^support$"),
        CommandHandler("support", support_command),
        CommandHandler("report", report_command),
        CommandHandler("ticket", ticket_detail_command),
        CommandHandler("resolve", resolve_command),
    ]
