"""Models for isolating users, broker accounts, and trading permissions."""

from dataclasses import dataclass
from enum import Enum


class TradingPermission(str, Enum):
    READ_ONLY = "read_only"
    PAPER = "paper"
    LIVE = "live"


@dataclass(frozen=True)
class UserAccount:
    """Non-secret identity and trading permission metadata."""

    user_id: str
    telegram_user_id: int
    broker_account_id: str | None = None
    permission: TradingPermission = TradingPermission.READ_ONLY
    enabled: bool = True
