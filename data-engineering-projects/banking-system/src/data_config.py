# config/data_config.py

# List of possible currencies with their symbols
CURRENCIES = [
    {"code": "USD", "symbol": "$"},  # United States Dollar
    {"code": "EUR", "symbol": "€"}  # Euro
]

# List of possible countries
COUNTRIES = [
    "USA",
    "France"
]

# List of possible merchant types based on the enum
MERCHANT_TYPES = [
    "online",      # E-commerce businesses
    "retail",      # Brick-and-mortar stores
    "restaurant",  # Restaurants and dining establishments
    "service",     # Service-oriented businesses (e.g., cleaning, repair)
    "grocery",     # Grocery stores
    "other"        # Other types of merchants
]

# List of possible account types based on the enum
ACCOUNT_TYPES = [
    "savings",  # Savings account
    "checking",  # Checking account
    "credit"     # Credit account
]

# List of possible transaction types based on the enum
TRANSACTION_TYPES = [
    # "deposit",    # Adding money to an account
    # "withdrawal", # Taking money out of an account
     "purchase",   # Buying goods or services
    # "cheque deposit", 
    # "cheque withdrawal",    # Payment made via cheque
    # "charge",     # Charging an amount to an account
     "POS",        # Point of Sale transactions
     "payment",    # General payments to vendors or services
    # "transfer"    # Moving money from one account to another
]

# List of possible POS payments based on merchant types
POS_PAYMENTS = {
    "restaurant": [
        "dine-in",       # Dining at the restaurant
        "takeaway",      # Taking food away from the restaurant
        "delivery"       # Food delivery service
    ],
    "retail": [
        "in-store",      # Shopping in a physical store
        "online",        # Shopping online
        "curbside"       # Curbside pickup
    ],
    "service": [
        "appointment",   # Scheduled service appointments
        "walk-in",       # Walk-in services
        "subscription"   # Subscription-based services
    ],
    "grocery": [
        "in-store",      # Shopping in a physical grocery store
        "online",        # Online grocery shopping
        "delivery"       # Grocery delivery service
    ],
    "other": [
        "miscellaneous"  # Miscellaneous POS payments
    ]
}