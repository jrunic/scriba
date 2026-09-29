from io import StringIO

import pytest
from rich.console import Console

from scriba.display import console, print_error, print_success, strip_html


@pytest.fixture
def captured_console(monkeypatch):
    """Injeta uma Console com destino e largura controlados — a Console
    default de display.py resolve sys.stdout de forma que nem sempre é
    capturada de forma confiável por capsys/CliRunner, e tabelas Rich
    truncam célula em terminais estreitos. Ver revisão dev-10 do plano."""
    buffer = StringIO()
    test_console = Console(file=buffer, width=200)
    monkeypatch.setattr("scriba.display.console", test_console)
    return buffer


def test_console_is_rich_console():
    assert isinstance(console, Console)


def test_print_error_writes_to_console(captured_console):
    print_error("deu ruim")
    assert "deu ruim" in captured_console.getvalue()


def test_print_success_writes_to_console(captured_console):
    print_success("beleza")
    assert "beleza" in captured_console.getvalue()


def test_strip_html_converts_br_and_p_to_newlines():
    html = "<p>Oi</p><br>tudo bem?"
    assert strip_html(html) == "Oi\ntudo bem?"


def test_strip_html_unescapes_entities():
    assert strip_html("A&nbsp;B") == "A B"


def test_strip_html_removes_style_block_content():
    html = "<style>body{color:red;font-size:14px}</style><p>Oi</p>"
    assert strip_html(html) == "Oi"


def test_strip_html_removes_script_block_content():
    html = "<script>var x = 1;</script><p>Oi</p>"
    assert strip_html(html) == "Oi"


def test_strip_html_removes_zero_width_space():
    assert strip_html("Oi\u200btudo bem") == "Oitudo bem"


from scriba.display import print_mail_table


def test_print_mail_table_shows_subject_and_sender(mock_message, captured_console):
    print_mail_table([mock_message])
    output = captured_console.getvalue()
    assert "Assunto de teste" in output
    assert "remetente@example.com" in output


from scriba.display import print_mail_detail


def test_print_mail_detail_strips_html_body(mock_message, captured_console):
    mock_message.body = "<p>Oi</p><br>tudo bem?"
    print_mail_detail(mock_message)
    output = captured_console.getvalue()
    assert "<p>" not in output
    assert "tudo bem?" in output


from scriba.display import print_event_table


def test_print_event_table_shows_subject_and_location(mock_event, captured_console):
    print_event_table([mock_event])
    output = captured_console.getvalue()
    assert "Reunião de teste" in output
    assert "Sala 1" in output


from scriba.display import print_event_detail


def test_print_event_detail_shows_location_and_body(mock_event, captured_console):
    print_event_detail(mock_event)
    output = captured_console.getvalue()
    assert "Sala 1" in output
    assert "Pauta da reunião." in output


from scriba.display import _location_name


def test_location_name_extracts_display_name_from_dict():
    """Achado de campo (VM Windows, 27/09/2026): Event.location na lib real
    é um dict estruturado (displayName/locationType/uniqueId/uniqueIdType),
    não uma string — exibir o dict cru mostra o repr inteiro pro usuário."""
    location = {"displayName": "Sala 1", "locationType": "default"}
    assert _location_name(location) == "Sala 1"


def test_location_name_handles_missing_or_empty_location():
    assert _location_name(None) == ""
    assert _location_name({}) == ""
    assert _location_name("Sala 1") == "Sala 1"


def test_print_mail_table_escapes_rich_markup_in_subject(captured_console):
    from unittest.mock import MagicMock

    msg = MagicMock()
    msg.sender = "remetente@example.com"
    msg.subject = "[bold red]FAKE[/]"
    msg.object_id = "id-1"
    print_mail_table([msg])
    output = captured_console.getvalue()
    assert "[bold red]FAKE[/]" in output


def test_print_mail_table_strips_esc_byte_from_sender(captured_console):
    from unittest.mock import MagicMock

    msg = MagicMock()
    msg.sender = "a\x1bevil@example.com"
    msg.subject = "assunto normal"
    msg.object_id = "id-2"
    print_mail_table([msg])
    output = captured_console.getvalue()
    assert "\x1b" not in output


def test_print_mail_detail_escapes_rich_markup_in_subject_and_body(captured_console):
    from unittest.mock import MagicMock

    msg = MagicMock()
    msg.sender = "remetente@example.com"
    msg.subject = "[bold red]FAKE[/]"
    msg.body = "corpo com [italic]markup[/] falso"
    print_mail_detail(msg)
    output = captured_console.getvalue()
    assert "[bold red]FAKE[/]" in output
    assert "[italic]markup[/]" in output


def test_print_mail_detail_strips_esc_byte_from_body(captured_console):
    """Critério 2 da spec nomeia o CORPO como portador do 0x1b — é o
    campo que passa por strip_html antes de _safe, o caminho com mais
    transformação no meio (achado dev-10: o teste da tabela cobre só o
    remetente)."""
    from unittest.mock import MagicMock

    msg = MagicMock()
    msg.sender = "remetente@example.com"
    msg.subject = "assunto normal"
    msg.body = "corpo com \x1b sequência de escape embutida"
    print_mail_detail(msg)
    output = captured_console.getvalue()
    assert "\x1b" not in output


def test_print_event_table_escapes_rich_markup_in_subject(captured_console):
    from unittest.mock import MagicMock

    ev = MagicMock()
    ev.subject = "[bold red]FAKE[/]"
    ev.start = None
    ev.location = None
    ev.object_id = "ev-1"
    print_event_table([ev])
    output = captured_console.getvalue()
    assert "[bold red]FAKE[/]" in output


def test_print_event_detail_escapes_rich_markup_in_subject_and_body(captured_console):
    from unittest.mock import MagicMock

    ev = MagicMock()
    ev.subject = "[bold red]FAKE[/]"
    ev.body = "pauta com [italic]markup[/] falso"
    ev.location = None
    print_event_detail(ev)
    output = captured_console.getvalue()
    assert "[bold red]FAKE[/]" in output
    assert "[italic]markup[/]" in output


def test_print_calendar_table_escapes_rich_markup_in_name(captured_console):
    from unittest.mock import MagicMock

    from scriba.display import print_calendar_table

    cal = MagicMock()
    cal.name = "[bold red]FAKE[/]"
    cal.calendar_id = "cal-1"
    print_calendar_table([cal])
    output = captured_console.getvalue()
    assert "[bold red]FAKE[/]" in output
