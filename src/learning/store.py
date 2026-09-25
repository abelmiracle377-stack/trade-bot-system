"""Append-only signal outcome storage for auditable learning datasets."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class SignalOutcome:
    """A signal and its eventual realized outcome."""

    signal_id: str
    user_id: str
    symbol: str
    direction: str
    probability: float
    entry_price: float
    exit_price: float | None = None
    realized_return: float | None = None
    outcome: str | None = None


class SignalOutcomeStore:
    """Persist signal outcomes as newline-delimited JSON records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, record: SignalOutcome) -> None:
        if not 0.0 <= record.probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if not record.symbol.strip():
            raise ValueError("symbol must not be empty")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")

    def read(self) -> list[SignalOutcome]:
        if not self.path.exists():
            return []
        records: list[SignalOutcome] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(SignalOutcome(**json.loads(line)))
        return records
