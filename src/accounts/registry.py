"""In-memory account registry used as a safe foundation for a persistent store."""

from .models import UserAccount


class AccountRegistry:
    """Register Telegram users without storing broker secrets."""

    def __init__(self) -> None:
        self._accounts: dict[int, UserAccount] = {}

    def register(self, account: UserAccount) -> None:
        if not account.enabled:
            raise ValueError("disabled accounts cannot be registered")
        self._accounts[account.telegram_user_id] = account

    def get(self, telegram_user_id: int) -> UserAccount | None:
        return self._accounts.get(telegram_user_id)

    def require(self, telegram_user_id: int) -> UserAccount:
        account = self.get(telegram_user_id)
        if account is None:
            raise PermissionError("Telegram user is not registered")
        return account
