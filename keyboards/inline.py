from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_terms_keyboard():
    """Terms & Conditions keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ I Accept & Agree", 
                callback_data="accept_terms"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Decline", 
                callback_data="decline_terms"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🛒 Buy Accounts", 
                callback_data="buy_accounts"
            ),
            InlineKeyboardButton(
                text="💰 Add Funds", 
                callback_data="add_funds"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎁 Earn Money", 
                callback_data="earn_money"
            ),
            InlineKeyboardButton(
                text="👤 My Profile", 
                callback_data="my_profile"
            )
        ],
        [
            InlineKeyboardButton(
                text="🆘 Support", 
                callback_data="support"
            ),
            InlineKeyboardButton(
                text="ℹ️ How to Use", 
                callback_data="how_to_use"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_countries_keyboard(countries, page=0, items_per_page=10):
    """Get countries keyboard with pagination"""
    keyboard = []
    
    # Calculate pagination
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_countries = countries[start_idx:end_idx]
    
    # Add country buttons (2 per row)
    row = []
    for i, country in enumerate(page_countries):
        button_text = f"{country.get('flag', '🏳️')} {country.get('name')}"
        callback_data = f"country_{country.get('id')}"
        row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        
        if len(row) == 2 or i == len(page_countries) - 1:
            keyboard.append(row)
            row = []
    
    # Pagination buttons
    pagination_row = []
    total_pages = (len(countries) + items_per_page - 1) // items_per_page
    
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="◀️ Previous", callback_data=f"countries_page_{page - 1}"))
    
    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"countries_page_{page + 1}"))
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Back button
    keyboard.append([
        InlineKeyboardButton(text="↩️ Back to Menu", callback_data="back_to_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_payment_methods_keyboard():
    """Payment methods keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="💳 UPI (Auto - Fast)", 
                callback_data="payment_upi"
            )
        ],
        [
            InlineKeyboardButton(
                text="🪙 Crypto (USDT - Manual)", 
                callback_data="payment_crypto"
            )
        ],
        [
            InlineKeyboardButton(
                text="↩️ Back to Home", 
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quantity_keyboard(product_id, price, max_qty=10):
    """Quantity selection keyboard"""
    keyboard = []
    
    # Quantity buttons (1-5, 6-10)
    row1 = []
    for qty in range(1, 6):
        if qty <= max_qty:
            row1.append(InlineKeyboardButton(text=str(qty), callback_data=f"qty_{product_id}_{qty}"))
    if row1:
        keyboard.append(row1)
    
    row2 = []
    for qty in range(6, 11):
        if qty <= max_qty:
            row2.append(InlineKeyboardButton(text=str(qty), callback_data=f"qty_{product_id}_{qty}"))
    if row2:
        keyboard.append(row2)
    
    # Custom amount
    keyboard.append([
        InlineKeyboardButton(text="🔢 Custom Amount", callback_data=f"custom_qty_{product_id}")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton(text="↩️ Back", callback_data="back_to_countries")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_confirm_purchase_keyboard(product_id, quantity, total_amount):
    """Confirm purchase keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"✅ Confirm - ₹{total_amount}", 
                callback_data=f"confirm_purchase_{product_id}_{quantity}"
            )
        ],
        [
            InlineKeyboardButton(
                text="↩️ Back", 
                callback_data="back_to_quantity"
            ),
            InlineKeyboardButton(
                text="❌ Cancel", 
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_profile_keyboard():
    """Profile menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="💰 Deposit Now", 
                callback_data="add_funds"
            )
        ],
        [
            InlineKeyboardButton(
                text="📦 My Orders", 
                callback_data="my_orders"
            ),
            InlineKeyboardButton(
                text="💸 My Payments", 
                callback_data="my_payments"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔑 Get OTP", 
                callback_data="get_otp"
            )
        ],
        [
            InlineKeyboardButton(
                text="↩️ Back to Menu", 
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(back_callback="back_to_menu"):
    """Simple back button keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="↩️ Back", 
                callback_data=back_callback
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_panel_keyboard():
    """Admin panel keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="➕ Add Country", 
                callback_data="admin_add_country"
            ),
            InlineKeyboardButton(
                text="📦 Add Stock", 
                callback_data="admin_add_stock"
            )
        ],
        [
            InlineKeyboardButton(
                text="👁️ View Stock", 
                callback_data="admin_view_stock"
            ),
            InlineKeyboardButton(
                text="📋 View Orders", 
                callback_data="admin_view_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Verify Payment", 
                callback_data="admin_verify_payment"
            ),
            InlineKeyboardButton(
                text="📊 Stats", 
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Broadcast", 
                callback_data="admin_broadcast"
            ),
            InlineKeyboardButton(
                text="🚫 Ban User", 
                callback_data="admin_ban"
            )
        ],
        [
            InlineKeyboardButton(
                text="↩️ Back to Menu", 
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_product_action_keyboard(product_id):
    """Get keyboard for product actions"""
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Now", callback_data=f"buy_prod_{product_id}")],
        [InlineKeyboardButton("🔙 Back to Products", callback_data="view_products")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_orders_keyboard(orders):
    """Orders list keyboard"""
    keyboard = []
    
    for order in orders[:10]:  # Max 10 orders
        order_id = order.get('order_id', '')[:8]
        amount = order.get('amount', 0)
        status = order.get('status', 'pending')
        
        status_emoji = "✅" if status == "completed" else "⏳"
        button_text = f"{status_emoji} {order_id} - ₹{amount}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text, 
                callback_data=f"order_detail_{order.get('order_id')}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="↩️ Back to Profile", callback_data="my_profile")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_payments_keyboard(payments):
    """Payments list keyboard"""
    keyboard = []
    
    for payment in payments[:10]:
        txn_id = payment.get('txn_id', '')[:8]
        amount = payment.get('amount', 0)
        status = payment.get('status', 'pending')
        
        status_emoji = "✅" if status == "verified" else "⏳"
        button_text = f"{status_emoji} {txn_id} - ₹{amount}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text, 
                callback_data=f"payment_detail_{payment.get('id')}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="↩️ Back to Profile", callback_data="my_profile")
    ])
    
    return InlineKeyboardMarkup(keyboard)
