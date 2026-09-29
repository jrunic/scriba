"""Comandos de autenticação: login, logout, status."""

import subprocess
import sys

import typer

from scriba.auth import TENANT_PROIBIDO, TOKEN_FILENAME, authenticate, is_authenticated
from scriba.config import get_state_dir, load_config, save_config
from scriba.display import console, print_error, print_success
from scriba.token_crypto import CofreIndisponivelError, nome_servico_keychain

app = typer.Typer(help="Gerencia autenticação.")


@app.command()
def login(
    client_id: str | None = typer.Option(None, "--client-id", envvar="SCRIBA_CLIENT_ID"),
    tenant_id: str | None = typer.Option(None, "--tenant-id", envvar="SCRIBA_TENANT_ID"),
) -> None:
    """Autentica via authorization code flow com PKCE (login pelo navegador)."""
    config = load_config()

    if client_id:
        config["client_id"] = client_id
    else:
        client_id = config.get("client_id")

    if not client_id:
        print_error("Nenhum client ID encontrado. Rode: scriba auth login --client-id <ID>")
        raise typer.Exit(1)

    if tenant_id is None:
        tenant_id = config.get("tenant_id")

    if not tenant_id or tenant_id == TENANT_PROIBIDO:
        print_error(
            "Tenant obrigatório. Rode: scriba auth login --tenant-id <id-do-tenant> "
            "('common' não é aceito — use o Directory (tenant) ID da sua organização, "
            "ver docs/guias/cadastrar-app-entra.md)."
        )
        raise typer.Exit(1)

    config["tenant_id"] = tenant_id
    save_config(config)

    if authenticate(client_id, tenant_id):
        print_success("Autenticado com sucesso.")
    else:
        print_error("Autenticação falhou.")
        raise typer.Exit(1)


@app.command()
def logout() -> None:
    """Remove o token local (e o item do Keychain em macOS, se houver)."""
    token_path = get_state_dir() / TOKEN_FILENAME
    tinha_token_local = token_path.exists()

    if tinha_token_local:
        token_path.unlink()

    if sys.platform == "darwin":
        servico = nome_servico_keychain(get_state_dir())
        subprocess.run(
            ["security", "delete-generic-password", "-s", servico, "-a", "token"],
            capture_output=True,
            check=False,
        )

    if tinha_token_local:
        print_success("Logout feito — token removido.")
        console.print(
            "[yellow]Aviso:[/] isso remove só o token local. A sessão no Microsoft "
            "Entra continua válida até expirar ou ser revogada — ver "
            "'Como revogar o acesso' em docs/guias/cadastrar-app-entra.md."
        )
    else:
        console.print("Nenhum token encontrado; já deslogado.")


@app.command()
def status() -> None:
    """Mostra status de autenticação e configuração."""
    config = load_config()
    console.print(f"[bold]Client ID:[/] {config.get('client_id', 'não definido')}")
    console.print(f"[bold]Tenant ID:[/] {config.get('tenant_id', 'não definido')}")

    try:
        autenticado = is_authenticated()
    except CofreIndisponivelError as exc:
        print_error(f"Cofre de credenciais do sistema indisponível: {exc}")
        raise typer.Exit(1) from None

    if autenticado:
        print_success("Autenticado.")
    else:
        print_error("Não autenticado.")
        raise typer.Exit(1)
