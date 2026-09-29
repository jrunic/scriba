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
        ["mail", "draft", "--to", "bob@example.com", "--subject", "Oi"],
        input="Tudo bem?",
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
        ["mail", "draft", "--to", "bob@example.com", "--subject", "Oi"],
        input="Tudo bem?",
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
def test_search_combines_unread_and_sender_filters(
    mock_print_table, mock_get_account, mock_account, mock_message
):
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
    query.equals.assert_any_call("isRead", False)
    query.contains.assert_any_call("from", "alice@example.com")


def test_build_search_query_renders_correct_odata_filter_with_real_o365_objects(
    monkeypatch, tmp_path
):
    """Regressão do achado de campo (VM Windows, 27/09/2026): a suíte
    mockada nunca teria pego a API errada (on_attribute/chain não existem)
    nem o atributo "from" que precisa ficar sem o path composto — só um
    objeto real da lib, sem mock, prova a string OData renderizada."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.auth import _build_account
    from scriba.commands.mail_cmd import _build_search_query

    account = _build_account(client_id="dummy-client-id", tenant_id="common")
    mailbox = account.mailbox()

    query = _build_search_query(mailbox, unread=True, sender="alice@example.com")
    rendered = query.as_params()["$filter"]

    assert (
        rendered == "isRead eq false and contains(from/emailAddress/address, 'alice@example.com')"
    )


def test_build_search_query_returns_none_without_filters(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.auth import _build_account
    from scriba.commands.mail_cmd import _build_search_query

    account = _build_account(client_id="dummy-client-id", tenant_id="common")
    mailbox = account.mailbox()

    assert _build_search_query(mailbox, unread=False, sender=None) is None


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


@patch("scriba.commands.mail_cmd.get_account")
def test_reply_creates_draft_addressed_to_sender_only_by_default(
    mock_get_account, mock_account, mock_message
):
    draft = MagicMock()
    draft.save_draft.return_value = True
    mock_message.reply.return_value = draft
    mailbox = MagicMock()
    mailbox.get_message.return_value = mock_message
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "reply", "msg-id-123"], input="Recebido, obrigado.")

    assert result.exit_code == 0
    mock_message.reply.assert_called_once_with(to_all=False)
    assert draft.body == "Recebido, obrigado."
    draft.save_draft.assert_called_once()
    draft.send.assert_not_called()


@patch("scriba.commands.mail_cmd.get_account")
def test_reply_with_reply_all_addresses_every_original_recipient(
    mock_get_account, mock_account, mock_message
):
    draft = MagicMock()
    draft.save_draft.return_value = True
    mock_message.reply.return_value = draft
    mailbox = MagicMock()
    mailbox.get_message.return_value = mock_message
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(
        app,
        ["mail", "reply", "msg-id-123", "--reply-all"],
        input="Recebido, obrigado a todos.",
    )

    assert result.exit_code == 0
    mock_message.reply.assert_called_once_with(to_all=True)


@patch("scriba.commands.mail_cmd.get_account")
def test_reply_reports_failure_when_save_draft_returns_false(
    mock_get_account, mock_account, mock_message
):
    draft = MagicMock()
    draft.save_draft.return_value = False
    mock_message.reply.return_value = draft
    mailbox = MagicMock()
    mailbox.get_message.return_value = mock_message
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "reply", "msg-id-123"], input="Oi")

    assert result.exit_code == 1


@patch("scriba.commands.mail_cmd.get_account")
def test_reply_with_unknown_id_fails(mock_get_account, mock_account):
    mailbox = MagicMock()
    mailbox.get_message.return_value = None
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "reply", "id-inexistente"], input="Oi")

    assert result.exit_code == 1
    assert "Erro" in result.output


@patch("scriba.commands.mail_cmd.get_account")
def test_reply_to_a_draft_message_fails_with_readable_error(
    mock_get_account, mock_account, mock_message
):
    mock_message.reply.side_effect = RuntimeError("Can't reply to this message")
    mailbox = MagicMock()
    mailbox.get_message.return_value = mock_message
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "reply", "msg-id-123"], input="Oi")

    assert result.exit_code == 1
    assert "Erro" in result.output


@patch("scriba.commands.mail_cmd.get_account")
def test_reply_reports_failure_when_reply_call_returns_none(
    mock_get_account, mock_account, mock_message
):
    mock_message.reply.return_value = None
    mailbox = MagicMock()
    mailbox.get_message.return_value = mock_message
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["mail", "reply", "msg-id-123"], input="Oi")

    assert result.exit_code == 1
    assert "Erro" in result.output


def test_message_reply_signature_still_has_to_all_true_by_default():
    """Documenta a armadilha achada na revisão dev-10 (27/09/2026): o
    default da lib é o oposto do que a CLI expõe (to_all=False). Se essa
    assinatura mudar (nome do parâmetro ou default), este teste quebra
    antes de virar um reply-all silencioso em produção."""
    import inspect

    from O365.message import Message

    sig = inspect.signature(Message.reply)

    assert "to_all" in sig.parameters
    assert sig.parameters["to_all"].default is True


def test_build_search_query_renders_subject_filter(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.auth import _build_account
    from scriba.commands.mail_cmd import _build_search_query

    account = _build_account(client_id="dummy-client-id", tenant_id="common")
    mailbox = account.mailbox()

    query = _build_search_query(mailbox, unread=False, sender=None, subject="fatura")
    rendered = query.as_params()["$filter"]

    assert rendered == "contains(subject, 'fatura')"


def test_build_search_query_renders_has_attachments_filter(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.auth import _build_account
    from scriba.commands.mail_cmd import _build_search_query

    account = _build_account(client_id="dummy-client-id", tenant_id="common")
    mailbox = account.mailbox()

    query = _build_search_query(mailbox, unread=False, sender=None, has_attachments=True)
    rendered = query.as_params()["$filter"]

    assert rendered == "hasAttachments eq true"


def test_build_search_query_renders_importance_filter(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from scriba.auth import _build_account
    from scriba.commands.mail_cmd import _build_search_query

    account = _build_account(client_id="dummy-client-id", tenant_id="common")
    mailbox = account.mailbox()

    query = _build_search_query(mailbox, unread=False, sender=None, importance="high")
    rendered = query.as_params()["$filter"]

    assert rendered == "importance eq 'high'"


@patch("scriba.commands.mail_cmd.get_account")
@patch("scriba.commands.mail_cmd._build_search_query")
def test_search_command_passes_new_flags_to_build_search_query(
    mock_build_query, mock_get_account, mock_account
):
    mock_build_query.return_value = None
    mailbox = MagicMock()
    inbox = MagicMock()
    inbox.get_messages.return_value = []
    mailbox.inbox_folder.return_value = inbox
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    runner.invoke(
        app,
        [
            "mail",
            "search",
            "--subject",
            "fatura",
            "--has-attachments",
            "--importance",
            "high",
        ],
    )

    _, kwargs = mock_build_query.call_args
    assert kwargs["subject"] == "fatura"
    assert kwargs["has_attachments"] is True
    assert kwargs["importance"] == "high"


def test_build_search_query_renders_start_date_filter_with_received_date_time(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from datetime import datetime

    from scriba.auth import _build_account
    from scriba.commands.mail_cmd import _build_search_query

    account = _build_account(client_id="dummy-client-id", tenant_id="common")
    mailbox = account.mailbox()

    query = _build_search_query(mailbox, unread=False, sender=None, start_date=datetime(2026, 9, 1))  # noqa: DTZ001 — fuso local, spec assumption 8
    rendered = query.as_params()["$filter"]

    assert rendered.startswith("receivedDateTime ge ")


@patch("scriba.commands.mail_cmd.get_account")
@patch("scriba.commands.mail_cmd._build_search_query")
def test_search_end_date_is_inclusive_of_the_whole_day(
    mock_build_query, mock_get_account, mock_account
):
    mock_build_query.return_value = None
    mailbox = MagicMock()
    inbox = MagicMock()
    inbox.get_messages.return_value = []
    mailbox.inbox_folder.return_value = inbox
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    runner.invoke(app, ["mail", "search", "--end-date", "2026-09-30"])

    _, kwargs = mock_build_query.call_args
    assert kwargs["end_date"].strftime("%Y-%m-%d") == "2026-10-01"


def test_start_end_attribute_shortcuts_map_to_event_path_not_message():
    """Trava contra a armadilha achada na revisão dev-10 (27/09/2026):
    'start'/'end' NÃO são atalhos genéricos — o _attribute_mapping da lib
    os expande pra 'start/DateTime'/'end/DateTime' (caminho de EVENTO,
    query.py:470). Se scriba algum dia usar esses nomes num filtro de
    mensagem, a query fica silenciosamente errada — este teste prova
    contra objeto real da lib que o atalho existe e aponta pro lugar
    errado, então mail search precisa evitá-lo (usa receivedDateTime)."""
    from O365.utils.query import QueryBuilder

    assert QueryBuilder._attribute_mapping["start"] == "start/DateTime"
    assert QueryBuilder._attribute_mapping["end"] == "end/DateTime"
    assert "receivedDateTime" not in QueryBuilder._attribute_mapping


def test_build_search_query_combines_three_filters_including_date(monkeypatch, tmp_path):
    """Critério 9 da spec: pina a string OData exata na parte sem data —
    a parte com data verifica só por conteúdo (achado de revisão dev-10:
    _parse_filter_word localiza o datetime no fuso do protocolo, então a
    string completa com offset é frágil entre máquinas)."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    from datetime import datetime

    from scriba.auth import _build_account
    from scriba.commands.mail_cmd import _build_search_query

    account = _build_account(client_id="dummy-client-id", tenant_id="common")
    mailbox = account.mailbox()

    query = _build_search_query(
        mailbox,
        unread=True,
        sender=None,
        has_attachments=True,
        start_date=datetime(2026, 9, 1),  # noqa: DTZ001 — fuso local, spec assumption 8
    )
    rendered = query.as_params()["$filter"]

    assert rendered.startswith(
        "isRead eq false and hasAttachments eq true and receivedDateTime ge "
    )


def test_read_body_from_file(tmp_path):
    from scriba.commands.mail_cmd import _read_body

    body_file = tmp_path / "corpo.txt"
    body_file.write_text("Corpo lido do arquivo.")

    assert _read_body(body_file) == "Corpo lido do arquivo."


def test_read_body_from_stdin_when_no_file(monkeypatch):
    import io

    from scriba.commands.mail_cmd import _read_body

    monkeypatch.setattr("sys.stdin", io.StringIO("Corpo via stdin."))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)

    assert _read_body(None) == "Corpo via stdin."


def test_read_body_empty_stdin_is_empty_string_not_error(monkeypatch):
    import io

    from scriba.commands.mail_cmd import _read_body

    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)

    assert _read_body(None) == ""


def test_read_body_fails_clearly_when_stdin_is_a_terminal_and_no_file(monkeypatch):
    import typer

    from scriba.commands.mail_cmd import _read_body

    monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)

    try:
        _read_body(None)
        raise AssertionError("esperava typer.Exit")
    except typer.Exit as exc:
        assert exc.exit_code == 1


@patch("scriba.commands.mail_cmd.get_account")
def test_draft_reads_body_from_file_option(mock_get_account, mock_account, tmp_path):
    new_message = MagicMock()
    new_message.save_draft.return_value = True
    mock_account.new_message.return_value = new_message
    mock_get_account.return_value = mock_account

    body_file = tmp_path / "corpo.txt"
    body_file.write_text("Tudo bem?")

    result = runner.invoke(
        app,
        [
            "mail",
            "draft",
            "--to",
            "bob@example.com",
            "--subject",
            "Oi",
            "--body-file",
            str(body_file),
        ],
    )

    assert result.exit_code == 0
    assert new_message.body == "Tudo bem?"


@patch("scriba.commands.mail_cmd.get_account")
def test_draft_reads_body_from_stdin_when_no_body_file(mock_get_account, mock_account):
    new_message = MagicMock()
    new_message.save_draft.return_value = True
    mock_account.new_message.return_value = new_message
    mock_get_account.return_value = mock_account

    result = runner.invoke(
        app,
        ["mail", "draft", "--to", "bob@example.com", "--subject", "Oi"],
        input="Corpo via stdin.\n",
    )

    assert result.exit_code == 0
    assert new_message.body == "Corpo via stdin.\n"


def test_draft_no_longer_accepts_body_option(monkeypatch, tmp_path):
    """Achado dev-10: sem isolar SCRIBA_HOME nem mockar get_account, na
    fase RED (--body ainda aceito) este teste roda o comando inteiro
    contra config/token REAIS de quem executa a suíte — se a máquina
    estiver autenticada, cria um rascunho de verdade no Outlook. O
    isolamento abaixo neutraliza isso independente da fase (RED ou
    GREEN): sem client_id configurado, get_account() sai antes de
    tocar rede, e a asserção (exit_code != 0) passa pelo motivo certo
    em ambas as fases — click rejeitando --body desconhecido no GREEN,
    "não configurado" no RED."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    result = runner.invoke(
        app,
        [
            "mail",
            "draft",
            "--to",
            "bob@example.com",
            "--subject",
            "Oi",
            "--body",
            "não deveria existir",
        ],
    )

    assert result.exit_code != 0


@patch("scriba.commands.mail_cmd.get_account")
def test_reply_reads_body_from_file_option(mock_get_account, mock_account, mock_message, tmp_path):
    draft = MagicMock()
    draft.save_draft.return_value = True
    mock_message.reply.return_value = draft
    mailbox = MagicMock()
    mailbox.get_message.return_value = mock_message
    mock_account.mailbox.return_value = mailbox
    mock_get_account.return_value = mock_account

    body_file = tmp_path / "corpo.txt"
    body_file.write_text("Recebido, obrigado.")

    result = runner.invoke(app, ["mail", "reply", "msg-id-123", "--body-file", str(body_file)])

    assert result.exit_code == 0
    assert draft.body == "Recebido, obrigado."


def test_reply_no_longer_accepts_body_option(monkeypatch, tmp_path):
    """Mesmo isolamento e mesmo motivo do teste equivalente de draft
    acima (achado dev-10)."""
    monkeypatch.setenv("SCRIBA_HOME", str(tmp_path))
    result = runner.invoke(app, ["mail", "reply", "msg-id-123", "--body", "não deveria existir"])

    assert result.exit_code != 0
