from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

ADMIN_IDS: list[int] = [
    int(i) for i in os.getenv("ADMIN_IDS", "0").split(",")
]

# SQLite
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///foodbot.db"
)

# Bot settings
DELIVERY_COST: int = int(
    os.getenv("DELIVERY_COST", 10000)
)

FREE_DELIVERY_FROM: int = int(
    os.getenv("FREE_DELIVERY_FROM", 100000)
)

SUPPORT_USERNAME: str = os.getenv(
    "SUPPORT_USERNAME",
    "support"
)

# Payment
CLICK_MERCHANT_ID: str = os.getenv(
    "CLICK_MERCHANT_ID",
    ""
)

CLICK_SERVICE_ID: str = os.getenv(
    "CLICK_SERVICE_ID",
    ""
)

PAYME_MERCHANT_ID: str = os.getenv(
    "PAYME_MERCHANT_ID",
    ""
)

PAYME_SECRET_KEY: str = os.getenv(
    "PAYME_SECRET_KEY",
    ""
)

UZUM_MERCHANT_ID: str = os.getenv(
    "UZUM_MERCHANT_ID",
    ""
)