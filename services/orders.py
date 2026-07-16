import logging
from database import (
    create_order, 
    update_order_with_product, 
    get_user_orders, 
    get_order_by_id
)
from utils.helpers import generate_order_id
from services.stock import get_product_by_id

logger = logging.getLogger(__name__)

def create_new_order(user_id, amount, payment_method):
    """Create a new order"""
    try:
        order_id = generate_order_id()
        order = create_order(order_id, user_id, amount, payment_method)
        
        if order:
            logger.info(f"Order created: {order_id} for user {user_id}")
            return True, order
        else:
            return False, "Failed to create order"
            
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return False, str(e)

def complete_order_with_product(order_id, product_id, phone_number, session_string):
    """Complete order with product details"""
    try:
        order = update_order_with_product(order_id, product_id, phone_number, session_string)
        
        if order:
            logger.info(f"Order completed: {order_id}")
            return True, order
        else:
            return False, "Failed to complete order"
            
    except Exception as e:
        logger.error(f"Error completing order: {e}")
        return False, str(e)

def get_user_order_history(user_id, limit=10):
    """Get user's order history"""
    try:
        orders = get_user_orders(user_id, limit)
        return orders
    except Exception as e:
        logger.error(f"Error getting order history: {e}")
        return []

def get_order_details(order_id):
    """Get detailed order information"""
    try:
        order = get_order_by_id(order_id)
        return order
    except Exception as e:
        logger.error(f"Error getting order details: {e}")
        return None

def get_user_active_orders(user_id):
    """Get user's pending/completed orders"""
    try:
        all_orders = get_user_orders(user_id, limit=50)
        
        if not all_orders:
            return []
        
        # Filter orders that have product details
        active_orders = [
            order for order in all_orders 
            if order.get('product_id') and order.get('status') == 'completed'
        ]
        
        return active_orders
    except Exception as e:
        logger.error(f"Error getting active orders: {e}")
        return []

def get_order_by_product_id(product_id):
    """Get order associated with product"""
    try:
        # This might need a direct query in database.py
        # For now, return None
        return None
    except Exception as e:
        logger.error(f"Error getting order by product: {e}")
        return None

def update_order_status(order_id, status):
    """Update order status"""
    try:
        from database import supabase
        result = supabase.table("orders").update({"status": status}).eq("order_id", order_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        return None
