from unittest.mock import patch

from typer.testing import CliRunner

from scriba.main import app

runner = CliRunner()


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_login_with_client_id_saves_config_and_authenticates(mock_load, mock_save, mock_auth):
    result = runner.invoke(app, ["auth", "login", "--client-id", "abc123"])

    assert result.exit_code == 0
    mock_save.assert_called_once_with({"client_id": "abc123", "tenant_id": "common"})
    mock_auth.assert_called_once_with("abc123", "common")


@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_login_without_client_id_and_no_config_fails(mock_load):
    result = runner.invoke(app, ["auth", "login"])

    assert result.exit_code == 1


@patch("scriba.commands.auth_cmd.authenticate", return_value=True)
@patch("scriba.commands.auth_cmd.save_config")
@patch("scriba.commands.auth_cmd.load_config", return_value={})
def test_login_with_env_var_saves_config_and_authenticates(mock_load, mock_save, mock_auth, monkeypatch):
    monkeypatch.setenv("SCRIBA_CLIENT_ID", "envclient")
    monkeypatch.delenv("SCRIBA_TENANT_ID", raising=False)

    result = runner.invoke(app, ["auth", "login"])

    assert result.exit_code == 0
    mock_save.assert_called_once_with({"client_id": "envclient", "tenant_id": "common"})
    mock_auth.assert_called_once_with("envclient", "common")


@patch("scriba.commands.auth_cmd.console")
@patch("scriba.commands.auth_cmd.is_authenticated", return_value=True)
@patch("scriba.commands.auth_cmd.load_config", return_value={"client_id": "abc", "tenant_id": "common"})
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
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    token_file = tmp_path / "token.token"
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
