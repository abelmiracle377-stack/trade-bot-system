import pytest

from src.accounts.models import UserAccount
from src.accounts.registry import AccountRegistry
from src.telegram.auth import TelegramAuthorizer


def test_telegram_authorization_requires_registration() -> None:
    authorizer = TelegramAuthorizer(AccountRegistry())

    with pytest.raises(PermissionError):
        authorizer.require_registered(999)


def test_telegram_authorization_returns_internal_user_id() -> None:
    registry = AccountRegistry()
    registry.register(UserAccount(user_id="user-1", telegram_user_id=123))

    assert TelegramAuthorizer(registry).require_registered(123) == "user-1"
