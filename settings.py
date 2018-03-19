DATABASE = {
    'database': 'mws',
    'user': 'mws',
    'password': 'F&l>]0vd%?1?vD',
    'host': 'localhost',
}

SNS_PLATFORM_ARNS = {
    "FCM": "arn:aws:sns:eu-west-1:865335715419:app/GCM/Exa_Wallet_Stage",
    "APNS": "arn:aws:sns:eu-west-1:865335715419:app/APNS/Exa_Wallet_iOS_Stage",
    "APNS_DEMO": "arn:aws:sns:eu-west-1:865335715419:app/APNS_SANDBOX/Exa_Wallet_iOS_DEMO_Stage"
}

SNS_ACCESS_KEY_ID = ""
SNS_SECRET_ACCESS_KEY = ""
SNS_REGION = "eu-west-1"

REDIS_URL = "redis://localhost/0"

try:
    from local_settings import *
except ImportError:
    pass
