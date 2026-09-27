"""Comandos de e-mail: draft, search, read."""

from typing import Optional

import typer

from scriba.auth import get_account
from scriba.display import console, print_error, print_success

app = typer.Typer(help="Comandos de e-mail")


@app.command()
def draft(
    to: str = typer.Option(..., "--to"),
    subject: str = typer.Option(..., "--subject"),
    body: str = typer.Option(..., "--body"),
    cc: Optional[str] = typer.Option(None, "--cc"),
) -> None:
    """Cria um rascunho — nunca envia."""
    account = get_account()
    new_message = account.new_message()

    new_message.to.add(to)
    if cc:
        new_message.cc.add(cc)
    new_message.subject = subject
    new_message.body = body

    if new_message.save_draft():
        print_success("Rascunho criado na pasta Rascunhos do Outlook.")
    else:
        print_error("Falha ao criar rascunho.")
        raise typer.Exit(1)
