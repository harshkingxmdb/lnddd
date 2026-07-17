import os
import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, VIEW_AVAILABLE_STOCK
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = None

def init_supabase():
    """Initialize Supabase client"""
    global supabase
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client initialized successfully")
            return supabase
        else:
            logger.error("SUPABASE_URL or SUPABASE_KEY not set")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

def get_supabase():
    """Get Supabase client instance"""
    global supabase
    if supabase is None:
        supabase = init_supabase()
    return supabase

# PostgreSQL direct connection for complex queries
def get_db_connection():
    """Get direct PostgreSQL connection"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable is not set")
            return None
            
        conn = psycopg2.connect(
            db_url,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@contextmanager
def get_db_cursor():
    """Context manager for database cursor"""
    conn = get_db_connection()
    if conn is None:
        yield None
        return
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

# User Functions
def create_user(user_id, username=None, full_name=None):
    """Create a new user"""
    try:
        import random
        import string
        
        # Generate unique referral code
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        data = {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "referral_code": referral_code,
            "wallet_balance": 0.00,
            "total_deposit": 0.00,
            "terms_accepted": False,
            "is_banned": False,
            "is_admin": user_id in __import__('config').ADMIN_IDS
        }
        
        result = supabase.table("users").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

def get_user(user_id):
    """Get user by Telegram ID"""
    try:
        result = supabase.table("users").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def update_user(user_id, data):
    """Update user data"""
    try:
        result = supabase.table("users").update(data).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return None

def accept_terms(user_id):
    """Mark terms as accepted"""
    try:
        result = supabase.table("users").update({"terms_accepted": True}).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error accepting terms: {e}")
        return None

# Country Functions
def get_all_countries():
    """Get all active countries"""
    try:
        result = supabase.table("countries").select("*").eq("is_active", True).order("display_order").execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        return []

def get_country_by_id(country_id):
    """Get country by ID"""
    try:
        result = supabase.table("countries").select("*").eq("id", country_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting country: {e}")
        return None

# Stock Functions
def get_available_stock():
    """Get available stock count per country"""
    try:
        result = supabase.table(VIEW_AVAILABLE_STOCK).select("*").execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting stock: {e}")
        return []

def get_stock_by_country(country_id):
    """Get available products for a country"""
    try:
        result = supabase.table("products").select("*").eq("country_id", country_id).eq("status", "available").execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting stock by country: {e}")
        return []

def add_product(country_id, phone_number, session_string, price, added_by):
    """Add new product to stock"""
    try:
        data = {
            "country_id": country_id,
            "phone_number": phone_number,
            "session_string": session_string,
            "price": price,
            "status": "available",
            "added_by": added_by
        }
        result = supabase.table("products").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        return None

def get_product_by_id(product_id):
    """Get product by ID"""
    try:
        result = supabase.table("products").select("*").eq("id", product_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        return None

def mark_product_sold(product_id, user_id):
    """Mark product as sold"""
    try:
        data = {
            "status": "sold",
            "sold_to": user_id,
            "sold_at": "now()"
        }
        result = supabase.table("products").update(data).eq("id", product_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error marking product sold: {e}")
        return None

# Order Functions
def create_order(order_id, user_id, amount, payment_method):
    """Create a new order"""
    try:
        data = {
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "payment_method": payment_method,
            "status": "pending"
        }
        result = supabase.table("orders").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return None

def update_order_with_product(order_id, product_id, phone_number, session_string):
    """Update order with product details"""
    try:
        data = {
            "product_id": product_id,
            "phone_number": phone_number,
            "session_string": session_string,
            "status": "completed",
            "completed_at": "now()"
        }
        result = supabase.table("orders").update(data).eq("order_id", order_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        return None

def get_user_orders(user_id, limit=10):
    """Get user's orders"""
    try:
        result = supabase.table("orders").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting user orders: {e}")
        return []

def get_order_by_id(order_id):
    """Get order by ID"""
    try:
        result = supabase.table("orders").select("*").eq("order_id", order_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        return None

# Payment Functions
def create_payment(user_id, amount, utr_number, payment_method, order_id=None):
    """Create a payment record"""
    try:
        import uuid
        txn_id = str(uuid.uuid4())[:8]
        
        data = {
            "txn_id": txn_id,
            "user_id": user_id,
            "order_id": order_id,
            "amount": amount,
            "utr_number": utr_number,
            "payment_method": payment_method,
            "status": "pending"
        }
        result = supabase.table("payments").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        return None

def get_payment_by_utr(utr_number):
    """Get payment by UTR number"""
    try:
        result = supabase.table("payments").select("*").eq("utr_number", utr_number).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting payment: {e}")
        return None

def verify_payment(payment_id, verified_by):
    """Verify a payment"""
    try:
        data = {
            "status": "verified",
            "verified_by": verified_by,
            "verified_at": "now()"
        }
        result = supabase.table("payments").update(data).eq("id", payment_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        return None

def update_wallet_balance(user_id, amount, operation="add"):
    """Update user wallet balance"""
    try:
        user = get_user(user_id)
        if not user:
            return None
        
        current_balance = user.get("wallet_balance", 0)
        
        if operation == "add":
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount
            
            if new_balance < 0:
                return None
        
        result = supabase.table("users").update({"wallet_balance": new_balance}).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating wallet: {e}")
        return None

# Referral Functions
def create_referral(referrer_id, referred_id):
    """Create referral record"""
    try:
        data = {
            "referrer_id": referrer_id,
            "referred_id": referred_id
        }
        result = supabase.table("referrals").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating referral: {e}")
        return None

def get_referral_by_referred(referred_id):
    """Get referral by referred user ID"""
    try:
        result = supabase.table("referrals").select("*").eq("referred_id", referred_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting referral: {e}")
        return None

def add_referral_bonus(referrer_id, deposit_amount):
    """Add referral bonus if deposit meets threshold"""
    try:
        from config import REFERRAL_DEPOSIT_THRESHOLD, REFERRAL_BONUS_AMOUNT
        
        if deposit_amount >= REFERRAL_DEPOSIT_THRESHOLD:
            # Update referral record
            result = supabase.table("referrals").update({
                "deposit_amount": deposit_amount,
                "bonus_credited": REFERRAL_BONUS_AMOUNT,
                "is_bonus_paid": True,
                "bonus_paid_at": "now()"
            }).eq("referrer_id", referrer_id).execute()
            
            # Add bonus to referrer's wallet
            if result.data:
                update_wallet_balance(referrer_id, REFERRAL_BONUS_AMOUNT, "add")
                return True
        return False
    except Exception as e:
        logger.error(f"Error adding referral bonus: {e}")
        return False

# Activity Log Functions
def log_activity(user_id, action, details=None, ip_address=None):
    """Log user activity"""
    try:
        import json
        data = {
            "user_id": user_id,
            "action": action,
            "details": json.dumps(details) if details else None,
            "ip_address": ip_address
        }
        supabase.table("activity_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

# Initialize Supabase on import
init_supabase()


def get_all_users():
    """Get all users from the database"""
    try:
        response = supabase.from_("users").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []
