import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Payment Configuration
UPI_IDS = [
    os.getenv("UPI_ID_1"),
    os.getenv("UPI_ID_2"),
]
UPI_IDS = [upi for upi in UPI_IDS if upi]  # Remove empty ones

# UPI QR Image URL (Set this in environment variables or here)
UPI_QR_URL = os.getenv("UPI_QR_URL", "https://litter.catbox.moe/an43st.jpg")

CRYPTO_USDT_ADDRESS = os.getenv("CRYPTO_USDT_ADDRESS")

# Mandatory Channels for Force Join
MANDATORY_CHANNELS = [
    {"name": " SHONA OTP Support", "id": -1003840085852, "url": "https://t.me/+Oy07CljKuERjYTFh"},
    {"name": "SHONA OTP UPDATES", "id": -1003969175933, "url": "https://t.me/OTPPP_UPDATESSSS"},
    {"name": "🚨 PRICE DROP ALERT 🚨", "id": -1004370918854, "url": "https://t.me/shonaStoreSupport"},
]

# Admin Configuration
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# Feature Flags
ENABLE_REFERRAL = os.getenv("ENABLE_REFERRAL", "True").lower() == "true"
ENABLE_PREMIUM_FEATURES = os.getenv("ENABLE_PREMIUM_FEATURES", "True").lower() == "true"
ENABLE_BLOCKQUOTES = os.getenv("ENABLE_BLOCKQUOTES", "True").lower() == "true"
ENABLE_COLORED_BUTTONS = os.getenv("ENABLE_COLORED_BUTTONS", "True").lower() == "true"

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Bot Info
BOT_VERSION = "1.0.0"
BOT_NAME = "Toxic Store Bot"

# Payment Constants
MIN_DEPOSIT = 10  # Minimum deposit in INR
REFERRAL_BONUS_AMOUNT = 20  # ₹20 bonus on ₹1000 deposit
REFERRAL_DEPOSIT_THRESHOLD = 1000  # ₹1000 minimum deposit for referral bonus

# UPI Validation
UPI_REGEX = r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{3,}$"
UTR_REGEX = r"^[0-9]{12}$"  # 12 digit UTR number

# Database Tables
TABLE_USERS = "users"
TABLE_COUNTRIES = "countries"
TABLE_PRODUCTS = "products"
TABLE_ORDERS = "orders"
TABLE_PAYMENTS = "payments"
TABLE_REFERRALS = "referrals"
TABLE_ACTIVITY_LOGS = "activity_logs"
VIEW_AVAILABLE_STOCK = os.getenv("VIEW_AVAILABLE_STOCK", "available_stock")
