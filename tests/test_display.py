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
