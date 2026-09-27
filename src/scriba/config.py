"""Resolução de diretórios XDG e I/O de config.toml — sem SO nativo (ADR
20260913-xdg-padrao-de-armazenamento-da-frota, XDG puro em qualquer SO)."""

import os
import sys
import tomllib
from pathlib import Path

import tomli_w

NAMESPACE = "scriba"
CONFIG_FILENAME = "config.toml"


def _xdg_or_default(env_var: str, default_subdir: str) -> Path:
    scriba_home = os.environ.get("SCRIBA_HOME")
    if scriba_home:
        return Path(scriba_home)

    value = os.environ.get(env_var)
    if value and Path(value).is_absolute():
        base = Path(value)
    else:
        base = Path.home() / default_subdir

    return base / NAMESPACE


def get_config_dir() -> Path:
    """Diretório de configuração — XDG_CONFIG_HOME, ou SCRIBA_HOME se definida."""
    path = _xdg_or_default("XDG_CONFIG_HOME", ".config")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def get_state_dir() -> Path:
    """Diretório de estado (token) — XDG_STATE_HOME, ou SCRIBA_HOME se definida."""
    path = _xdg_or_default("XDG_STATE_HOME", os.path.join(".local", "state"))
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def load_config() -> dict:
    """Lê config.toml; retorna dict vazio se ainda não existir."""
    config_file = get_config_dir() / CONFIG_FILENAME
    if not config_file.exists():
        return {}
    try:
        return tomllib.loads(config_file.read_text())
    except tomllib.TOMLDecodeError:
        print(f"Config corrompido: {config_file}", file=sys.stderr)
        sys.exit(1)


def save_config(config: dict) -> None:
    """Grava config.toml (0600)."""
    config_file = get_config_dir() / CONFIG_FILENAME
    config_file.write_bytes(tomli_w.dumps(config).encode())
    config_file.chmod(0o600)
