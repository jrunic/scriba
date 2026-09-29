from unittest.mock import patch

from typer.testing import CliRunner

from scriba.main import app

runner = CliRunner()


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_login_with_client_id_and_tenant_saves_config_and_authenticates(
    mock_load, mock_save, mock_auth
):
    result = runner.invoke(
        app, ["auth", "login", "--client-id", "abc123", "--tenant-id", "tenant-real-do-cliente"]
    )

    assert result.exit_code == 0
    mock_save.assert_called_once_with(
        {"client_id": "abc123", "tenant_id": "tenant-real-do-cliente"}
    )
    mock_auth.assert_called_once_with("abc123", "tenant-real-do-cliente")


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_login_without_client_id_and_no_config_fails(mock_load, mock_save, mock_auth, monkeypatch):
    monkeypatch.delenv("SCRIBA_CLIENT_ID", raising=False)
    monkeypatch.delenv("SCRIBA_TENANT_ID", raising=False)
    result = runner.invoke(app, ["auth", "login", "--tenant-id", "tenant-real"])

    assert result.exit_code == 1
    mock_auth.assert_not_called()


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_login_without_tenant_and_no_config_fails(mock_load, mock_save, mock_auth, monkeypatch):
    monkeypatch.delenv("SCRIBA_TENANT_ID", raising=False)
    result = runner.invoke(app, ["auth", "login", "--client-id", "abc123"])

    assert result.exit_code == 1
    mock_auth.assert_not_called()


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_login_rejects_common_as_explicit_tenant(mock_load, mock_save, mock_auth, monkeypatch):
    monkeypatch.delenv("SCRIBA_TENANT_ID", raising=False)
    result = runner.invoke(app, ["auth", "login", "--client-id", "abc123", "--tenant-id", "common"])

    assert result.exit_code == 1
    mock_auth.assert_not_called()


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch(
    "scriba.commands.auth_cmd.load_config",
    return_value={"client_id": "abc", "tenant_id": "common"},
)
def test_login_rejects_common_already_saved_in_config_without_new_option(
    mock_load, mock_save, mock_auth, monkeypatch
):
    monkeypatch.delenv("SCRIBA_TENANT_ID", raising=False)
    result = runner.invoke(app, ["auth", "login"])

    assert result.exit_code == 1
    mock_auth.assert_not_called()


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_login_with_env_var_tenant_saves_config_and_authenticates(
    mock_load, mock_save, mock_auth, monkeypatch
):
    monkeypatch.setenv("SCRIBA_CLIENT_ID", "envclient")
    monkeypatch.setenv("SCRIBA_TENANT_ID", "tenant-do-env")

    result = runner.invoke(app, ["auth", "login"])

    assert result.exit_code == 0
    mock_save.assert_called_once_with({"client_id": "envclient", "tenant_id": "tenant-do-env"})
    mock_auth.assert_called_once_with("envclient", "tenant-do-env")


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch(
    "scriba.commands.auth_cmd.load_config",
    return_value={"client_id": "abc", "tenant_id": "tenant-antigo-salvo"},
)
def test_login_explicit_tenant_option_wins_over_saved_config(mock_load, mock_save, mock_auth):
    """Precedência corrigida na revisão dev-10: o código atual faz
    `tenant_id = config.get("tenant_id", tenant_id)` — o valor SALVO
    sobrescreve silenciosamente a opção explícita. A correção inverte
    isso: a opção explícita vence."""
    result = runner.invoke(app, ["auth", "login", "--tenant-id", "tenant-novo-explicito"])

    assert result.exit_code == 0
    mock_auth.assert_called_once_with("abc", "tenant-novo-explicito")


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch(
    "scriba.commands.auth_cmd.load_config",
    return_value={"client_id": "abc", "tenant_id": "tenant-valido-salvo"},
)
def test_login_uses_saved_valid_tenant_when_no_option_given(mock_load, mock_save, mock_auth):
    """Quarto caso do critério 4 da spec (achado dev-10: faltava no
    plano) — configuração salva com tenant VÁLIDO, sem opção nova,
    autentica normalmente com o valor salvo."""
    result = runner.invoke(app, ["auth", "login"])

    assert result.exit_code == 0
    mock_auth.assert_called_once_with("abc", "tenant-valido-salvo")


@patch("scriba.commands.auth_cmd.console")
@patch("scriba.commands.auth_cmd.is_authenticated", return_value=True)
@patch(
    "scriba.commands.auth_cmd.load_config", return_value={"client_id": "abc", "tenant_id": "common"}
)
def test_status_reports_authenticated(mock_load, mock_is_auth, mock_console):
    result = runner.invoke(app, ["auth", "status"])

    assert result.exit_code == 0
    printed = " ".join(str(call.args[0]) for call in mock_console.print.call_args_list)
    assert "abc" in printed


@patch("scriba.commands.auth_cmd.print_error")
@patch("scriba.commands.auth_cmd.is_authenticated", return_value=False)
@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_status_reports_not_authenticated(mock_load, mock_is_auth, mock_print_error):
    result = runner.invoke(app, ["auth", "status"])

    assert result.exit_code == 1
    mock_print_error.assert_called_once()


def test_logout_removes_token_file(tmp_path, monkeypatch):
    """Achado de campo (VM Windows, 27/09/2026): o FileSystemTokenBackend
    real grava o arquivo como "token" — sem sufixo ".token". O código e
    este teste assumiam "token.token"; os dois estavam errados do mesmo
    jeito, então o teste nunca teria pego o bug (confirmado por dir real
    no state dir da VM)."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    token_file = tmp_path / "token"
    token_file.write_text("fake-token")

    result = runner.invoke(app, ["auth", "logout"])

    assert result.exit_code == 0
    assert not token_file.exists()


@patch("scriba.commands.auth_cmd.console")
def test_logout_without_token_reports_already_logged_out(mock_console, tmp_path, monkeypatch):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))

    result = runner.invoke(app, ["auth", "logout"])

    assert result.exit_code == 0
    mock_console.print.assert_called_once()


def test_logout_warns_that_entra_session_is_not_revoked(tmp_path, monkeypatch):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    token_file = tmp_path / "token"
    token_file.write_text("fake-token")

    result = runner.invoke(app, ["auth", "logout"])

    assert result.exit_code == 0
    output_lower = result.output.lower()
    assert "revog" in output_lower
    assert "entra" in output_lower


def test_status_reports_distinct_message_when_vault_is_unavailable(monkeypatch):
    """Achado dev-10: sem tratamento em status(), CofreIndisponivelError
    propagada por is_authenticated() vira traceback cru — o critério 4
    exige mensagem própria 'em qualquer um dos pontos de entrada'."""
    from scriba.token_crypto import CofreIndisponivelError

    with patch(
        "scriba.commands.auth_cmd.is_authenticated",
        side_effect=CofreIndisponivelError("cofre bloqueado"),
    ):
        result = runner.invoke(app, ["auth", "status"])

    assert result.exit_code == 1
    assert "cofre" in result.output.lower()
    assert "traceback" not in result.output.lower()
