from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from scriba.main import app

runner = CliRunner()


@patch("scriba.commands.mail_cmd.get_account")
def test_draft_creates_message_and_saves_without_sending(mock_get_account, mock_account):
    new_message = MagicMock()
    new_message.save_draft.return_value = True
    mock_account.new_message.return_value = new_message
    mock_get_account.return_value = mock_account

    result = runner.invoke(
        app,
        ["mail", "draft", "--to", "bob@example.com", "--subject", "Oi", "--body", "Tudo bem?"],
    )

    assert result.exit_code == 0
    new_message.to.add.assert_called_once_with("bob@example.com")
    assert new_message.subject == "Oi"
    assert new_message.body == "Tudo bem?"
    new_message.save_draft.assert_called_once()
    new_message.send.assert_not_called()


@patch("scriba.commands.mail_cmd.get_account")
def test_draft_reports_failure_when_save_draft_returns_false(mock_get_account, mock_account):
    new_message = MagicMock()
    new_message.save_draft.return_value = False
    mock_account.new_message.return_value = new_message
    mock_get_account.return_value = mock_account

    result = runner.invoke(
        app,
        ["mail", "draft", "--to", "bob@example.com", "--subject", "Oi", "--body", "Tudo bem?"],
    )

    assert result.exit_code == 1
