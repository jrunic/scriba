"""Smoke manual de `save_draft` contra uma conta Microsoft 365 REAL.

Não faz parte da suíte automatizada (uv run pytest). Roda uma vez, à mão,
contra um tenant sandbox do Microsoft 365 Developer Program — nunca contra
uma caixa de produção. É o tracer bullet real da Task 5: se save_draft()
não funcionar como o código espera, a decisão de biblioteca (O365 vs
msgraph-sdk) é revisada antes de continuar para a Task 6.

Pré-requisito: um app registration no Entra ID do tenant sandbox (public
client, permissões delegadas Mail.ReadWrite + Calendars.ReadWrite,
"Allow public client flows" = Sim).

Uso:
    SCRIBA_CLIENT_ID=<client-id> SCRIBA_TENANT_ID=<tenant-id> \
        uv run python scripts/rascunho_smoke.py destinatario@exemplo.com
"""

import os
import sys

from scriba.auth import authenticate, get_account
from scriba.config import save_config


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Uso: uv run python scripts/rascunho_smoke.py <destinatario@exemplo.com>",
            file=sys.stderr,
        )
        sys.exit(1)

    to_address = sys.argv[1]
    client_id = os.environ.get("SCRIBA_CLIENT_ID")
    tenant_id = os.environ.get("SCRIBA_TENANT_ID", "common")

    if not client_id:
        print("Defina SCRIBA_CLIENT_ID antes de rodar.", file=sys.stderr)
        sys.exit(1)

    print("Autenticando via device code flow...")
    if not authenticate(client_id, tenant_id):
        print("FALHA: autenticação não completou.", file=sys.stderr)
        sys.exit(1)

    # get_account() lê client_id/tenant_id do config.toml (mesmo caminho que
    # o comando `scriba auth login` usa) — sem gravar aqui, get_account()
    # não acha configuração nenhuma e falha com "Não configurado", mesmo
    # logo depois de autenticar com sucesso. Achado real do tracer bullet.
    save_config({"client_id": client_id, "tenant_id": tenant_id})

    account = get_account()
    new_message = account.new_message()
    new_message.to.add(to_address)
    new_message.subject = "scriba smoke test — rascunho"
    new_message.body = "Se você está lendo isto na pasta Rascunhos, o tracer bullet funcionou."

    if new_message.save_draft():
        print("OK: save_draft() retornou True.")
        print("Confira AGORA a pasta Rascunhos do Outlook da conta autenticada.")
    else:
        print(
            "FALHA: save_draft() retornou False — investigar antes de prosseguir.", file=sys.stderr
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
