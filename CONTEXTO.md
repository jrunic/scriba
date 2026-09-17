---
id: 202609171425
projeto: scriba
tipo: index
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: Padrões técnicos canônicos e restrições do repo scriba — carga default da sessão.
tags: [contexto, dev-skills, Python]
---

# CONTEXTO.md — scriba

## Propósito

CLI Python que dá a um agente de IA acesso a e-mail e agenda do Microsoft 365
(Outlook) via Microsoft Graph — leitura de e-mail, criação de rascunho, leitura
e criação de eventos de calendário. Autenticação delegada por usuário via
device code flow (MSAL), sem client secret. Envio autônomo de e-mail é fora de
escopo por decisão de segurança, não técnica.

## Agente padrão

**Tech** (SRE Agentic) — guardião deste repositório. Modo de atuação: Código + SRE Agentic
(Autocura Assistida). Outros agentes podem ler/contribuir; mudanças estruturais passam por Tech.

## Stack

- **Linguagem:** Python 3.12+
- **Framework CLI:** Typer + Rich (formatação de terminal)
- **Cliente Microsoft Graph:** O365 (github.com/O365/python-o365) sobre MSAL
  (device code flow, public client, sem secret) — ver `docs/decisoes/` para a
  avaliação contra `msgraph-sdk` oficial
- **Banco:** nenhum — estado é config + token OAuth em disco
- **Deploy:** distribuição manual/local por enquanto (instalação via `uv`/`pip`
  na máquina do usuário); sem `upgrade-fleet`, sem systemd, sem cron

### Naming

Convenção Python (PEP 8): `snake_case` (funções/variáveis), `PascalCase`
(classes), `UPPER_SNAKE` (constantes). Identificadores em inglês — exceção da
ADR `20260609-pt-br-padrao-jedi-labs` pra código de aplicação, que segue a
convenção da linguagem/comunidade, não o padrão PT-BR do brain.

### Linguagem

- **Slug do repo/CLI:** `scriba` — nome comercial sem prefixo de frota (ADR
  `20260808-naming-por-audiencia-do-artefato`), repositório público
- **Identificadores no código:** inglês (convenção Python)
- **Comentários inline:** pt-BR
- **Commits:** tipo conventional em inglês (`feat:`, `fix:`...), descrição em pt-BR

### Segredos

- **Onde:** nenhum segredo de aplicação. Auth é public client + device code
  flow (MSAL) — sem client secret, sem certificado. O `client_id`/`tenant_id`
  do app Entra não são segredos (config de usuário). O token OAuth por usuário
  fica em disco local, sob XDG (ver Estrutura) — nunca versionado, nunca em
  `jedi-secrets` (não é credencial da frota, é credencial pessoal do usuário
  final da ferramenta).

### Bibliotecas

- **Política:** requer justificativa registrada (ADR local em
  `docs/decisoes/` para dependência nova que não seja trivial/transitiva) —
  projeto já teve uma decisão de biblioteca avaliada formalmente (O365 vs
  msgraph-sdk) e opera sobre dado sensível (e-mail/agenda de terceiros)
- **Atuais:** `msal`, `O365`, `typer`, `rich`, `tomli-w` (escrita TOML;
  leitura via `tomllib` da stdlib)

### Estrutura

```
CONTEXTO.md GLOSSARIO.md — contratos vivos (raiz)
docs/arquitetura.md — mapa fino
docs/decisoes/  — ADRs locais
docs/dominio/   — modelo de domínio (neg-02)
docs/{tutoriais,guias,referencias,explicacoes}/ — quadrantes Diátaxis (ADR 20260620)

src/scriba/                  — main.py (entry point Typer), auth.py, config.py, display.py
src/scriba/commands/         — sub-apps Typer por domínio: auth_cmd.py, mail_cmd.py, cal_cmd.py
tests/                       — unit (mocka O365 na fronteira) + integração (typer.testing.CliRunner)
scripts/                     — scripts de debug de auth para validação em campo (fora do pacote)
```

Config e token do usuário seguem XDG Base Directory (ADR
`20260913-xdg-padrao-de-armazenamento-da-frota`):
`$XDG_CONFIG_HOME/scriba/config.toml` (client_id, tenant_id) e
`$XDG_STATE_HOME/scriba/token` (cache MSAL). `SCRIBA_HOME` como válvula de
escape para sobrepor a raiz. Não usar `~/.scriba/` flat.

### Testes

- **Framework:** pytest
- **Pasta:** `tests/`
- **Estratégia:** duas camadas — unit mockando `O365` na fronteira, integração
  via `typer.testing.CliRunner` (mock só em fronteira de sistema, disciplina
  do `dev-04-desenvolve-com-tdd`)

### Build/Run

- **Setup:** `uv sync`
- **Testes:** `uv run pytest tests/ -v`
- **Run:** `uv run scriba --help`
- **Build:** `uv build`

### Lint/Format

- **Lint:** `uv run ruff check .`
- **Format:** `uv run ruff format .`

## Onde o trabalho acontece

**O trabalho de desenvolvimento acontece fora deste repositório**, nos
documentos internos do autor.

| Artefato | Lar canônico |
|---|---|
| Roadmap de ciclos, spec, plano | fora deste repositório |
| Arquivo de apoio de tarefa, diário de sessão | fora deste repositório |
| Discussão de negócio, issue | fora deste repositório |
| **Código, testes, migrations** | **este repo** |
| **Documentação do produto** (Diátaxis) | **este repo**, `docs/` |
| **Modelo de domínio, GLOSSARIO.md** | **este repo** |
| **ADR de contrato da ferramenta** | **este repo**, `docs/decisoes/` |
| **README, CHANGELOG** | **este repo** |

**As skills leem esta seção** em vez de inferir por visibilidade.

## Leitura obrigatória antes de spec/plano

- `docs/arquitetura.md` — mapa estrutural
- `GLOSSARIO.md` — vocabulário do domínio (usar estes termos, nunca sinônimos)
- `roadmap.md` — incremento ativo e fronteiras (contrato do Passo 0 do dev-02)
- `docs/dominio/` — modelo formal dos contextos que o trabalho toca

## Restrições

Hard limits sempre relevantes durante a sessão (ADR `20260609-eliminacao-do-84-ia.md` — substitui antigo `docs/84-ia/restricoes.md`).

- **Runner de testes canônico:** `uv run pytest tests/ -v`
- **Idioma da saída para humano:** inglês (CLI pública, audiência não é só pt-BR)
- **Comentários inline:** pt-BR
- **Slug do repo/CLI:** `scriba`
- **`Mail.Send` nunca é pedido nem implementado por padrão.** Escopo do app
  Entra é `Mail.ReadWrite` (rascunho, não envio), `Calendars.ReadWrite`,
  `offline_access`, `User.Read`. Envio autônomo é decisão de segurança
  explicitamente fora do escopo — mudar isso é ADR, não PR direto.
- **Sem client secret em nenhuma hipótese.** Auth é public client + device
  code flow. Se alguma feature futura exigir client credentials (app-only),
  é decisão de segurança que passa por ADR antes do código.
- **Implementação que contradiz `docs/dominio/` ou `GLOSSARIO.md` atualiza o doc no mesmo commit;** divergência que vira decisão arquitetural → dev-07-cria-adr (ADR `20260705-familia-neg-skills-negocio`)


## Decisões Herdadas (explícitas)

- Kebab-case em paths; identificadores seguem a convenção da stack
- Comentários inline em pt-BR
- Sem segredos no repositório
- Sem comandos destrutivos sem confirmação
- Conhecimento destilado em `docs/`; restrições em `CONTEXTO.md`

## Decisões Locais Divergentes

[Listar onde este projeto diverge de regras globais. Cada divergência idealmente tem ADR em docs/decisoes/.]

## Estado Atual

Projeto criado em 2026-09-17 via `dev-01-define-padroes`. Aguardando primeira spec via `dev-02-escreve-spec`.

## Pendências

- [ ] Primeira spec via dev-02-escreve-spec
- [ ] Primeiro plano via dev-03-escreve-plano
- [ ] Setup de testes (framework + pasta + primeiro teste exemplar)

## Referências

- [[docs/arquitetura.md]] — mapa estrutural do repo (mapa fino, isento — carga sob demanda)
- [[docs/explicacoes/visao-geral.md]] — o quê e por quê (quadrante explicação, carga sob demanda)
- [[docs/decisoes/]] — ADRs locais
