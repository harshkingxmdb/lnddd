import logging
import asyncio
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Store OTP requests
otp_requests = {}

async def wait_for_otp(context, phone_number, timeout=120):
    """
    Wait for OTP to arrive for given phone number
    Returns OTP code or None if timeout
    """
    try:
        # Create a future for OTP
        future = asyncio.Future()
        
        # Store in global dict
        otp_requests[phone_number] = {
            'future': future,
            'created_at': datetime.now(),
            'timeout': timeout
        }
        
        # Wait for OTP with timeout
        try:
            otp = await asyncio.wait_for(future, timeout=timeout)
            return otp
        except asyncio.TimeoutError:
            logger.info(f"OTP timeout for {phone_number}")
            return None
        finally:
            # Clean up
            if phone_number in otp_requests:
                del otp_requests[phone_number]
                
    except Exception as e:
        logger.error(f"Error waiting for OTP: {e}")
        return None

def process_incoming_otp(message_text, message_from=None):
    """
    Process incoming message to extract OTP
    Returns OTP if found, else None
    """
    try:
        # Common OTP patterns
        patterns = [
            r'\b(\d{4})\b',           # 4 digit OTP
            r'\b(\d{5})\b',           # 5 digit OTP
            r'\b(\d{6})\b',           # 6 digit OTP
            r'OTP[:\s]*(\d{4,6})',     # OTP: 123456
            r'code[:\s]*(\d{4,6})',    # code: 123456
            r'verification[:\s]*(\d{4,6})', # verification: 123456
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                otp = match.group(1)
                logger.info(f"OTP detected: {otp}")
                return otp
        
        return None
        
    except Exception as e:
        logger.error(f"Error processing OTP: {e}")
        return None

def resolve_otp_for_phone(phone_number, otp):
    """Resolve OTP request for given phone number"""
    try:
        if phone_number in otp_requests:
            request = otp_requests[phone_number]
            future = request.get('future')
            
            if future and not future.done():
                future.set_result(otp)
                logger.info(f"OTP {otp} delivered for {phone_number}")
                return True
                
    except Exception as e:
        logger.error(f"Error resolving OTP: {e}")
    
    return False

def get_pending_otp_requests():
    """Get all pending OTP requests"""
    return {
        phone: {
            'created_at': data['created_at'],
            'timeout': data['timeout']
        }
        for phone, data in otp_requests.items()
        if not data['future'].done()
    }

async def forward_otp_to_user(context, user_id, phone_number, otp):
    """Forward OTP to user"""
    try:
        message = f"""
🔐 **OTP Received**

Phone: `{phone_number}`
OTP Code: `{otp}`

Enter this OTP in the login screen to complete verification.
"""
        await context.bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')
        return True
    except Exception as e:
        logger.error(f"Error forwarding OTP: {e}")
        return False

async def request_manual_otp(context, user_id, phone_number):
    """Request user to enter OTP manually"""
    try:
        message = f"""
📱 **OTP Required**

Please enter the OTP sent to `{phone_number}`

Type the OTP code here to complete verification.

Timeout: 2 minutes
"""
        await context.bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')
        return True
    except Exception as e:
        logger.error(f"Error requesting manual OTP: {e}")
        return False
