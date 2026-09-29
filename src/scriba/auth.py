"""Autenticação O365/MSAL — authorization code flow + PKCE via loopback
local, sem client secret.

SCOPES usa "Mail.ReadWrite" cru, não o preset "message_all" do O365 —
"message_all" embute Mail.Send (ver O365/connection.py DEFAULT_SCOPES),
e este projeto nunca solicita envio de e-mail.

Loopback (ADR `20260928-fluxo-de-auth-troca-device-code-por-auth-code-pkce`):
chama Connection.get_authorization_url()/request_token() direto, não
Account.authenticate() — esse wrapper imprime texto em inglês hardcoded, o
que violaria a restrição pt-BR do CONTEXTO.md.
"""

import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import typer
from O365 import Account, FileSystemTokenBackend

from scriba.config import get_state_dir, load_config
from scriba.display import console, print_error
from scriba.token_crypto import (
    CofreIndisponivelError,
    TokenFormatoAntigoError,
    criar_adaptador_criptografia,
    nome_servico_keychain,
)

SCOPES = ["Mail.ReadWrite", "calendar_all"]
TOKEN_FILENAME = "token"
CALLBACK_TIMEOUT_SECONDS = 300
TENANT_PROIBIDO = "common"


class _CallbackHandler(BaseHTTPRequestHandler):
    """Captura a URL de callback do navegador numa página de confirmação."""

    def do_GET(self) -> None:
        self.server.callback_url = f"http://localhost:{self.server.server_port}{self.path}"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body>Login conclu\xc3\xaddo. Pode fechar esta aba e "
            b"voltar ao terminal.</body></html>"
        )

    def log_message(self, format: str, *args: object) -> None:
        pass  # silencia o log padrão (evita vazar a query string do callback no stdout)


class _TokenBackendComPermissaoRestrita(FileSystemTokenBackend):
    """Restringe a permissão do arquivo de token a 0600 — a lib O365
    grava com `open("w")` puro, herdando a umask do processo (achado F2
    da auditoria de segurança externa, 29/09/2026; medido: 0o644 sem
    esta correção). O arquivo nasce já restrito (chmod ANTES do
    conteúdo, não depois — achado dev-10: aplicar chmod só depois da
    escrita deixa uma janela, ainda que curta e local, em que o
    conteúdo do token já está em disco com a permissão frouxa da
    umask). Não sobrescreve `cryptography_manager` (herdado de
    BaseTokenBackend) — é o ponto de extensão que a Fase 2 (jd-task
    #1077) usa depois, atribuindo um adaptador de criptografia a este
    mesmo atributo, nesta mesma instância. Não redesenhar esta classe
    sem coordenar com a Fase 2."""

    def save_token(self, force: bool = False) -> bool:
        if not self.token_path.parent.exists():
            self.token_path.parent.mkdir(parents=True)
        self.token_path.touch(mode=0o600, exist_ok=True)
        self.token_path.chmod(0o600)  # touch() não reaplica modo em arquivo já existente
        return super().save_token(force=force)


def _token_backend() -> FileSystemTokenBackend:
    backend = _TokenBackendComPermissaoRestrita(
        token_path=get_state_dir(),
        token_filename=TOKEN_FILENAME,
    )
    adaptador = criar_adaptador_criptografia(servico=nome_servico_keychain(get_state_dir()))
    if adaptador is not None:
        backend.cryptography_manager = adaptador
    return backend


def _build_account(client_id: str, tenant_id: str) -> Account:
    return Account(
        (client_id,),
        auth_flow_type="public",
        tenant_id=tenant_id,
        token_backend=_token_backend(),
    )


def _get_graph_scopes(client_id: str, tenant_id: str) -> list[str]:
    account = _build_account(client_id, tenant_id)
    return account.protocol.get_scopes_for(SCOPES)


def _capture_callback_url(server: HTTPServer) -> str | None:
    server.callback_url = None
    server.handle_request()
    server.server_close()
    return server.callback_url


def authenticate(client_id: str, tenant_id: str) -> bool:
    """Autoriza via authorization code flow + PKCE, loopback local.

    Retorna True se autenticou.
    """
    scopes = _get_graph_scopes(client_id, tenant_id)
    account = _build_account(client_id, tenant_id)
    connection = account.con

    server = HTTPServer(("localhost", 0), _CallbackHandler)
    server.timeout = CALLBACK_TIMEOUT_SECONDS
    redirect_uri = f"http://localhost:{server.server_port}"

    auth_uri, flow = connection.get_authorization_url(scopes, redirect_uri=redirect_uri)

    console.print("\n[bold]Abrindo o navegador para você fazer login…[/]")
    webbrowser.open(auth_uri)

    callback_url = _capture_callback_url(server)

    if callback_url is None:
        print_error("Login não completado em tempo (5 minutos). Tente novamente.")
        return False

    try:
        authenticated = connection.request_token(callback_url, flow=flow)
    except ValueError:
        # state incorreto (proteção CSRF do MSAL) — requisição espúria no
        # listener, ou callback corrompido. Erro legível, não traceback.
        authenticated = False

    if not authenticated:
        print_error("Autenticação falhou.")
        return False

    return True


def is_authenticated() -> bool:
    config = load_config()
    client_id = config.get("client_id")
    tenant_id = config.get("tenant_id")
    if not client_id or not tenant_id or tenant_id == TENANT_PROIBIDO:
        return False
    try:
        account = _build_account(client_id, tenant_id)
        return account.is_authenticated
    except Exception:  # noqa: BLE001 — checagem de status nunca deve estourar pro chamador
        return False


def get_account() -> Account:
    """Retorna Account autenticada ou sai com erro (exit 1)."""
    config = load_config()
    client_id = config.get("client_id")
    tenant_id = config.get("tenant_id")

    if not client_id or not tenant_id or tenant_id == TENANT_PROIBIDO:
        print_error(
            "Não configurado. Rode: scriba auth login --client-id <ID> --tenant-id <TENANT>"
        )
        raise typer.Exit(1)

    account = _build_account(client_id, tenant_id)

    if not account.is_authenticated:
        print_error("Não autenticado. Rode: scriba auth login")
        raise typer.Exit(1)

    return account
