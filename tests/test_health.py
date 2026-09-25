import json
from datetime import datetime, timedelta, timezone

from scripts.check_health import check_health


def test_health_accepts_recent_success(tmp_path):
    path = tmp_path / "status.json"
    path.write_text(
        json.dumps(
            {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        encoding="utf-8",
    )

    healthy, message = check_health(str(path), max_age_hours=36)

    assert healthy is True
    assert "healthy" in message


def test_health_rejects_failed_run(tmp_path):
    path = tmp_path / "status.json"
    path.write_text(
        json.dumps(
            {
                "status": "failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "broker unavailable",
            }
        ),
        encoding="utf-8",
    )

    healthy, message = check_health(str(path), max_age_hours=36)

    assert healthy is False
    assert "failed" in message


def test_health_rejects_stale_success(tmp_path):
    path = tmp_path / "status.json"
    path.write_text(
        json.dumps(
            {
                "status": "success",
                "timestamp": (
                    datetime.now(timezone.utc) - timedelta(hours=40)
                ).isoformat(),
            }
        ),
        encoding="utf-8",
    )

    healthy, message = check_health(str(path), max_age_hours=36)

    assert healthy is False
    assert "too old" in message
