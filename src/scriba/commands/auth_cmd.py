"""Comandos de autenticação: login, logout, status."""

import typer

from scriba.auth import TOKEN_FILENAME, authenticate, is_authenticated
from scriba.config import get_state_dir, load_config, save_config
from scriba.display import console, print_error, print_success

app = typer.Typer(help="Gerencia autenticação.")


@app.command()
def login(
    client_id: str | None = typer.Option(None, "--client-id", envvar="SCRIBA_CLIENT_ID"),
    tenant_id: str = typer.Option("common", "--tenant-id", envvar="SCRIBA_TENANT_ID"),
) -> None:
    """Autentica via device code flow."""
    config = load_config()

    if client_id:
        config["client_id"] = client_id
        config["tenant_id"] = tenant_id
        save_config(config)
    else:
        client_id = config.get("client_id")

    if not client_id:
        print_error("Nenhum client ID encontrado. Rode: scriba auth login --client-id <ID>")
        raise typer.Exit(1)

    tenant_id = config.get("tenant_id", tenant_id)

    if authenticate(client_id, tenant_id):
        print_success("Autenticado com sucesso.")
    else:
        print_error("Autenticação falhou.")
        raise typer.Exit(1)


@app.command()
def logout() -> None:
    """Remove o token local."""
    # FileSystemTokenBackend grava exatamente TOKEN_FILENAME, sem sufixo
    # ".token" — achado de campo (VM Windows, 27/09/2026); confirmado por
    # listagem real do state dir, não pela suposição anterior.
    token_path = get_state_dir() / TOKEN_FILENAME
    if token_path.exists():
        token_path.unlink()
        print_success("Logout feito — token removido.")
    else:
        console.print("Nenhum token encontrado; já deslogado.")


@app.command()
def status() -> None:
    """Mostra status de autenticação e configuração."""
    config = load_config()
    console.print(f"[bold]Client ID:[/] {config.get('client_id', 'não definido')}")
    console.print(f"[bold]Tenant ID:[/] {config.get('tenant_id', 'não definido')}")

    if is_authenticated():
        print_success("Autenticado.")
    else:
        print_error("Não autenticado.")
        raise typer.Exit(1)
