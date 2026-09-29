from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from scriba import auth
from scriba.auth import SCOPES, _get_graph_scopes


def test_scopes_never_include_mail_send(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))

    scopes = _get_graph_scopes(client_id="dummy-client-id", tenant_id="common")

    assert not any(s.endswith("/Mail.Send") for s in scopes)
    assert "https://graph.microsoft.com/Mail.ReadWrite" in scopes
    assert "https://graph.microsoft.com/Calendars.ReadWrite" in scopes


def test_scopes_constant_does_not_use_message_all_preset():
    assert "message_all" not in SCOPES
    assert "Mail.ReadWrite" in SCOPES


def test_authenticate_opens_real_authorization_url_via_loopback(monkeypatch, tmp_path):
    """Contrato real com a lib O365 (sem rede): connection.con de verdade,
    só o HTTPServer e o webbrowser.open() são mockados. Callback de erro
    prova que request_token() roda de ponta a ponta sem travar nem estourar."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))

    fake_server = MagicMock()
    fake_server.server_port = 54321
    opened_urls = []

    def _fake_open(url):
        opened_urls.append(url)
        state = parse_qs(urlparse(url).query)["state"][0]
        fake_server.callback_url = (
            f"http://localhost:54321/?error=access_denied&error_description=denied&state={state}"
        )

    with (
        patch("scriba.auth.HTTPServer", return_value=fake_server),
        patch("scriba.auth.webbrowser.open", side_effect=_fake_open) as mock_open,
        patch("scriba.auth._capture_callback_url", side_effect=lambda server: server.callback_url),
    ):
        result = auth.authenticate("dummy-client-id", "common")

    assert result is False
    mock_open.assert_called_once()
    opened_url = opened_urls[0]
    assert opened_url.startswith("https://login.microsoftonline.com/")
    assert "localhost%3A54321" in opened_url or "localhost:54321" in opened_url


def test_authenticate_returns_false_on_state_mismatch_without_traceback(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))

    fake_server = MagicMock()
    fake_server.server_port = 54321
    fake_server.callback_url = (
        "http://localhost:54321/?error=access_denied"
        "&error_description=denied&state=state-que-nao-bate"
    )

    with (
        patch("scriba.auth.HTTPServer", return_value=fake_server),
        patch("scriba.auth.webbrowser.open"),
        patch("scriba.auth._capture_callback_url", side_effect=lambda server: server.callback_url),
        patch("scriba.auth.print_error") as mock_print_error,
    ):
        result = auth.authenticate("dummy-client-id", "common")

    assert result is False
    mock_print_error.assert_called_once_with("Autenticação falhou.")


def test_authenticate_returns_false_and_pt_br_error_on_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))

    with (
        patch("scriba.auth.webbrowser.open"),
        patch("scriba.auth.CALLBACK_TIMEOUT_SECONDS", 0.05),
        patch("scriba.auth.print_error") as mock_print_error,
    ):
        result = auth.authenticate("dummy-client-id", "common")

    assert result is False
    mock_print_error.assert_called_once()
    message = mock_print_error.call_args.args[0]
    assert "5 minutos" in message
    assert "Timeout" not in message and "timeout" not in message.lower()


def test_token_file_gets_restrictive_permission_after_save(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))

    from scriba.auth import _token_backend

    backend = _token_backend()
    backend._cache = {"fake": "token-cache-state"}
    backend._has_state_changed = True

    saved = backend.save_token(force=True)

    assert saved is True
    token_path = tmp_path / "token"
    assert token_path.exists()
    mode = token_path.stat().st_mode & 0o777
    assert mode == 0o600


def test_token_file_permission_is_reapplied_on_second_save_simulating_refresh(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))

    from scriba.auth import _token_backend

    backend = _token_backend()
    backend._cache = {"fake": "token-cache-state-v1"}
    backend._has_state_changed = True
    backend.save_token(force=True)

    token_path = tmp_path / "token"
    token_path.chmod(0o644)  # simula umask frouxa entre as duas escritas
    assert (token_path.stat().st_mode & 0o777) == 0o644

    backend._cache = {"fake": "token-cache-state-v2-refresh"}
    backend._has_state_changed = True
    backend.save_token(force=True)

    assert (token_path.stat().st_mode & 0o777) == 0o600


def test_token_file_permission_applies_even_with_preexisting_loose_directory(monkeypatch, tmp_path):
    """Critério 3 da spec: a correção não depende do mkdir ter criado o
    diretório com a permissão certa — o diretório de estado pode já
    existir de uma instalação anterior a esta correção, com permissão
    frouxa, e o chmod do arquivo tem de valer do mesmo jeito."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    tmp_path.chmod(0o755)  # diretório pré-existente, frouxo

    from scriba.auth import _token_backend

    backend = _token_backend()
    backend._cache = {"fake": "token-cache-state"}
    backend._has_state_changed = True
    backend.save_token(force=True)

    token_path = tmp_path / "token"
    assert (token_path.stat().st_mode & 0o777) == 0o600


def test_cryptography_manager_attribute_is_still_inherited_and_settable(monkeypatch, tmp_path):
    """A Fase 2 (jd-task #1077, ciclo 5) atribui um adaptador a este
    atributo, herdado de BaseTokenBackend, sem redesenhar esta subclasse
    — este teste trava que a subclasse não sobrescreve nem remove o
    atributo. `SCRIBA_HOME` isolado em tmp_path (achado dev-10: sem
    isso, `_token_backend()` cria/toca o diretório de estado real da
    máquina de quem roda a suíte)."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.auth import _token_backend

    backend = _token_backend()
    assert backend.cryptography_manager is None

    sentinel = object()
    backend.cryptography_manager = sentinel
    assert backend.cryptography_manager is sentinel


def test_is_authenticated_returns_false_when_tenant_is_common(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.config import save_config

    save_config({"client_id": "abc123", "tenant_id": "common"})

    from scriba.auth import is_authenticated

    assert is_authenticated() is False


def test_is_authenticated_returns_false_when_tenant_is_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.config import save_config

    save_config({"client_id": "abc123"})

    from scriba.auth import is_authenticated

    assert is_authenticated() is False


def test_get_account_exits_with_error_when_tenant_is_common(monkeypatch, tmp_path):
    import typer

    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.config import save_config

    save_config({"client_id": "abc123", "tenant_id": "common"})

    from scriba.auth import get_account

    try:
        get_account()
        raise AssertionError("esperava typer.Exit")
    except typer.Exit as exc:
        assert exc.exit_code == 1


def test_token_backend_gets_cryptography_manager_assigned_on_supported_platform(
    monkeypatch, tmp_path
):
    """Sobrescreve a fixture autouse da Task 4 (que neutraliza o
    adaptador por padrão) para provar que, quando o de verdade roda, a
    atribuição acontece — sem redesenhar a subclasse da Fase 1."""
    from unittest.mock import patch

    from scriba.token_crypto import criar_adaptador_criptografia

    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("scriba.auth.criar_adaptador_criptografia", criar_adaptador_criptografia)

    with patch("scriba.token_crypto._criar_keychain"):
        from scriba.auth import _token_backend

        backend = _token_backend()

    from scriba.token_crypto import AdaptadorMacOSKeychain

    assert isinstance(backend.cryptography_manager, AdaptadorMacOSKeychain)


def test_token_backend_keeps_cryptography_manager_none_by_default_in_other_tests(
    monkeypatch, tmp_path
):
    """Confirma que a fixture autouse da Task 4 protege por padrão —
    sem sobrescrever nada, cryptography_manager continua None mesmo
    numa plataforma suportada (comportamento idêntico à Fase 1 para
    todo teste que não pede o adaptador real)."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    monkeypatch.setattr("sys.platform", "darwin")

    from scriba.auth import _token_backend

    backend = _token_backend()

    assert backend.cryptography_manager is None
