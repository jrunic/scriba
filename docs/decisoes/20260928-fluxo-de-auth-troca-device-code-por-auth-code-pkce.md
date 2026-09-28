---
id: 202609281600
projeto: scriba
tipo: decisao
status: aprovado
data: 2026-09-28
escopo: repo:scriba
plataforma: "*"
dominios: [tecnologia]
descricao: "ADR — scriba troca device code flow por authorization code flow + PKCE (loopback), porque Microsoft Entra Security Defaults bloqueia device code por padrão em todo tenant novo"
tags: [adr, decisao, auth, msal, o365, security-defaults]
---

# ADR — troca de fluxo de autenticação: device code → authorization code + PKCE

## Status

Aprovado em 2026-09-28.

## Contexto

O v0 do `scriba` (ADR `20260927-biblioteca-microsoft-graph.md`) escolheu
device code flow porque desacopla o navegador (máquina do humano) do CLI
(ambiente de quem roda o comando) — não exige HTTP listener local nem que
os dois estejam na mesma máquina.

Em 27-28/09/2026, `scriba auth login` passou a falhar no tenant de teste
(`jedilabs123.onmicrosoft.com`) com `Error Code: 530035`. Confirmado contra
a documentação oficial da Microsoft
(`learn.microsoft.com/entra/fundamentals/security-defaults`, seção
"Enforced security policies"):

> **Block device code flow** — "After security defaults are enabled in your
> tenant, authentication requests that use device code flow are blocked.
> [...] Starting July 1, 2026, all new Microsoft Entra tenants block device
> code flow as part of security defaults."

Não é falha de configuração pontual: é a postura de segurança que a
Microsoft está tornando padrão em **todo tenant novo desde 01/07/2026**.
Qualquer organização cliente sem licença Entra ID P1/P2 (não pode usar
Conditional Access pra abrir exceção) bloqueia o único mecanismo de auth
que o `scriba` implementava — risco real pra qualquer cliente real do
produto, não hipotético.

## Decisão

Trocar o fluxo de auth pra **authorization code flow com PKCE**, via
loopback local (`http://localhost`) — sem client secret, continua public
client.

Reaproveita a integração já existente da lib `O365`: `Account.authenticate()`
aceita `redirect_uri` e um `handle_consent: Callable` customizável (o
default da lib pede copiar-colar manual da URL de retorno via
`consent_input_token`). Por baixo, `Connection.get_authorization_url()`/
`request_token()` já chamam `msal_client.initiate_auth_code_flow()`/
`acquire_token_by_auth_code_flow()` e gravam no mesmo
`FileSystemTokenBackend` que o device code usava — a troca é só o
`handle_consent`, não a integração inteira.

## Evidência de campo

Medido em 28/09/2026 contra o mesmo tenant que bloqueou device code duas
vezes ao vivo — detalhe completo em
`13-processos/manter-scriba/11-tarefas/20260928-pesquisa-troca-fluxo-auth.md`
(fora deste repositório):

1. `msal.PublicClientApplication.acquire_token_interactive()` — token
   emitido, prova que auth code + PKCE não é bloqueado pelos Padrões de
   Segurança (coerente com a doc oficial, que lista device code separado
   dos outros controles).
2. Caminho real que `auth.py` usaria — `Account.authenticate()` nativo da
   `O365` com `handle_consent` customizado (`HTTPServer` local em
   `http://localhost:8765`, sem porta fixa registrada no app — a Microsoft
   casa qualquer porta contra um redirect `http://localhost` sem porta pra
   client público). Token persistido, recarregado em processo novo, e
   usado numa chamada real ao Graph (`mailbox.get_messages`) — funcionou.

## Topologia — por que isso não reabre a decisão original

Device code foi escolhido porque não exige que navegador e CLI estejam na
mesma máquina. Loopback exige. Medido contra a arquitetura real do `koine`
(`docs/arquitetura.md` do repo `koine`, não assumido): o fluxo principal é
`cli.main([cliente, agente, pasta]) → ... → launch.lancar(cliente, pasta) →
execvpe no cliente IA`. `execvpe` é substituição de processo local — o
Koine nunca lança o cliente de IA numa máquina remota. Não existe cenário
headless/remoto na arquitetura atual do Koine — loopback serve pra toda a
base de usuários que o `scriba` foi desenhado pra atender.

## O que muda no código e na documentação (fora do escopo deste ADR — spec)

- `auth.py`/`auth_cmd.py`: novo `handle_consent` com loopback, redirect
  configurável, mensagens de saída diferentes (sem "código de X dígitos").
- App registration do `scriba` (e qualquer cliente que já tenha um)
  precisa de Redirect URI `http://localhost` cadastrado — device code não
  precisava de nenhum.
- `docs/guias/instalar.md` (trilha do humano): não tem mais código pra
  digitar, vira "confirme o login que abrir no navegador".
- `docs/guias/verificar-prontidao-organizacao.md`, pergunta 3: a
  remediação "pedir exceção de Conditional Access" pra bloqueio de device
  code deixa de fazer sentido (o novo fluxo não é bloqueado por Padrões de
  Segurança) — mas a pergunta de Conditional Access em si continua
  relevante por outros motivos (sign-in frequency), revisar sem remover.

## Alternativas recusadas

- **Desabilitar Padrões de Segurança no tenant do cliente:** reduz a
  postura de segurança da organização inteira; decisão do cliente, não do
  `scriba`; não escala (o Orlando não controla a configuração de cada
  tenant cliente).
- **Exigir Entra ID P1 + Conditional Access com exceção:** custo de
  licença e decisão do cliente; produto ficaria condicionado a upgrade
  pago só pra funcionar.
- **Manter device code, documentar como limitação:** inviável — é o único
  fluxo de auth implementado; sem alternativa, "documentar a limitação"
  significa o produto não funcionar em qualquer tenant novo pós-01/07/2026.

## Referências

- learn.microsoft.com/entra/fundamentals/security-defaults
- github.com/MicrosoftDocs/entra-docs — `reference-error-codes.md` (530035)
- `13-processos/manter-scriba/11-tarefas/20260928-pesquisa-troca-fluxo-auth.md`
  (fora deste repositório) — medições completas
- ADR anterior: `20260927-biblioteca-microsoft-graph.md`
