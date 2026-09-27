from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from scriba.main import app

runner = CliRunner()


@patch("scriba.commands.cal_cmd.get_account")
@patch("scriba.commands.cal_cmd.print_event_table")
def test_list_shows_events_in_default_range(mock_print_table, mock_get_account, mock_account, mock_event):
    schedule = MagicMock()
    calendar = MagicMock()
    calendar.get_events.return_value = [mock_event]
    calendar.new_query.return_value = MagicMock()
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "list"])

    assert result.exit_code == 0
    mock_print_table.assert_called_once_with([mock_event])


@patch("scriba.commands.cal_cmd.get_account")
def test_list_with_custom_range(mock_get_account, mock_account, mock_event):
    schedule = MagicMock()
    calendar = MagicMock()
    calendar.get_events.return_value = [mock_event]
    calendar.new_query.return_value = MagicMock()
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "list", "--start", "2026-10-01", "--end", "2026-10-31"])

    assert result.exit_code == 0


@patch("scriba.commands.cal_cmd.get_account")
@patch("scriba.commands.cal_cmd.console")
def test_list_with_no_events_reports_empty(mock_console, mock_get_account, mock_account):
    schedule = MagicMock()
    calendar = MagicMock()
    calendar.get_events.return_value = []
    calendar.new_query.return_value = MagicMock()
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "list"])

    assert result.exit_code == 0
    mock_console.print.assert_called_once_with("Nenhum evento encontrado no intervalo.")


@patch("scriba.commands.cal_cmd.get_account")
@patch("scriba.commands.cal_cmd.print_event_detail")
def test_read_shows_event_detail(mock_print_detail, mock_get_account, mock_account, mock_event):
    schedule = MagicMock()
    calendar = MagicMock()
    calendar.get_event.return_value = mock_event
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "read", "event-id-456"])

    assert result.exit_code == 0
    mock_print_detail.assert_called_once_with(mock_event)


@patch("scriba.commands.cal_cmd.get_account")
def test_read_with_unknown_id_fails(mock_get_account, mock_account):
    schedule = MagicMock()
    calendar = MagicMock()
    calendar.get_event.return_value = None
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "read", "id-inexistente"])

    assert result.exit_code == 1
