"""Comandos de e-mail: draft, search, read."""

from typing import Optional

import typer

from scriba.auth import get_account
from scriba.display import console, print_error, print_mail_detail, print_mail_table, print_success

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


@app.command()
def search(
    unread: bool = typer.Option(False, "--unread"),
    sender: Optional[str] = typer.Option(None, "--from"),
    limit: int = typer.Option(25, "--limit"),
) -> None:
    """Lista/filtra mensagens recentes da caixa de entrada."""
    account = get_account()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    params = {"limit": limit}
    if unread or sender:
        query = mailbox.new_query()
        first = True
        if unread:
            clause = query.on_attribute("isRead") if first else query.chain("and").on_attribute("isRead")
            clause.equals(False)
            first = False
        if sender:
            clause = query.on_attribute("from/emailAddress/address") if first else query.chain("and").on_attribute("from/emailAddress/address")
            clause.contains(sender)
            first = False
        params["query"] = query

    messages = list(inbox.get_messages(**params))

    if not messages:
        console.print("Nenhuma mensagem encontrada.")
        return

    print_mail_table(messages)


@app.command()
def read(message_id: str = typer.Argument(...)) -> None:
    """Lê uma mensagem por ID."""
    account = get_account()
    mailbox = account.mailbox()

    msg = mailbox.get_message(object_id=message_id)
    if msg is None:
        print_error(f"Mensagem não encontrada: {message_id}")
        raise typer.Exit(1)

    print_mail_detail(msg)
