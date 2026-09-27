"""Comandos de agenda: list, read, create."""

from datetime import datetime, timedelta

import typer

from scriba.auth import get_account
from scriba.display import (
    console,
    print_calendar_table,
    print_error,
    print_event_detail,
    print_event_table,
    print_success,
)

app = typer.Typer(help="Comandos de agenda")


@app.command()
def calendars() -> None:
    """Lista os calendários da conta (nome e id)."""
    account = get_account()
    schedule = account.schedule()

    cals = schedule.list_calendars()
    if not cals:
        console.print("Nenhum calendário encontrado.")
        return

    print_calendar_table(cals)


def _parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")  # noqa: DTZ007 — fuso local, spec assumption 8
    except ValueError:
        print_error(f"Data inválida: {value} (esperado AAAA-MM-DD)")
        raise typer.Exit(1) from None


@app.command("list")
def list_events(
    start: str | None = typer.Option(None, "--start"),
    end: str | None = typer.Option(None, "--end"),
    limit: int = typer.Option(25, "--limit"),
) -> None:
    """Lista eventos num intervalo (default: próximos 7 dias)."""
    start_dt = (
        _parse_date(start)
        if start
        else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)  # noqa: DTZ005 — fuso local, spec assumption 8
    )
    end_dt = _parse_date(end) if end else start_dt + timedelta(days=7)

    account = get_account()
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    if calendar is None:
        print_error("Não foi possível acessar o calendário padrão.")
        raise typer.Exit(1)

    # `get_events(include_recurring=True)` (default) exige start_recurring/
    # end_recurring — não um Query genérico de start/end. Achado de campo
    # (VM Windows, 27/09/2026): `new_query("start")` não existe na lib
    # instalada (`new_query()` não aceita argumento) e `get_events` sem
    # esses dois parâmetros levanta ValueError com include_recurring=True.
    events = list(calendar.get_events(limit=limit, start_recurring=start_dt, end_recurring=end_dt))

    if not events:
        console.print("Nenhum evento encontrado no intervalo.")
        return

    print_event_table(events)


@app.command()
def read(event_id: str = typer.Argument(...)) -> None:
    """Lê um evento por ID."""
    account = get_account()
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    if calendar is None:
        print_error("Não foi possível acessar o calendário padrão.")
        raise typer.Exit(1)

    # get_event() recebe o id posicional — achado de campo, mesma sessão:
    # `object_id=` não é keyword aceita aqui (diferente de get_message).
    event = calendar.get_event(event_id)
    if not event:
        print_error(f"Evento não encontrado: {event_id}")
        raise typer.Exit(1)

    print_event_detail(event)


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")  # noqa: DTZ007 — fuso local, spec assumption 8
    except ValueError:
        print_error(f"Data/hora inválida: {value} (esperado AAAA-MM-DD HH:MM)")
        raise typer.Exit(1) from None


@app.command()
def create(
    subject: str = typer.Option(..., "--subject"),
    start: str = typer.Option(..., "--start"),
    end: str = typer.Option(..., "--end"),
    location: str | None = typer.Option(None, "--location"),
) -> None:
    """Cria um evento na agenda padrão."""
    start_dt = _parse_datetime(start)
    end_dt = _parse_datetime(end)

    account = get_account()
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    if calendar is None:
        print_error("Não foi possível acessar o calendário padrão.")
        raise typer.Exit(1)

    new_event = calendar.new_event()
    new_event.subject = subject
    new_event.start = start_dt
    new_event.end = end_dt
    if location:
        new_event.location = location

    if new_event.save():
        print_success(f"Evento criado: {subject}")
    else:
        print_error("Falha ao criar evento.")
        raise typer.Exit(1)
