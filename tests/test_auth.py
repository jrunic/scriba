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
