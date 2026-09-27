import sys

import pytest

from scriba.config import get_config_dir, get_state_dir, load_config, save_config


def test_get_config_dir_default(monkeypatch, tmp_path):
    monkeypatch.delenv("SCRIBA_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr("scriba.config.Path.home", lambda: tmp_path)

    result = get_config_dir()

    assert result == tmp_path / ".config" / "scriba"
    assert result.is_dir()


@pytest.mark.skipif(sys.platform == "win32", reason="permissao POSIX nao se aplica no Windows")
def test_get_config_dir_is_created_with_restrictive_permissions(monkeypatch, tmp_path):
    monkeypatch.delenv("SCRIBA_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr("scriba.config.Path.home", lambda: tmp_path)

    result = get_config_dir()

    assert oct(result.stat().st_mode)[-3:] == "700"


def test_get_config_dir_honors_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.delenv("SCRIBA_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "custom-config"))

    result = get_config_dir()

    assert result == tmp_path / "custom-config" / "scriba"


def test_scriba_home_collapses_config_and_state(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path / "one-root"))

    assert get_config_dir() == tmp_path / "one-root"
    assert get_state_dir() == tmp_path / "one-root"


def test_save_and_load_config_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))

    save_config({"client_id": "abc", "tenant_id": "def"})
    result = load_config()

    assert result == {"client_id": "abc", "tenant_id": "def"}
