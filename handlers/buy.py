import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards.inline import get_countries_keyboard, get_quantity_keyboard, get_confirm_purchase_keyboard, get_product_action_keyboard
from middleware.auth import require_auth
from middleware.ratelimit import rate_limit, rate_limit_callback
from database import get_all_countries, get_available_stock, get_stock_by_country
from services.stock import check_stock_available, get_stock_count
from services.orders import create_new_order, complete_order_with_product
from services.payments import deduct_wallet_balance, get_wallet_balance
from services.stock import get_product_for_purchase, purchase_product
from utils.helpers import generate_order_id
from utils.formatters import format_amount, format_account_details
from utils.validators import validate_quantity
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Store user purchase context
user_purchase_context = {}

@require_auth
@rate_limit_callback
async def buy_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy accounts button"""
    query = update.callback_query
    await query.answer()
    
    # Get all countries
    countries = get_all_countries()
    
    if not countries:
        await query.edit_message_text(
            "❌ No countries available at the moment. Please check back later.",
            reply_markup=None
        )
        return
    
    # Get stock summary
    stock_data = get_available_stock()
    stock_dict = {item.get('country_id'): item.get('available_count', 0) for item in stock_data}
    
    # Add stock count to countries
    for country in countries:
        country_id = country.get('id')
        country['stock'] = stock_dict.get(country_id, 0)
    
    # Store in context
    context.user_data['countries'] = countries
    context.user_data['countries_page'] = 0
    
    keyboard = get_countries_keyboard(countries, page=0)
    
    await query.edit_message_text(
        "🌍 **SELECT COUNTRY**\n\nChoose a country to see available products:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def country_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country selection"""
    query = update.callback_query
    await query.answer()
    
    # Extract country ID from callback data
    callback_data = query.data
    country_id = int(callback_data.replace("country_", ""))
    
    # Get country details
    from database import get_country_by_id
    country = get_country_by_id(country_id)
    
    if not country:
        await query.edit_message_text("❌ Country not found. Please try again.")
        return
    
    # Check stock availability
    stock_count = get_stock_count(country_id)
    
    if stock_count == 0:
        # Show "Coming Soon" message
        await query.edit_message_text(
            f"🚧 **{country.get('flag', '')} {country.get('name')}**\n\n"
            f"📦 **Coming Soon!**\n\n"
            f"We are currently adding stock for this country. "
            f"Please check back later.\n\n"
            f"Subscribe to our channels for updates!",
            reply_markup=None,
            parse_mode='Markdown'
        )
        return
    
    # Store selected country in context
    context.user_data['selected_country'] = country
    
    # Get products for this country
    products = get_stock_by_country(country_id)
    
    if not products:
        await query.edit_message_text(
            f"❌ No products available for {country.get('flag', '')} {country.get('name')} at the moment.",
            reply_markup=None
        )
        return
    
    # Store products in context
    context.user_data['country_products'] = products
    
    # Show first product
    await show_product_details(update, context, query, products[0], 0, len(products))

async def show_product_details(update, context, query, product, index, total):
    """Show product details to user"""
    product_id = product.get('id')
    phone_number = product.get('phone_number', 'N/A')
    price = product.get('price', 0)
    
    # Hide part of phone number
    hidden_phone = phone_number[:3] + "****" + phone_number[-3:] if len(phone_number) > 6 else phone_number
    
    product_text = f"""
📱 **Product Details**

Country: {context.user_data.get('selected_country', {}).get('flag', '')}
Phone: `{hidden_phone}`
Price: {format_amount(price)}

Product {index + 1} of {total}
"""
    

    keyboard = [
        [
            InlineKeyboardButton(text="🛒 Buy Now", callback_data=f"buy_product_{product_id}"),
            InlineKeyboardButton(text="⏩ Next", callback_data=f"next_product_{index}")
        ],
        [
            InlineKeyboardButton(text="↩️ Back to Countries", callback_data="back_to_countries")
        ]
    ]
    

    keyboard_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        product_text,
        reply_markup=keyboard_markup,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def buy_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy product button"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    product_id = int(callback_data.replace("buy_product_", ""))
    
    # Get product
    from services.stock import get_product_by_id
    product = get_product_by_id(product_id)
    
    if not product or product.get('status') != 'available':
        await query.edit_message_text(
            "❌ This product is no longer available. Please choose another one.",
            reply_markup=None
        )
        return
    
    # Store product for purchase
    context.user_data['purchase_product'] = product
    
    # Get quantity keyboard
    price = product.get('price', 0)
    keyboard = get_quantity_keyboard(product_id, price, max_qty=5)
    
    await query.edit_message_text(
        f"📦 **Product Selected**\n\n"
        f"Price per account: {format_amount(price)}\n\n"
        f"Select quantity:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def quantity_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quantity selection"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    parts = callback_data.split("_")
    
    if parts[0] == "qty":
        product_id = int(parts[1])
        quantity = int(parts[2])
    else:
        # Custom quantity
        await query.edit_message_text(
            "Please enter the quantity you want to purchase:",
            reply_markup=None
        )
        context.user_data['awaiting_custom_qty'] = True
        return
    
    # Validate quantity
    product = context.user_data.get('purchase_product')
    if not product:
        await query.edit_message_text("❌ Session expired. Please start over.")
        return
    
    price = product.get('price', 0)
    total = price * quantity
    
    # Check stock availability
    from services.stock import get_stock_by_country
    country_id = product.get('country_id')
    stock_count = get_stock_count(country_id)
    
    if stock_count < quantity:
        await query.edit_message_text(
            f"❌ Only {stock_count} accounts available. Please reduce quantity.",
            reply_markup=None
        )
        return
    
    # Store purchase details
    context.user_data['purchase_quantity'] = quantity
    context.user_data['purchase_total'] = total
    
    keyboard = get_confirm_purchase_keyboard(product_id, quantity, total)
    
    await query.edit_message_text(
        f"🛒 **Order Summary**\n\n"
        f"Product: {product.get('phone_number', 'N/A')}\n"
        f"Quantity: {quantity}\n"
        f"Total: {format_amount(total)}\n\n"
        f"Please confirm your purchase:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def confirm_purchase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle purchase confirmation"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    parts = callback_data.replace("confirm_purchase_", "").split("_")
    product_id = int(parts[0])
    quantity = int(parts[1])
    
    user_id = update.effective_user.id
    product = context.user_data.get('purchase_product')
    total = context.user_data.get('purchase_total')
    
    if not product:
        await query.edit_message_text("❌ Session expired. Please start over.")
        return
    
    # Check wallet balance
    balance = get_wallet_balance(user_id)
    
    if balance < total:
        await query.edit_message_text(
            f"❌ **Insufficient Balance!**\n\n"
            f"Required: {format_amount(total)}\n"
            f"Your Balance: {format_amount(balance)}\n\n"
            f"Please add funds first.",
            reply_markup=None,
            parse_mode='Markdown'
        )
        return
    
    # Deduct balance
    success, result = deduct_wallet_balance(user_id, total)
    
    if not success:
        await query.edit_message_text(f"❌ {result}")
        return
    
    # Create order
    order_success, order = create_new_order(user_id, total, "wallet")
    
    if not order_success:
        # Refund balance if order fails
        from services.payments import add_wallet_balance
        add_wallet_balance(user_id, total)
        await query.edit_message_text("❌ Failed to create order. Please try again.")
        return
    
    order_id = order.get('order_id')
    
    # Get product and mark as sold
    product_data, error = get_product_for_purchase(product_id)
    
    if not product_data:
        from services.payments import add_wallet_balance
        add_wallet_balance(user_id, total)
        await query.edit_message_text(f"❌ {error}")
        return
    
    # Mark as sold
    purchase_success, purchased_product = purchase_product(product_id, user_id)
    
    if not purchase_success:
        from services.payments import add_wallet_balance
        add_wallet_balance(user_id, total)
        await query.edit_message_text("❌ Failed to complete purchase. Amount refunded.")
        return
    
    # Complete order
    phone = product_data.get('phone_number')
    session = product_data.get('session_string')
    complete_order_with_product(order_id, product_id, phone, session)
    
    # Send account details
    account_details = format_account_details(phone, session)
    
    await query.edit_message_text(
        f"✅ **Purchase Successful!**\n\n"
        f"Order ID: `{order_id}`\n"
        f"Amount: {format_amount(total)}\n\n"
        + account_details,
        parse_mode='Markdown'
    )
    
    # Clear purchase context
    context.user_data.pop('purchase_product', None)
    context.user_data.pop('purchase_quantity', None)
    context.user_data.pop('purchase_total', None)

@rate_limit_callback
async def back_to_countries_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to countries button"""
    query = update.callback_query
    await query.answer()
    
    countries = context.user_data.get('countries', get_all_countries())
    page = context.user_data.get('countries_page', 0)
    
    keyboard = get_countries_keyboard(countries, page)
    
    await query.edit_message_text(
        "🌍 **SELECT COUNTRY**\n\nChoose a country to see available products:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@rate_limit_callback
async def countries_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle countries pagination"""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.replace("countries_page_", ""))
    countries = context.user_data.get('countries', get_all_countries())
    
    context.user_data['countries_page'] = page
    keyboard = get_countries_keyboard(countries, page)
    
    await query.edit_message_text(
        "🌍 **SELECT COUNTRY**\n\nChoose a country to see available products:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Export handlers
def get_handlers():
    from telegram.ext import CallbackQueryHandler, MessageHandler, filters
    
    return [
        CallbackQueryHandler(buy_accounts_callback, pattern="^buy_accounts$"),
        CallbackQueryHandler(country_selection_callback, pattern="^country_\\d+$"),
        CallbackQueryHandler(buy_product_callback, pattern="^buy_product_\\d+$"),
        CallbackQueryHandler(quantity_selection_callback, pattern="^qty_\\d+_\\d+$"),
        CallbackQueryHandler(confirm_purchase_callback, pattern="^confirm_purchase_"),
        CallbackQueryHandler(back_to_countries_callback, pattern="^back_to_countries$"),
        CallbackQueryHandler(countries_page_callback, pattern="^countries_page_\\d+$"),
    ]
