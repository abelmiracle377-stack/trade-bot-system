"""Telegram authorization boundary for trading commands."""

from src.accounts.registry import AccountRegistry


class TelegramAuthorizer:
    """Authorize Telegram users through the account registry."""

    def __init__(self, registry: AccountRegistry) -> None:
        self.registry = registry

    def require_registered(self, telegram_user_id: int) -> str:
        account = self.registry.require(telegram_user_id)
        return account.user_id
