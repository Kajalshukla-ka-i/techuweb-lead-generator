import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


def validate_settings():
    """Validate required MongoDB environment variables."""

    required_settings = {
        "MONGODB_URI": MONGODB_URI,
        "DATABASE_NAME": DATABASE_NAME,
        "COLLECTION_NAME": COLLECTION_NAME,
    }

    missing_settings = [
        name
        for name, value in required_settings.items()
        if not value or not value.strip()
    ]

    if missing_settings:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing_settings)
            + ". Check your .env file or deployment environment."
        )
