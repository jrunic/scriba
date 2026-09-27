"""Comandos de e-mail: draft, search, read."""


import typer

from scriba.auth import get_account
from scriba.display import console, print_error, print_mail_detail, print_mail_table, print_success

app = typer.Typer(help="Comandos de e-mail")


@app.command()
def draft(
    to: str = typer.Option(..., "--to"),
    subject: str = typer.Option(..., "--subject"),
    body: str = typer.Option(..., "--body"),
    cc: str | None = typer.Option(None, "--cc"),
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
def reply(
    message_id: str = typer.Argument(...),
    body: str = typer.Option(..., "--body"),
    reply_all: bool = typer.Option(False, "--reply-all"),
) -> None:
    """Cria um rascunho de resposta a uma mensagem existente — nunca envia."""
    account = get_account()
    mailbox = account.mailbox()

    original = mailbox.get_message(object_id=message_id)
    if original is None:
        print_error(f"Mensagem não encontrada: {message_id}")
        raise typer.Exit(1)

    try:
        draft = original.reply(to_all=reply_all)
    except RuntimeError:
        print_error("Não é possível responder a esta mensagem (já é rascunho).")
        raise typer.Exit(1) from None

    if draft is None:
        print_error("Falha ao criar rascunho de resposta.")
        raise typer.Exit(1)

    draft.body = body

    if draft.save_draft():
        print_success("Resposta criada na pasta Rascunhos do Outlook.")
    else:
        print_error("Falha ao salvar rascunho de resposta.")
        raise typer.Exit(1)


def _build_search_query(mailbox, *, unread: bool, sender: str | None):
    """Combina filtros com o operador `&` do CompositeFilter.

    Achado de campo (VM Windows, 27/09/2026): a lib `O365` instalada
    (2.1.10) não tem `on_attribute()`/`chain()` — `QueryBuilder.equals()`/
    `.contains()` recebem `(atributo, valor)` direto e devolvem um
    `CompositeFilter` que se combina com `&`/`|`. O mock da suíte aceitava
    qualquer chamada e nunca teria pego essa deriva de API.
    """
    q = mailbox.new_query()
    filters = []
    if unread:
        filters.append(q.equals("isRead", False))
    if sender:
        # "from" (não o path composto) — o mapeamento interno da lib expande
        # pra "from/emailAddress/address" com o casing certo do protocolo;
        # passar o path já composto corrompe a string (achado de campo).
        filters.append(q.contains("from", sender))
    if not filters:
        return None
    combined = filters[0]
    for extra in filters[1:]:
        combined = combined & extra
    return combined


@app.command()
def search(
    unread: bool = typer.Option(False, "--unread"),
    sender: str | None = typer.Option(None, "--from"),
    limit: int = typer.Option(25, "--limit"),
) -> None:
    """Lista/filtra mensagens recentes da caixa de entrada."""
    account = get_account()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    query = _build_search_query(mailbox, unread=unread, sender=sender)
    messages = list(inbox.get_messages(limit=limit, query=query))

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
