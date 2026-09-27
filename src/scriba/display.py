"""Console Rich compartilhada e utilitários de formatação."""

import html
import re

from rich.console import Console

console = Console()


def print_error(msg: str) -> None:
    console.print(f"[bold red]Erro:[/] {msg}")


def print_success(msg: str) -> None:
    console.print(f"[bold green]OK:[/] {msg}")


def strip_html(text: str) -> str:
    """Converte corpo de e-mail em HTML para texto legível em terminal."""
    clean = re.sub(r"<br\s*/?>", "\n", text)
    clean = re.sub(r"<p[^>]*>", "\n", clean)
    clean = re.sub(r"</p>", "", clean)
    clean = re.sub(r"<[^>]+>", "", clean)
    clean = re.sub(r"&nbsp;", " ", clean)
    clean = html.unescape(clean)
    return clean.strip()


def looks_like_html(text: str) -> bool:
    return bool(re.search(r"<(html|div|p|br|table)\b", text, re.IGNORECASE))


from rich.table import Table


def print_mail_table(messages: list) -> None:
    table = Table(title="Mensagens")
    table.add_column("De", style="cyan", max_width=30)
    table.add_column("Assunto", style="white")
    table.add_column("ID", style="dim", max_width=36)

    for msg in messages:
        sender = str(getattr(msg, "sender", "") or "")
        subject = getattr(msg, "subject", "") or ""
        object_id = getattr(msg, "object_id", "") or ""
        table.add_row(sender, subject, object_id)

    console.print(table)


from rich.panel import Panel


def print_mail_detail(msg) -> None:
    sender = str(getattr(msg, "sender", "") or "Desconhecido")
    body = getattr(msg, "body", "") or "(vazio)"
    if looks_like_html(body):
        body = strip_html(body)

    header = f"[bold]De:[/] {sender}"
    console.print(Panel(header, title=getattr(msg, "subject", "") or "(sem assunto)", border_style="blue"))
    console.print(body)
