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
            f"http://localhost:54321/?error=access_denied"
            f"&error_description=denied&state={state}"
        )

    with patch("scriba.auth.HTTPServer", return_value=fake_server), \
         patch("scriba.auth.webbrowser.open", side_effect=_fake_open) as mock_open, \
         patch("scriba.auth._capture_callback_url", side_effect=lambda server: server.callback_url):
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

    with patch("scriba.auth.HTTPServer", return_value=fake_server), \
         patch("scriba.auth.webbrowser.open"), \
         patch("scriba.auth._capture_callback_url", side_effect=lambda server: server.callback_url), \
         patch("scriba.auth.print_error") as mock_print_error:
        result = auth.authenticate("dummy-client-id", "common")

    assert result is False
    mock_print_error.assert_called_once_with("Autenticação falhou.")
