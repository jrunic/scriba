import sys
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from scriba import auth
from scriba.auth import SCOPES, _get_graph_scopes

_SEM_CHMOD_POSIX = pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "chmod() não implementa permissão POSIX no Windows — o sistema usa "
        "ACL, e stat() sempre reporta 0o666 num arquivo normal. Medido em "
        "campo na bancada Windows (koine-restrito) em 29/09/2026, rodando a "
        "suíte de verdade pela primeira vez num Windows real. Não é bug do "
        "produto: já documentado como limite conhecido desde a Fase 1 — "
        "Windows é protegido por cifra do conteúdo (DPAPI, Fase 2), não por "
        "permissão de arquivo."
    ),
)


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


@_SEM_CHMOD_POSIX
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


@_SEM_CHMOD_POSIX
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


@_SEM_CHMOD_POSIX
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


def test_get_account_reports_not_authenticated_for_old_format_token_on_windows(
    monkeypatch, tmp_path
):
    """Critério 3, ramo Windows: token em formato antigo (texto puro)
    vira 'não autenticado' via TokenFormatoAntigoError — não
    traceback. sys.platform fixado para exercitar o adaptador Windows
    de verdade (mockado só na fronteira do SO)."""
    import typer

    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    monkeypatch.setattr("sys.platform", "win32")

    from scriba.token_crypto import criar_adaptador_criptografia

    monkeypatch.setattr("scriba.auth.criar_adaptador_criptografia", criar_adaptador_criptografia)

    from unittest.mock import MagicMock, patch

    with patch("scriba.token_crypto._criar_agente_dpapi", return_value=MagicMock()):
        from scriba.config import save_config

        save_config({"client_id": "abc", "tenant_id": "tenant-real"})
        (tmp_path / "token").write_text('{"access_token": "token-em-claro-antigo"}')

        from scriba.auth import get_account

        try:
            get_account()
            raise AssertionError("esperava typer.Exit")
        except typer.Exit as exc:
            assert exc.exit_code == 1


def test_get_account_reports_not_authenticated_for_missing_keychain_item_on_macos(
    monkeypatch, tmp_path
):
    """Critério 3, ramo macOS: item de Keychain ausente (arquivo
    antigo ou primeiro uso) vira 'não autenticado' pelo caminho normal
    — sem exceção propagada, via o discriminante ITEM_NOT_FOUND do
    adaptador macOS."""
    import typer

    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    monkeypatch.setattr("sys.platform", "darwin")

    from scriba.token_crypto import criar_adaptador_criptografia

    monkeypatch.setattr("scriba.auth.criar_adaptador_criptografia", criar_adaptador_criptografia)

    from unittest.mock import MagicMock, patch

    from test_token_crypto import _OSErrorComExitStatus

    keychain_mock = MagicMock()
    keychain_mock.get_generic_password.side_effect = _OSErrorComExitStatus(-25300)

    with patch("scriba.token_crypto._criar_keychain", return_value=keychain_mock):
        from scriba.config import save_config

        save_config({"client_id": "abc", "tenant_id": "tenant-real"})
        (tmp_path / "token").write_text("qualquer-conteudo-marcador-ou-antigo")

        from scriba.auth import get_account

        try:
            get_account()
            raise AssertionError("esperava typer.Exit")
        except typer.Exit as exc:
            assert exc.exit_code == 1


def test_get_account_reports_distinct_error_for_real_vault_failure(monkeypatch, tmp_path):
    """Critério 4. Backend real (passa o isinstance check de
    Connection.__init__), com um adaptador falso cujo decrypt()
    levanta CofreIndisponivelError — exercita o caminho real de
    load_token()/deserialize(), não um mock que nunca é alcançado."""
    import typer

    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.auth import TOKEN_FILENAME, _TokenBackendComPermissaoRestrita
    from scriba.config import get_state_dir, save_config
    from scriba.token_crypto import CofreIndisponivelError

    save_config({"client_id": "abc", "tenant_id": "tenant-real"})
    (tmp_path / "token").write_text("qualquer-conteudo")

    class _AdaptadorQuebrado:
        def encrypt(self, data):
            return data

        def decrypt(self, data):
            raise CofreIndisponivelError("cofre bloqueado")

    def _backend_com_adaptador_quebrado():
        backend = _TokenBackendComPermissaoRestrita(
            token_path=get_state_dir(), token_filename=TOKEN_FILENAME
        )
        backend.cryptography_manager = _AdaptadorQuebrado()
        return backend

    monkeypatch.setattr("scriba.auth._token_backend", _backend_com_adaptador_quebrado)

    from scriba.auth import get_account

    try:
        get_account()
        raise AssertionError("esperava typer.Exit")
    except typer.Exit as exc:
        assert exc.exit_code == 1


def test_is_authenticated_does_not_swallow_real_vault_failure(monkeypatch, tmp_path):
    """Achado dev-10: is_authenticated() tinha except Exception amplo
    que converteria CofreIndisponivelError em False silencioso,
    contradizendo 'falha de proteção não vira sessão desprotegida
    silenciosa'. Mesma técnica de backend real do teste acima."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.auth import TOKEN_FILENAME, _TokenBackendComPermissaoRestrita
    from scriba.config import get_state_dir, save_config
    from scriba.token_crypto import CofreIndisponivelError

    save_config({"client_id": "abc", "tenant_id": "tenant-real"})
    (tmp_path / "token").write_text("qualquer-conteudo")

    class _AdaptadorQuebrado:
        def encrypt(self, data):
            return data

        def decrypt(self, data):
            raise CofreIndisponivelError("cofre bloqueado")

    def _backend_com_adaptador_quebrado():
        backend = _TokenBackendComPermissaoRestrita(
            token_path=get_state_dir(), token_filename=TOKEN_FILENAME
        )
        backend.cryptography_manager = _AdaptadorQuebrado()
        return backend

    monkeypatch.setattr("scriba.auth._token_backend", _backend_com_adaptador_quebrado)

    import pytest

    from scriba.auth import is_authenticated
    from scriba.token_crypto import CofreIndisponivelError as _CIE

    with pytest.raises(_CIE):
        is_authenticated()


def test_token_file_content_is_protected_on_windows_after_save(monkeypatch, tmp_path):
    """Critério 1, Windows. Asserção sobre o argumento que chegou em
    protect() — achado dev-10: sem isso, um encrypt() que descartasse
    o conteúdo passaria pela asserção de "não contém a substring"."""
    from unittest.mock import MagicMock, patch

    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    monkeypatch.setattr("sys.platform", "win32")

    from scriba.token_crypto import criar_adaptador_criptografia

    monkeypatch.setattr("scriba.auth.criar_adaptador_criptografia", criar_adaptador_criptografia)

    agente_mock = MagicMock()
    agente_mock.protect.return_value = b"bytes-cifrados-fake"

    with patch("scriba.token_crypto._criar_agente_dpapi", return_value=agente_mock):
        from scriba.auth import _token_backend

        backend = _token_backend()
        backend._cache = {"access_token": "token-real-de-teste"}
        backend._has_state_changed = True
        backend.save_token(force=True)

    agente_mock.protect.assert_called_once()
    conteudo_enviado_para_cifrar = agente_mock.protect.call_args.args[0]
    assert "token-real-de-teste" in conteudo_enviado_para_cifrar

    token_path = tmp_path / "token"
    conteudo_em_disco = token_path.read_text()
    assert "token-real-de-teste" not in conteudo_em_disco
    assert "access_token" not in conteudo_em_disco


def test_token_file_stays_protected_after_simulated_refresh_windows(monkeypatch, tmp_path):
    from unittest.mock import MagicMock, patch

    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    monkeypatch.setattr("sys.platform", "win32")

    from scriba.token_crypto import criar_adaptador_criptografia

    monkeypatch.setattr("scriba.auth.criar_adaptador_criptografia", criar_adaptador_criptografia)

    agente_mock = MagicMock()
    agente_mock.protect.side_effect = [b"cifrado-v1", b"cifrado-v2-refresh"]

    with patch("scriba.token_crypto._criar_agente_dpapi", return_value=agente_mock):
        from scriba.auth import _token_backend

        backend = _token_backend()
        backend._cache = {"access_token": "v1"}
        backend._has_state_changed = True
        backend.save_token(force=True)

        backend._cache = {"access_token": "v2-apos-refresh"}
        backend._has_state_changed = True
        backend.save_token(force=True)

    assert agente_mock.protect.call_count == 2
    primeiro_conteudo = agente_mock.protect.call_args_list[0].args[0]
    segundo_conteudo = agente_mock.protect.call_args_list[1].args[0]
    assert "v1" in primeiro_conteudo and "v2-apos-refresh" not in primeiro_conteudo
    assert "v2-apos-refresh" in segundo_conteudo

    conteudo_em_disco = (tmp_path / "token").read_text()
    assert "v1" not in conteudo_em_disco
    assert "v2-apos-refresh" not in conteudo_em_disco


def test_keychain_content_is_protected_on_macos_after_save_and_refresh(monkeypatch, tmp_path):
    from unittest.mock import MagicMock, patch

    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    monkeypatch.setattr("sys.platform", "darwin")

    from scriba.token_crypto import criar_adaptador_criptografia

    monkeypatch.setattr("scriba.auth.criar_adaptador_criptografia", criar_adaptador_criptografia)

    keychain_mock = MagicMock()

    with patch("scriba.token_crypto._criar_keychain", return_value=keychain_mock):
        from scriba.auth import _token_backend

        backend = _token_backend()
        backend._cache = {"access_token": "v1"}
        backend._has_state_changed = True
        backend.save_token(force=True)

        backend._cache = {"access_token": "v2-apos-refresh"}
        backend._has_state_changed = True
        backend.save_token(force=True)

    assert keychain_mock.set_generic_password.call_count == 2
    primeiro_valor = keychain_mock.set_generic_password.call_args_list[0].args[2]
    segundo_valor = keychain_mock.set_generic_password.call_args_list[1].args[2]
    assert "v1" in primeiro_valor
    assert "v2-apos-refresh" in segundo_valor

    conteudo_arquivo = (tmp_path / "token").read_text()
    assert "v1" not in conteudo_arquivo
    assert "v2-apos-refresh" not in conteudo_arquivo
    assert "access_token" not in conteudo_arquivo
