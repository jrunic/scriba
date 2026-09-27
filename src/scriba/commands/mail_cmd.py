"""Comandos de e-mail: draft, search, read."""

from datetime import timedelta

import typer

from scriba.auth import get_account
from scriba.commands.cal_cmd import _parse_date
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


def _build_search_query(
    mailbox,
    *,
    unread: bool,
    sender: str | None,
    subject: str | None = None,
    has_attachments: bool = False,
    importance: str | None = None,
    start_date=None,
    end_date=None,
):
    """Combina filtros com o operador `&` do CompositeFilter.

    Achado de campo (VM Windows, 27/09/2026): a lib `O365` instalada
    (2.1.10) não tem `on_attribute()`/`chain()` — `QueryBuilder.equals()`/
    `.contains()` recebem `(atributo, valor)` direto e devolvem um
    `CompositeFilter` que se combina com `&`/`|`. `--start-date`/
    `--end-date` usam o atributo `receivedDateTime` explícito — nunca os
    atalhos `start`/`end`, que o `_attribute_mapping` da lib expande para
    caminho de EVENTO (`start/DateTime`), não de mensagem (achado de
    revisão dev-10, query.py:470).
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
    if subject:
        filters.append(q.contains("subject", subject))
    if has_attachments:
        filters.append(q.equals("hasAttachments", True))
    if importance:
        filters.append(q.equals("importance", importance))
    if start_date:
        filters.append(q.greater_equal("receivedDateTime", start_date))
    if end_date:
        filters.append(q.less_equal("receivedDateTime", end_date))
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
    subject: str | None = typer.Option(None, "--subject"),
    has_attachments: bool = typer.Option(False, "--has-attachments"),
    importance: str | None = typer.Option(None, "--importance"),
    start_date: str | None = typer.Option(None, "--start-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    limit: int = typer.Option(25, "--limit"),
) -> None:
    """Lista/filtra mensagens recentes da caixa de entrada."""
    account = get_account()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    # --end-date é inclusivo do dia inteiro (decisão de revisão dev-10,
    # 27/09/2026): soma um dia antes do less_equal, senão exclui as
    # mensagens do próprio dia final (_parse_date devolve meia-noite).
    end_date_dt = _parse_date(end_date) + timedelta(days=1) if end_date else None

    query = _build_search_query(
        mailbox,
        unread=unread,
        sender=sender,
        subject=subject,
        has_attachments=has_attachments,
        importance=importance,
        start_date=_parse_date(start_date) if start_date else None,
        end_date=end_date_dt,
    )
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
