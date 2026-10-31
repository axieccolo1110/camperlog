import os
import subprocess
import sys

import pytest
from click.testing import CliRunner

from camperlog.cli import cli
from camperlog.config import ConfigError, missing_web_vars, require_web_config

WEB_VARS = ("CAMPERLOG_PASSWORD", "CAMPERLOG_SECRET_KEY")


@pytest.fixture
def no_web_vars(monkeypatch):
    for name in WEB_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def with_web_vars(monkeypatch):
    monkeypatch.setenv("CAMPERLOG_PASSWORD", "pw")
    monkeypatch.setenv("CAMPERLOG_SECRET_KEY", "key")


def test_nothing_missing_when_both_set(with_web_vars):
    assert missing_web_vars() == []
    require_web_config()


@pytest.mark.parametrize("name", WEB_VARS)
def test_each_variable_is_required(with_web_vars, monkeypatch, name):
    monkeypatch.delenv(name)
    with pytest.raises(ConfigError, match=name):
        require_web_config()


def test_empty_or_blank_value_counts_as_missing(with_web_vars, monkeypatch):
    monkeypatch.setenv("CAMPERLOG_PASSWORD", "")
    monkeypatch.setenv("CAMPERLOG_SECRET_KEY", "   ")
    assert missing_web_vars() == list(WEB_VARS)


def test_message_is_german_and_names_both_variables(no_web_vars):
    with pytest.raises(ConfigError) as exc:
        require_web_config()
    msg = str(exc.value)
    assert "Webserver startet nicht" in msg
    assert "CAMPERLOG_PASSWORD" in msg and "CAMPERLOG_SECRET_KEY" in msg


def test_create_app_refuses_without_config(no_web_vars):
    from camperlog.web.app import create_app

    with pytest.raises(ConfigError):
        create_app()


def test_serve_aborts_without_config_and_does_not_start_server(
    no_web_vars, monkeypatch
):
    import uvicorn

    started = []
    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: started.append(1))

    result = CliRunner().invoke(cli, ["serve"])

    assert result.exit_code != 0
    assert "CAMPERLOG_PASSWORD" in result.output
    assert "CAMPERLOG_SECRET_KEY" in result.output
    assert started == []


def test_serve_starts_with_config(with_web_vars, monkeypatch):
    import uvicorn

    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: calls.append((a, kw)))

    result = CliRunner().invoke(cli, ["serve"])

    assert result.exit_code == 0
    assert calls[0][0] == ("camperlog.web.app:app",)


def test_other_cli_commands_work_without_config(no_web_vars, test_db):
    runner = CliRunner()
    assert runner.invoke(cli, ["--help"]).exit_code == 0
    assert runner.invoke(cli, ["trip", "list"]).exit_code == 0
    assert runner.invoke(cli, ["fuel", "list"]).exit_code == 0


def test_uvicorn_direct_start_aborts_without_config(tmp_path):
    """Railway starts uvicorn directly, not via ``camperlog serve``."""
    env = {k: v for k, v in os.environ.items() if k not in WEB_VARS}
    env["DATABASE_URL"] = f"sqlite:///{tmp_path / 'x.db'}"

    proc = subprocess.run(
        [sys.executable, "-m", "uvicorn", "camperlog.web.app:app", "--port", "0"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert proc.returncode != 0
    assert "CAMPERLOG_PASSWORD" in proc.stderr
    assert "CAMPERLOG_SECRET_KEY" in proc.stderr
