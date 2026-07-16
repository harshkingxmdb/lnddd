import re
from config import UTR_REGEX, UPI_REGEX

def validate_utr(utr_number):
    """
    Validate UTR (Unique Transaction Reference) number
    UTR is typically 12 digits
    """
    if not utr_number:
        return False, "UTR number cannot be empty"
    
    # Remove spaces
    utr_number = utr_number.strip()
    
    # Check if it's 12 digits
    if not re.match(r'^\d{12}$', utr_number):
        return False, "UTR number must be 12 digits"
    
    return True, "Valid UTR"

def validate_phone(phone_number):
    """
    Validate phone number
    Supports international format
    """
    if not phone_number:
        return False, "Phone number cannot be empty"
    
    # Remove spaces and special characters
    phone = re.sub(r'[\s\-\(\)\+]', '', phone_number)
    
    # Check if it's a valid phone number (8-15 digits)
    if not re.match(r'^\d{8,15}$', phone):
        return False, "Phone number must be 8-15 digits"
    
    return True, phone

def validate_amount(amount):
    """
    Validate amount
    Amount should be positive number
    """
    try:
        amount = float(amount)
        if amount <= 0:
            return False, "Amount must be greater than 0"
        if amount > 100000:
            return False, "Amount cannot exceed ₹100,000"
        return True, amount
    except ValueError:
        return False, "Invalid amount format"

def validate_upi_id(upi_id):
    """
    Validate UPI ID format
    Format: something@bankname
    """
    if not upi_id:
        return False, "UPI ID cannot be empty"
    
    if not re.match(UPI_REGEX, upi_id):
        return False, "Invalid UPI ID format"
    
    return True, upi_id

def validate_quantity(quantity, max_qty=10, min_qty=1):
    """
    Validate quantity
    """
    try:
        quantity = int(quantity)
        if quantity < min_qty:
            return False, f"Minimum quantity is {min_qty}"
        if quantity > max_qty:
            return False, f"Maximum quantity is {max_qty}"
        return True, quantity
    except ValueError:
        return False, "Invalid quantity"

def validate_country_id(country_id):
    """
    Validate country ID
    """
    try:
        country_id = int(country_id)
        if country_id <= 0:
            return False, "Invalid country ID"
        return True, country_id
    except ValueError:
        return False, "Invalid country ID format"

def validate_user_id(user_id):
    """
    Validate Telegram user ID
    """
    try:
        user_id = int(user_id)
        if user_id <= 0:
            return False, "Invalid user ID"
        return True, user_id
    except ValueError:
        return False, "Invalid user ID format"

def is_valid_session_string(session_string):
    """
    Validate session string (basic check)
    """
    if not session_string:
        return False, "Session string cannot be empty"
    
    if len(session_string) < 10:
        return False, "Session string too short"
    
    return True, session_string

def sanitize_input(text):
    """
    Sanitize user input to prevent injection
    """
    if not text:
        return ""
    
    # Remove dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    text = text.strip()
    
    return text
