"""Optional Telegram command interface.

This module deliberately contains no broker credentials and no direct broker calls.
Execution must be supplied through a separately authorized service boundary.
"""

from collections.abc import Callable

from src.telegram.auth import TelegramAuthorizer


class TradingTelegramHandlers:
    """Framework-neutral command handlers for a future Telegram adapter."""

    def __init__(self, authorizer: TelegramAuthorizer) -> None:
        self.authorizer = authorizer

    def status(self, telegram_user_id: int) -> str:
        user_id = self.authorizer.require_registered(telegram_user_id)
        return f"Trading account {user_id}: interface connected; execution state requires broker service."

    def register_command(self, name: str, handler: Callable[..., str]) -> tuple[str, Callable[..., str]]:
        if not name.startswith("/"):
            raise ValueError("command must start with /")
        return name, handler
