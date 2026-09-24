from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_security_policy_exists():
    assert (ROOT / "SECURITY.md").is_file()


def test_example_environment_file_exists():
    assert (ROOT / ".env.example").is_file()


def test_root_env_file_is_not_present():
    assert not (ROOT / ".env").exists()


def test_trading_security_documentation_exists():
    assert (ROOT / "docs" / "TRADING_SECURITY.md").is_file()
