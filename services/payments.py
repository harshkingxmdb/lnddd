import logging
from database import (
    create_payment,
    get_payment_by_utr,
    verify_payment,
    update_wallet_balance,
    get_user
)
from utils.validators import validate_utr
from config import REFERRAL_DEPOSIT_THRESHOLD, REFERRAL_BONUS_AMOUNT

logger = logging.getLogger(__name__)

# Simulated UTR verification (in production, integrate with actual UPI API)
# For now, we'll auto-verify UTRs that are valid format
VERIFIED_UTR_CACHE = set()

def verify_utr_payment(utr_number, expected_amount=None):
    """
    Verify UTR payment
    In production, this should call actual UPI API
    """
    try:
        # Validate UTR format
        is_valid, message = validate_utr(utr_number)
        if not is_valid:
            return False, message
        
        # Check if UTR already used
        existing = get_payment_by_utr(utr_number)
        if existing:
            return False, "This UTR number has already been used"
        
        # For demo purposes, auto-verify all valid UTRs
        # In production, replace with actual UPI API call
        return True, "UTR verified successfully"
        
    except Exception as e:
        logger.error(f"Error verifying UTR: {e}")
        return False, str(e)

def create_payment_record(user_id, amount, utr_number, payment_method, order_id=None):
    """Create payment record after user submits UTR"""
    try:
        # Verify UTR first
        is_verified, message = verify_utr_payment(utr_number, amount)
        
        if not is_verified:
            return False, message
        
        # Create payment record
        payment = create_payment(user_id, amount, utr_number, payment_method, order_id)
        
        if not payment:
            return False, "Failed to create payment record"
        
        # Auto-verify payment (since UTR is valid)
        verified = verify_payment(payment.get('id'), user_id)
        
        if verified:
            # Add amount to user's wallet
            wallet_update = update_wallet_balance(user_id, amount, "add")
            
            if wallet_update:
                # Update total deposit
                user = get_user(user_id)
                total_deposit = user.get('total_deposit', 0) + amount
                from database import supabase
                supabase.table("users").update({"total_deposit": total_deposit}).eq("user_id", user_id).execute()
                
                # Check for referral bonus
                check_referral_bonus(user_id, amount)
                
                logger.info(f"Payment verified: {utr_number} for user {user_id}, amount ₹{amount}")
                return True, payment
            
        return False, "Payment verification failed"
        
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        return False, str(e)

def create_crypto_payment_record(user_id, amount, screenshot_url, order_id=None):
    """Create crypto payment record (manual verification)"""
    try:
        payment = create_payment(
            user_id, 
            amount, 
            utr_number=f"CRYPTO_{user_id}_{order_id}", 
            payment_method="crypto", 
            order_id=order_id
        )
        
        if payment:
            # Update with screenshot
            from database import supabase
            supabase.table("payments").update({"screenshot_url": screenshot_url}).eq("id", payment.get('id')).execute()
            
            logger.info(f"Crypto payment created for user {user_id}, amount ₹{amount}")
            return True, payment
        else:
            return False, "Failed to create crypto payment record"
            
    except Exception as e:
        logger.error(f"Error creating crypto payment: {e}")
        return False, str(e)

def add_wallet_balance(user_id, amount):
    """Add balance to user's wallet"""
    try:
        result = update_wallet_balance(user_id, amount, "add")
        
        if result:
            logger.info(f"Added ₹{amount} to wallet of user {user_id}")
            return True, result
        else:
            return False, "Failed to add balance"
            
    except Exception as e:
        logger.error(f"Error adding wallet balance: {e}")
        return False, str(e)

def deduct_wallet_balance(user_id, amount):
    """Deduct balance from user's wallet"""
    try:
        user = get_user(user_id)
        current_balance = user.get('wallet_balance', 0)
        
        if current_balance < amount:
            return False, f"Insufficient balance. Need ₹{amount}, have ₹{current_balance}"
        
        result = update_wallet_balance(user_id, amount, "deduct")
        
        if result:
            logger.info(f"Deducted ₹{amount} from wallet of user {user_id}")
            return True, result
        else:
            return False, "Failed to deduct balance"
            
    except Exception as e:
        logger.error(f"Error deducting wallet balance: {e}")
        return False, str(e)

def get_wallet_balance(user_id):
    """Get user's wallet balance"""
    try:
        user = get_user(user_id)
        return user.get('wallet_balance', 0) if user else 0
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        return 0

def check_referral_bonus(user_id, deposit_amount):
    """Check and give referral bonus if deposit meets threshold"""
    try:
        from database import get_referral_by_referred, add_referral_bonus
        
        if deposit_amount >= REFERRAL_DEPOSIT_THRESHOLD:
            referral = get_referral_by_referred(user_id)
            
            if referral and not referral.get('is_bonus_paid'):
                referrer_id = referral.get('referrer_id')
                add_referral_bonus(referrer_id, deposit_amount)
                logger.info(f"Referral bonus given to {referrer_id} for referring {user_id}")
                
    except Exception as e:
        logger.error(f"Error checking referral bonus: {e}")

def get_user_payments(user_id, limit=10):
    """Get user's payment history"""
    try:
        from database import supabase
        result = supabase.table("payments").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting user payments: {e}")
        return []
