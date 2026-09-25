from src.accounts.models import TradingPermission, UserAccount
from src.accounts.registry import AccountRegistry


def test_registry_isolates_users_without_credentials() -> None:
    registry = AccountRegistry()
    account = UserAccount(
        user_id="user-1",
        telegram_user_id=123,
        broker_account_id="broker-1",
        permission=TradingPermission.PAPER,
    )
    registry.register(account)

    assert registry.require(123) == account
    assert registry.get(456) is None
