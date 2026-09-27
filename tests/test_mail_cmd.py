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


@patch("scriba.commands.mail_cmd.get_account")
@patch("scriba.commands.mail_cmd.print_mail_table")
def test_search_lists_unread_only(mock_print_table, mock_get_account, mock_account, mock_message):
    mailbox = MagicMock()
    inbox = MagicMock()
    inbox.get_messages.return_value = [mock_message]
    mailbox.inbox_folder.return_value = inbox
    mailbox.new_query.return_value = MagicMock()
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "search", "--unread"])

    assert result.exit_code == 0
    mock_print_table.assert_called_once_with([mock_message])


@patch("scriba.commands.mail_cmd.get_account")
@patch("scriba.commands.mail_cmd.print_mail_table")
def test_search_combines_unread_and_sender_filters(mock_print_table, mock_get_account, mock_account, mock_message):
    mailbox = MagicMock()
    inbox = MagicMock()
    inbox.get_messages.return_value = [mock_message]
    mailbox.inbox_folder.return_value = inbox
    query = MagicMock()
    mailbox.new_query.return_value = query
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "search", "--unread", "--from", "alice@example.com"])

    assert result.exit_code == 0
    query.on_attribute.assert_any_call("isRead")
    query.chain.assert_any_call("and")


@patch("scriba.commands.mail_cmd.get_account")
@patch("scriba.commands.mail_cmd.console")
def test_search_with_no_messages_reports_empty(mock_console, mock_get_account, mock_account):
    mailbox = MagicMock()
    inbox = MagicMock()
    inbox.get_messages.return_value = []
    mailbox.inbox_folder.return_value = inbox
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "search"])

    assert result.exit_code == 0
    mock_console.print.assert_called_once_with("Nenhuma mensagem encontrada.")


@patch("scriba.commands.mail_cmd.get_account")
@patch("scriba.commands.mail_cmd.print_mail_detail")
def test_read_shows_message_body(mock_print_detail, mock_get_account, mock_account, mock_message):
    mailbox = MagicMock()
    mailbox.get_message.return_value = mock_message
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "read", "msg-id-123"])

    assert result.exit_code == 0
    mock_print_detail.assert_called_once_with(mock_message)


@patch("scriba.commands.mail_cmd.get_account")
def test_read_with_unknown_id_fails(mock_get_account, mock_account):
    mailbox = MagicMock()
    mailbox.get_message.return_value = None
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "read", "id-inexistente"])

    assert result.exit_code == 1
