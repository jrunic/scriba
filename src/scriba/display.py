"""Console Rich compartilhada e utilitários de formatação."""

import html
import re

from rich.console import Console
from rich.markup import escape as _escape_rich_markup

console = Console()

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _safe(text) -> str:
    """Texto remoto (assunto, remetente, corpo, nome) nunca é markup Rich
    nem carrega caractere de controle — achado F7 da auditoria de
    segurança externa (29/09/2026): sem isto, `[bold red]...[/]` vindo de
    um assunto de e-mail é interpretado como formatação real."""
    text = str(text or "")
    text = _CONTROL_CHARS_RE.sub("", text)
    return _escape_rich_markup(text)


def print_error(msg: str) -> None:
    console.print(f"[bold red]Erro:[/] {msg}")


def print_success(msg: str) -> None:
    console.print(f"[bold green]OK:[/] {msg}")


def strip_html(text: str) -> str:
    """Converte corpo de e-mail em HTML para texto legível em terminal.

    Remove bloco <style>/<script> inteiro (conteúdo, não só a tag) e
    zero-width space (U+200B) — achado de campo (VM Windows, 27/09/2026):
    e-mail HTML real da Microsoft deixava CSS vazando no terminal e o
    U+200B quebrava a codificação cp1252 do console legado do Windows com
    UnicodeEncodeError.
    """
    clean = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<script[^>]*>.*?</script>", "", clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<br\s*/?>", "\n", clean)
    clean = re.sub(r"<p[^>]*>", "\n", clean)
    clean = re.sub(r"</p>", "", clean)
    clean = re.sub(r"<[^>]+>", "", clean)
    clean = re.sub(r"&nbsp;", " ", clean)
    clean = html.unescape(clean)
    clean = clean.replace("\u200b", "")
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
        table.add_row(_safe(sender), _safe(subject), object_id)

    console.print(table)


from rich.panel import Panel


def print_mail_detail(msg) -> None:
    sender = str(getattr(msg, "sender", "") or "Desconhecido")
    body = getattr(msg, "body", "") or "(vazio)"
    if looks_like_html(body):
        body = strip_html(body)

    header = f"[bold]De:[/] {_safe(sender)}"
    console.print(
        Panel(
            header, title=_safe(getattr(msg, "subject", "") or "(sem assunto)"), border_style="blue"
        )
    )
    console.print(_safe(body))


def _location_name(location) -> str:
    """Event.location na lib real é um dict estruturado (displayName,
    locationType, uniqueId, uniqueIdType) — achado de campo (VM Windows,
    27/09/2026). Exibir o dict cru mostraria o repr inteiro pro usuário."""
    if isinstance(location, dict):
        return location.get("displayName", "") or ""
    return str(location) if location else ""


def print_event_table(events: list) -> None:
    table = Table(title="Eventos")
    table.add_column("Assunto", style="white")
    table.add_column("Início", style="green", max_width=20)
    table.add_column("Local", style="cyan", max_width=25)
    table.add_column("ID", style="dim", max_width=36)

    for ev in events:
        start = ev.start.strftime("%Y-%m-%d %H:%M") if getattr(ev, "start", None) else ""
        location = _location_name(getattr(ev, "location", None))
        table.add_row(
            _safe(getattr(ev, "subject", "") or ""),
            start,
            _safe(location),
            getattr(ev, "object_id", "") or "",
        )

    console.print(table)


def print_event_detail(event) -> None:
    location = _location_name(getattr(event, "location", None))
    header = f"[bold]Local:[/] {_safe(location)}"

    body = getattr(event, "body", "") or "(sem descrição)"
    if looks_like_html(body):
        body = strip_html(body)

    console.print(
        Panel(
            header,
            title=_safe(getattr(event, "subject", "") or "(sem assunto)"),
            border_style="green",
        )
    )
    console.print(_safe(body))


def print_calendar_table(calendars: list) -> None:
    table = Table(title="Calendários")
    table.add_column("Nome", style="white")
    table.add_column("ID", style="dim", max_width=48)

    for cal in calendars:
        table.add_row(_safe(getattr(cal, "name", "") or ""), getattr(cal, "calendar_id", "") or "")

    console.print(table)
