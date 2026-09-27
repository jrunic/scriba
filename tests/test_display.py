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


from scriba.display import print_mail_table


def test_print_mail_table_shows_subject_and_sender(mock_message, captured_console):
    print_mail_table([mock_message])
    output = captured_console.getvalue()
    assert "Assunto de teste" in output
    assert "remetente@example.com" in output
