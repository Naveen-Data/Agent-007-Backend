import logging
import uuid

logger = logging.getLogger("app.utils")


def new_request_id() -> str:
    return uuid.uuid4().hex


def safe_trim(text: str, n: int = 500) -> str:
    return text if len(text) <= n else text[:n] + "..."
