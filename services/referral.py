import logging
from database import (
    create_referral,
    get_referral_by_referred,
    get_user,
    update_user
)
from utils.helpers import generate_referral_code
from config import REFERRAL_BONUS_AMOUNT, REFERRAL_DEPOSIT_THRESHOLD

logger = logging.getLogger(__name__)

def generate_user_referral_code(user_id):
    """Generate referral code for user"""
    try:
        referral_code = generate_referral_code(user_id)
        
        # Update user with referral code
        update_user(user_id, {"referral_code": referral_code})
        
        return referral_code
    except Exception as e:
        logger.error(f"Error generating referral code: {e}")
        return None

def get_user_referral_code(user_id):
    """Get user's referral code"""
    try:
        user = get_user(user_id)
        
        if user and user.get('referral_code'):
            return user.get('referral_code')
        else:
            return generate_user_referral_code(user_id)
            
    except Exception as e:
        logger.error(f"Error getting referral code: {e}")
        return None

def get_referral_link(user_id, bot_username):
    """Get full referral link for user"""
    try:
        referral_code = get_user_referral_code(user_id)
        if referral_code:
            return f"https://t.me/{bot_username}?start=ref_{referral_code}"
        return None
    except Exception as e:
        logger.error(f"Error getting referral link: {e}")
        return None

def track_referral(referred_user_id, referrer_code):
    """Track when a user signs up with referral code"""
    try:
        # Find referrer by referral code
        from database import supabase
        result = supabase.table("users").select("user_id").eq("referral_code", referrer_code).execute()
        
        if not result.data:
            logger.warning(f"Invalid referral code: {referrer_code}")
            return False, "Invalid referral code"
        
        referrer_id = result.data[0].get('user_id')
        
        # Don't allow self-referral
        if referrer_id == referred_user_id:
            logger.warning(f"Self-referral attempt by {referred_user_id}")
            return False, "You cannot refer yourself"
        
        # Check if already referred
        existing = get_referral_by_referred(referred_user_id)
        if existing:
            logger.info(f"User {referred_user_id} already referred by {existing.get('referrer_id')}")
            return False, "Already referred by someone else"
        
        # Create referral record
        referral = create_referral(referrer_id, referred_user_id)
        
        if referral:
            logger.info(f"Referral tracked: {referrer_id} referred {referred_user_id}")
            return True, referral
        else:
            return False, "Failed to track referral"
            
    except Exception as e:
        logger.error(f"Error tracking referral: {e}")
        return False, str(e)

def get_referrer_of(user_id):
    """Get who referred this user"""
    try:
        referral = get_referral_by_referred(user_id)
        
        if referral:
            referrer_id = referral.get('referrer_id')
            referrer = get_user(referrer_id)
            return referrer
        return None
        
    except Exception as e:
        logger.error(f"Error getting referrer: {e}")
        return None

def get_referral_stats(user_id):
    """Get referral statistics for a user"""
    try:
        from database import supabase
        
        # Get all referrals by this user
        result = supabase.table("referrals").select("*").eq("referrer_id", user_id).execute()
        
        referrals = result.data if result.data else []
        
        total_referrals = len(referrals)
        total_bonus = sum(r.get('bonus_credited', 0) for r in referrals if r.get('is_bonus_paid'))
        pending_bonus = sum(
            r.get('deposit_amount', 0) for r in referrals 
            if not r.get('is_bonus_paid') and r.get('deposit_amount', 0) >= REFERRAL_DEPOSIT_THRESHOLD
        )
        
        return {
            'total_referrals': total_referrals,
            'total_bonus': total_bonus,
            'pending_bonus': pending_bonus,
            'referrals': referrals,
            'threshold': REFERRAL_DEPOSIT_THRESHOLD,
            'bonus_amount': REFERRAL_BONUS_AMOUNT
        }
        
    except Exception as e:
        logger.error(f"Error getting referral stats: {e}")
        return {
            'total_referrals': 0,
            'total_bonus': 0,
            'pending_bonus': 0,
            'referrals': [],
            'threshold': REFERRAL_DEPOSIT_THRESHOLD,
            'bonus_amount': REFERRAL_BONUS_AMOUNT
        }

def get_referral_earnings(user_id):
    """Get total referral earnings"""
    try:
        stats = get_referral_stats(user_id)
        return stats.get('total_bonus', 0)
    except Exception as e:
        logger.error(f"Error getting referral earnings: {e}")
        return 0
