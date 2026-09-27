"""Autenticação O365/MSAL — device code flow, sem client secret.

SCOPES usa "Mail.ReadWrite" cru, não o preset "message_all" do O365 —
"message_all" embute Mail.Send (ver O365/connection.py DEFAULT_SCOPES),
e este projeto nunca solicita envio de e-mail.
"""

import typer
from msal import PublicClientApplication
from O365 import Account, FileSystemTokenBackend

from scriba.config import get_state_dir, load_config
from scriba.display import console, print_error

SCOPES = ["Mail.ReadWrite", "calendar_all"]
TOKEN_FILENAME = "token"
MSAL_AUTHORITY = "https://login.microsoftonline.com/{tenant_id}"


def _token_backend() -> FileSystemTokenBackend:
    return FileSystemTokenBackend(
        token_path=get_state_dir(),
        token_filename=TOKEN_FILENAME,
    )


def _build_account(client_id: str, tenant_id: str = "common") -> Account:
    return Account(
        (client_id,),
        auth_flow_type="public",
        tenant_id=tenant_id,
        token_backend=_token_backend(),
    )


def _get_graph_scopes(client_id: str, tenant_id: str = "common") -> list[str]:
    account = _build_account(client_id, tenant_id)
    return account.protocol.get_scopes_for(SCOPES)


def authenticate(client_id: str, tenant_id: str = "common") -> bool:
    """Roda o device code flow via MSAL. Retorna True se autenticou."""
    backend = _token_backend()
    scopes = _get_graph_scopes(client_id, tenant_id)
    authority = MSAL_AUTHORITY.format(tenant_id=tenant_id)

    app = PublicClientApplication(client_id, authority=authority, token_cache=backend)

    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        print_error(
            f"Falha ao iniciar device code flow: {flow.get('error_description', 'erro desconhecido')}"
        )
        return False

    console.print(f"\n[bold]Acesse:[/] [link]{flow['verification_uri']}[/link]")
    console.print(f"[bold]Digite o código:[/] [bold cyan]{flow['user_code']}[/bold cyan]\n")

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        backend.save_token(force=True)
        return True

    print_error(result.get("error_description", "Autenticação falhou."))
    return False


def is_authenticated() -> bool:
    config = load_config()
    client_id = config.get("client_id")
    if not client_id:
        return False
    try:
        account = _build_account(client_id, config.get("tenant_id", "common"))
        return account.is_authenticated
    except Exception:  # noqa: BLE001 — checagem de status nunca deve estourar pro chamador
        return False


def get_account() -> Account:
    """Retorna Account autenticada ou sai com erro (exit 1)."""
    config = load_config()
    client_id = config.get("client_id")

    if not client_id:
        print_error("Não configurado. Rode: scriba auth login --client-id <ID>")
        raise typer.Exit(1)

    account = _build_account(client_id, config.get("tenant_id", "common"))

    if not account.is_authenticated:
        print_error("Não autenticado. Rode: scriba auth login")
        raise typer.Exit(1)

    return account
