
import os

API_BASE = os.getenv(
    "ECHOCHAT_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


def get_api_url(path: str) -> str:
    return f"{API_BASE}/{path.lstrip('/')}"
