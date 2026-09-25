#!/usr/bin/env python3
"""Validate the latest scheduled trading-agent run status."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def check_health(path: str, max_age_hours: float) -> tuple[bool, str]:
    status_path = Path(path)
    if not status_path.exists():
        return False, f"status file not found: {status_path}"

    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
        timestamp = datetime.fromisoformat(payload["timestamp"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return False, f"invalid status file: {exc}"

    if payload.get("status") != "success":
        return False, f"last agent run was {payload.get('status', 'unknown')}"

    age = datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)
    if age > timedelta(hours=max_age_hours):
        return False, f"last successful run is too old: {age}"

    return True, "agent health is healthy"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status-file", default="data/runtime/last_run_status.json")
    parser.add_argument("--max-age-hours", type=float, default=36.0)
    args = parser.parse_args()

    healthy, message = check_health(args.status_file, args.max_age_hours)
    print(message)
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
