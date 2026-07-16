import logging
from database import (
    get_available_stock, 
    get_stock_by_country, 
    add_product, 
    get_product_by_id,
    mark_product_sold,
    get_country_by_id
)
from utils.validators import validate_phone, is_valid_session_string

logger = logging.getLogger(__name__)

def get_all_stock_with_country():
    """Get all stock with country names"""
    try:
        stock_data = get_available_stock()
        return stock_data
    except Exception as e:
        logger.error(f"Error getting all stock: {e}")
        return []

def get_stock_for_country(country_id):
    """Get available stock for a specific country"""
    try:
        products = get_stock_by_country(country_id)
        return products
    except Exception as e:
        logger.error(f"Error getting stock for country {country_id}: {e}")
        return []

def get_stock_count(country_id):
    """Get available stock count for a country"""
    try:
        products = get_stock_by_country(country_id)
        return len(products) if products else 0
    except Exception as e:
        logger.error(f"Error getting stock count: {e}")
        return 0

def check_stock_available(country_id, quantity=1):
    """Check if enough stock is available"""
    try:
        available_count = get_stock_count(country_id)
        return available_count >= quantity, available_count
    except Exception as e:
        logger.error(f"Error checking stock: {e}")
        return False, 0

def add_new_stock(country_id, phone_number, session_string, price, added_by):
    """Add new stock to database"""
    try:
        # Validate inputs
        is_valid_phone, phone_result = validate_phone(phone_number)
        if not is_valid_phone:
            return False, phone_result
        
        is_valid_session, session_result = is_valid_session_string(session_string)
        if not is_valid_session:
            return False, session_result
        
        # Validate price
        try:
            price = float(price)
            if price <= 0:
                return False, "Price must be greater than 0"
        except:
            return False, "Invalid price format"
        
        # Check if country exists
        country = get_country_by_id(country_id)
        if not country:
            return False, "Country not found"
        
        # Add product
        product = add_product(country_id, phone_result, session_string, price, added_by)
        
        if product:
            logger.info(f"Stock added: {phone_result} for {country.get('name')} by {added_by}")
            return True, product
        else:
            return False, "Failed to add stock"
            
    except Exception as e:
        logger.error(f"Error adding stock: {e}")
        return False, str(e)

def get_product_for_purchase(product_id):
    """Get product and mark as sold (atomic operation)"""
    try:
        product = get_product_by_id(product_id)
        
        if not product:
            return None, "Product not found"
        
        if product.get('status') != 'available':
            return None, "Product not available"
        
        return product, None
        
    except Exception as e:
        logger.error(f"Error getting product for purchase: {e}")
        return None, str(e)

def purchase_product(product_id, user_id):
    """Mark product as sold to user"""
    try:
        product = mark_product_sold(product_id, user_id)
        
        if product:
            logger.info(f"Product {product_id} sold to user {user_id}")
            return True, product
        else:
            return False, "Failed to mark product as sold"
            
    except Exception as e:
        logger.error(f"Error purchasing product: {e}")
        return False, str(e)

def get_all_countries_stock_summary():
    """Get stock summary for all countries"""
    try:
        stock_summary = get_available_stock()
        
        summary = {}
        for item in stock_summary:
            summary[item.get('country_id')] = {
                'name': item.get('country_name'),
                'flag': item.get('flag'),
                'available': item.get('available_count', 0)
            }
        
        return summary
    except Exception as e:
        logger.error(f"Error getting stock summary: {e}")
        return {}

def is_country_available(country_id):
    """Check if country has any stock"""
    try:
        count = get_stock_count(country_id)
        return count > 0, count
    except Exception as e:
        logger.error(f"Error checking country availability: {e}")
        return False, 0
