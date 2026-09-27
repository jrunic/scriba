from unittest.mock import MagicMock, call, patch

from typer.testing import CliRunner

from scriba.main import app

runner = CliRunner()


@patch("scriba.commands.cal_cmd.get_account")
@patch("scriba.commands.cal_cmd.print_event_table")
def test_list_shows_events_in_default_range(mock_print_table, mock_get_account, mock_account, mock_event):
    schedule = MagicMock()
    calendar = MagicMock()
    calendar.get_events.return_value = [mock_event]
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "list"])

    assert result.exit_code == 0
    mock_print_table.assert_called_once_with([mock_event])
    _, kwargs = calendar.get_events.call_args
    assert "start_recurring" in kwargs
    assert "end_recurring" in kwargs


@patch("scriba.commands.cal_cmd.get_account")
def test_list_with_custom_range(mock_get_account, mock_account, mock_event):
    schedule = MagicMock()
    calendar = MagicMock()
    calendar.get_events.return_value = [mock_event]
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "list", "--start", "2026-10-01", "--end", "2026-10-31"])

    assert result.exit_code == 0
    _, kwargs = calendar.get_events.call_args
    assert kwargs["start_recurring"].strftime("%Y-%m-%d") == "2026-10-01"
    assert kwargs["end_recurring"].strftime("%Y-%m-%d") == "2026-10-31"


@patch("scriba.commands.cal_cmd.get_account")
@patch("scriba.commands.cal_cmd.console")
def test_list_with_no_events_reports_empty(mock_console, mock_get_account, mock_account):
    schedule = MagicMock()
    calendar = MagicMock()
    calendar.get_events.return_value = []
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
    calendar.get_event.assert_called_once_with("event-id-456")


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


@patch("scriba.commands.cal_cmd.get_account")
def test_create_saves_event_with_subject_and_times(mock_get_account, mock_account):
    schedule = MagicMock()
    calendar = MagicMock()
    new_event = MagicMock()
    new_event.save.return_value = True
    calendar.new_event.return_value = new_event
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(
        app,
        ["cal", "create", "--subject", "Reunião", "--start", "2026-10-08 12:00", "--end", "2026-10-08 13:00"],
    )

    assert result.exit_code == 0
    assert new_event.subject == "Reunião"
    new_event.save.assert_called_once()


@patch("scriba.commands.cal_cmd.get_account")
def test_create_reports_failure_when_save_returns_false(mock_get_account, mock_account):
    schedule = MagicMock()
    calendar = MagicMock()
    new_event = MagicMock()
    new_event.save.return_value = False
    calendar.new_event.return_value = new_event
    schedule.get_default_calendar.return_value = calendar
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(
        app,
        ["cal", "create", "--subject", "Reunião", "--start", "2026-10-08 12:00", "--end", "2026-10-08 13:00"],
    )

    assert result.exit_code == 1


@patch("scriba.commands.cal_cmd.get_account")
@patch("scriba.commands.cal_cmd.print_calendar_table")
def test_calendars_lists_accounts_calendars(mock_print_table, mock_get_account, mock_account, mock_calendar):
    schedule = MagicMock()
    schedule.list_calendars.return_value = [mock_calendar]
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "calendars"])

    assert result.exit_code == 0
    mock_print_table.assert_called_once_with([mock_calendar])


@patch("scriba.commands.cal_cmd.get_account")
@patch("scriba.commands.cal_cmd.console")
def test_calendars_with_none_reports_empty(mock_console, mock_get_account, mock_account):
    schedule = MagicMock()
    schedule.list_calendars.return_value = []
    mock_account.schedule.return_value = schedule
    mock_get_account.return_value = mock_account

    result = runner.invoke(app, ["cal", "calendars"])

    assert result.exit_code == 0
    mock_console.print.assert_called_once_with("Nenhum calendário encontrado.")


def test_resolve_calendar_tries_calendar_id_first(mock_calendar):
    from scriba.commands.cal_cmd import _resolve_calendar

    schedule = MagicMock()
    schedule.get_calendar.return_value = mock_calendar

    result = _resolve_calendar(schedule, "cal-id-default")

    assert result is mock_calendar
    schedule.get_calendar.assert_called_once_with(calendar_id="cal-id-default")


def test_resolve_calendar_falls_back_to_calendar_name(mock_calendar_secondary):
    from scriba.commands.cal_cmd import _resolve_calendar

    schedule = MagicMock()
    schedule.get_calendar.side_effect = [None, mock_calendar_secondary]

    result = _resolve_calendar(schedule, "Trabalho")

    assert result is mock_calendar_secondary
    assert schedule.get_calendar.call_args_list == [
        call(calendar_id="Trabalho"),
        call(calendar_name="Trabalho"),
    ]


@patch("scriba.commands.cal_cmd.print_error")
def test_resolve_calendar_raises_readable_error_when_nothing_resolves(mock_print_error):
    from scriba.commands.cal_cmd import _resolve_calendar
    import typer

    schedule = MagicMock()
    schedule.get_calendar.return_value = None

    try:
        _resolve_calendar(schedule, "não-existe")
        raised = False
    except typer.Exit as exc:
        raised = True
        assert exc.exit_code == 1

    assert raised
    mock_print_error.assert_called_once_with("Calendário não encontrado: não-existe")


def test_schedule_get_calendar_signature_still_requires_exactly_one_of_id_or_name():
    """Trava contra deriva de API — achado de revisão dev-10 (27/09/2026):
    calendar_id e calendar_name são mutuamente exclusivos, os dois com
    default None (calendar.py:2044). Se a lib renomear um dos dois,
    _resolve_calendar quebra silenciosamente sem este teste."""
    import inspect

    from O365.calendar import Schedule

    sig = inspect.signature(Schedule.get_calendar)

    assert sig.parameters["calendar_id"].default is None
    assert sig.parameters["calendar_name"].default is None
