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
