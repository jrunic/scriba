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
authorization code flow + PKCE (MSAL, loopback local), sem client secret.
Envio autônomo de e-mail é fora de
escopo por decisão de segurança, não técnica.

## Agente padrão

**Tech** (SRE Agentic) — guardião deste repositório. Modo de atuação: Código + SRE Agentic
(Autocura Assistida). Outros agentes podem ler/contribuir; mudanças estruturais passam por Tech.

## Stack

- **Linguagem:** Python 3.12+
- **Framework CLI:** Typer + Rich (formatação de terminal)
- **Cliente Microsoft Graph:** O365 (github.com/O365/python-o365) sobre MSAL
  (authorization code flow + PKCE via loopback, public client, sem secret) —
  ver `docs/decisoes/` para a avaliação contra `msgraph-sdk` oficial e a
  troca de fluxo (`20260928-fluxo-de-auth-troca-device-code-por-auth-code-pkce`)
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

- **Onde:** nenhum segredo de aplicação. Auth é public client + authorization
  code flow com PKCE (MSAL, loopback local) — sem client secret, sem
  certificado. O `client_id`/`tenant_id`
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
  leitura via `tomllib` da stdlib), `msal-extensions` (pin exato 1.3.1 —
  cofre do SO para o token, F1 da auditoria, Fase 2)

### Estrutura

```
CONTEXTO.md GLOSSARIO.md — contratos vivos (raiz)
docs/arquitetura.md — mapa fino
docs/decisoes/  — ADRs locais
docs/dominio/   — modelo de domínio (neg-02)
docs/{tutoriais,guias,referencias,explicacoes}/ — quadrantes Diátaxis (ADR 20260620)

src/scriba/                  — main.py (entry point Typer), auth.py, config.py, display.py, token_crypto.py
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
- **Idioma da saída para humano:** pt-BR. (Divergência do que este arquivo
  dizia antes — "inglês" — nunca foi seguida; corrigido em 27/09/2026 pra
  bater com o que os 9 comandos entregam de fato.)
- **Comentários inline:** pt-BR
- **Slug do repo/CLI:** `scriba`
- **`Mail.Send` nunca é pedido nem implementado por padrão.** Escopo
  explicitamente pedido pelo código (medido via `_get_graph_scopes()`,
  achado da revisão `dev-10` de 27/09/2026 — a linha anterior aqui citava
  `offline_access`/`User.Read` como pedidos, o que a medição não confirma):
  `Mail.ReadWrite` (rascunho, não envio) e `Calendars.ReadWrite`.
  `offline_access` é concedido implicitamente pelo MSAL a client público, sem
  aparecer na lista que o código declara; `User.Read` depende da configuração
  do app registration no portal, não do código. Envio autônomo é decisão de
  segurança explicitamente fora do escopo — mudar isso é ADR, não PR direto.
- **Sem client secret em nenhuma hipótese.** Auth é public client +
  authorization code flow com PKCE (loopback local). Se alguma feature
  futura exigir client credentials (app-only), é decisão de segurança que
  passa por ADR antes do código.
- **Redirect URI `http://localhost` (sem porta fixa) é pré-condição do app
  registration.** Quem administra o tenant onde o `scriba` roda precisa
  cadastrar esse Redirect URI antes do primeiro login — sem ele,
  `get_authorization_url()` falha. Ver `docs/guias/instalar.md`.
- **Implementação que contradiz `docs/dominio/` ou `GLOSSARIO.md` atualiza o doc no mesmo commit;** divergência que vira decisão arquitetural → dev-07-cria-adr (ADR `20260705-familia-neg-skills-negocio`)
- **A API de query da lib `O365` instalada (2.1.10) não é a dos tutoriais
  antigos.** `new_query()` não aceita argumento; não existe
  `on_attribute()`/`chain()`. `QueryBuilder.equals()`/`.contains()`/
  `.greater_equal()` recebem `(atributo, valor)` direto e devolvem um
  `CompositeFilter` que se combina com `&`/`|`. Atributo de campo composto
  (ex.: remetente) é a chave curta do mapeamento (`"from"`), não o path
  Graph completo — a lib expande sozinha. Achado de campo (bancada
  Windows, 27/09/2026) que a suíte mockada não pega sozinha: qualquer
  código novo que construa `Query` deve ter pelo menos um teste contra um
  objeto `O365` real (padrão em `tests/test_mail_cmd.py::test_build_search_query_*`),
  não só mock.
- **`Schedule.get_calendar()`/qualquer chamada da lib `O365` não devolve
  `None` para todo erro — devolve `None` só quando o Graph responde com
  uma resposta HTTP falsy; para a maioria dos erros 4xx/5xx (`raise_http_errors=True`
  é o default) ela levanta `requests.exceptions.HTTPError`.** Achado de
  campo (bancada Windows, 27/09/2026): um id malformado (não um id real de
  formato reconhecível) causa 400 Bad Request no Graph, e a lib levanta em
  vez de devolver falsy — código que trata "não encontrado" como só
  `if resultado is None` some com esse caso. Qualquer caminho que tente
  recurso por id possivelmente inválido precisa envolver a chamada em
  `try/except HTTPError`, não só checar `None` (ver `_resolve_calendar` em
  `cal_cmd.py` para o padrão).


## Decisões Herdadas (explícitas)

- Kebab-case em paths; identificadores seguem a convenção da stack
- Comentários inline em pt-BR
- Sem segredos no repositório
- Sem comandos destrutivos sem confirmação
- Conhecimento destilado em `docs/`; restrições em `CONTEXTO.md`

## Decisões Locais Divergentes

[Listar onde este projeto diverge de regras globais. Cada divergência idealmente tem ADR em docs/decisoes/.]

## Estado Atual

Segundo incremento (`scriba-20260927-resposta-calendarios-busca`)
implementado, validado em campo e **aceito** em 27/09/2026 — soma aos 9
comandos do v0 mais `mail reply`/`--reply-all`, `cal calendars`,
`--calendar` em `cal list/read/create`, e
`--subject`/`--has-attachments`/`--importance`/`--start-date`/`--end-date`
em `mail search`. 72 testes verdes, validado em macOS e na VM Windows (conta
restrita). Um bug real de campo corrigido no caminho: a lib `O365` levanta
`HTTPError` (não devolve `None`) pra id de calendário malformado — ver
restrição em `## Restrições`.

`docs/guias/` ganhou 4 guias how-to (prontidão da organização, instalação,
reautenticação, permissões e limites), voltados a quem usa o `scriba` por
trás de um agente de IA — não só a quem desenvolve o repo. Trabalho fora do
roadmap de incrementos (documentação, sem código de produto).

Terceiro incremento (`scriba-20260928-troca-fluxo-auth`) implementado,
validado em campo e **aceito** em 28/09/2026 — troca device code flow por
authorization code flow + PKCE via loopback local (Microsoft Entra Security
Defaults bloqueia device code por padrão em todo tenant novo desde
01/07/2026). 75 testes verdes. Publicado como release `v0.2.0`
(github.com/jrunic/scriba/releases/tag/v0.2.0, 28/09/2026) — primeira
release desde a `v0.1.0`.

Guia `docs/guias/cadastrar-app-entra.md` adicionado (voltado à equipe de TI
que autoriza o app no Microsoft Entra) e resíduo de texto "device code"
corrigido em 3 pontos fora do alcance da varredura do incremento 3
(docstring do comando, script de smoke test, glossário). Publicado como
release `v0.2.1` (28/09/2026).

Quarto incremento (`scriba-20260929-endurecimento-pos-auditoria-fase1`,
jd-task #1076) implementado e **aceito** em 29/09/2026 — oito achados de
uma auditoria de segurança externa sem dependência nova: sanitização Rich
em 5 pontos de exibição, permissão restrita (0600) do arquivo de token,
tenant obrigatório sem exceção para `"common"`, aviso de não-revogação no
`auth logout`, guia de instalação por release com checksum, guia de
revogação reescrito a partir de fonte oficial da Microsoft, corpo de
mensagem fora de argumento de CLI (`--body-file`/stdin), pinagem das
GitHub Actions por hash de commit. 104 testes verdes. Lacunas conhecidas
em `## Pendências`. A Fase 2 (F1 da mesma auditoria, cofre do SO para o
token) é jd-task #1077, ciclo 5 — implementada (ver incremento abaixo),
tarefa fechada; ciclo aberto até a validação de campo.

Quinto incremento (`scriba-20260929-endurecimento-pos-auditoria-fase2`,
jd-task #1077) implementado — F1 da auditoria: conteúdo do token
protegido pelo cofre do sistema operacional (DPAPI no Windows, Keychain
no macOS), via `cryptography_manager` (dependência nova `msal-extensions`,
pin exato 1.3.1, ADR local). Linux fora de escopo — permanece só com a
permissão de arquivo da Fase 1. Validação de campo (bancada Windows
AppLocker e macOS) pendente antes de aceitar o ciclo — ver `## Pendências`.

## Pendências

- [ ] Definir o próximo incremento (envio continua fora por decisão de
      segurança)
- [ ] Login via canal sem sessão gráfica interativa (SSH puro, tarefa
      agendada) não abre o navegador visivelmente — achado de campo do
      incremento 3, documentado em `docs/guias/instalar.md`, mas sem
      solução própria ainda. Considerar se algum incremento futuro precisa
      de um mecanismo alternativo pra esse cenário (ex.: exibir a URL como
      fallback se o navegador não responder em N segundos).
- [ ] **Endurecimento pós-auditoria, Fase 1 (incremento 4) deixou quatro
      lacunas conhecidas, não fechadas por essa fase** — conferir antes de
      assumir que estão resolvidas:
      1. Permissão restrita do token (0600) não tem teste com
         `SCRIBA_HOME` apontando para diretório de outro dono/grupo — só
         o caso de diretório pré-existente frouxo do mesmo usuário.
      2. `mail draft`/`mail reply` sem `--body-file` leem `stdin` sem
         timeout — um consumidor (agente via subprocesso) que não feche
         o descritor trava o comando indefinidamente. Mitigação futura:
         exigir marcador explícito pra ler de stdin, ou timeout na
         leitura.
      3. O listener de loopback do login (`_capture_callback_url`)
         continua vulnerável a um processo local consumindo a única
         `handle_request()` antes do navegador do usuário — só a
         exceção de state CSRF tem tratamento, a exaustão de requisição
         única não.
      4. Três testes em `tests/test_auth.py`
         (`test_is_authenticated_returns_false_when_tenant_is_common` e
         os dois vizinhos) passam pelo motivo errado — ausência de token
         salvo, não validação de tenant. Não provam a guarda de
         `TENANT_PROIBIDO`; se ela for removida, esses testes continuam
         verdes. Corrigir a fixture antes de confiar neles como
         regressão.
- [x] ~~Validação de campo da Fase 2 (jd-task #1077) antes de aceitar o
      ciclo 5~~ — feita em 29/09/2026, bancada Windows AppLocker (tenant
      `jedilabs123.onmicrosoft.com`) e macOS, os onze comandos de ponta a
      ponta nas duas plataformas, critérios 6 e 7 atendidos. Achado no
      caminho: os 3 testes de permissão de arquivo da Fase 1 falham no
      Windows real (`chmod` não é POSIX lá) — corrigidos com
      `skipif(sys.platform == "win32")`. Detalhe:
      `11-tarefas/20260929-validacao-de-campo-fase2-endurecimento.md`
      (fora deste repositório).
- [ ] **macOS: primeiro acesso ao item do Keychain por binário/caminho
      distinto pede senha do sistema; depois de aprovar ("sempre
      permitir"), fica silencioso — não confirmado com o binário de
      produção real.** Relato direto do Orlando (vendo a tela) na
      validação de campo de 29/09/2026: pediu senha "nos primeiros"
      comandos, depois parou de pedir. Consistente com a leitura do
      código: `msal_extensions.osx.Keychain` cria o item via
      `SecKeychainAddGenericPassword` sem lista de aplicativos confiáveis
      (`trustedApplications=None`), então o macOS pede aprovação (com
      opção "sempre permitir") na primeira vez que **cada identidade de
      processo distinta** tenta ler — e a sessão de validação usou várias
      formas de invocar (`uv run scriba ...`, `uv run python3 -c ...`),
      cada uma provavelmente contando como identidade própria. **Não
      medido ainda:** se o binário de produção único (`scriba` instalado
      via `pip install`, um só caminho) pede só uma vez por
      instalação/usuário, ou se pede de novo a cada nova versão instalada
      (caminho do binário muda?). Se for só uma vez por instalação, é UX
      aceitável (mesmo padrão de outros CLIs que usam Keychain) e só
      precisa de uma frase no guia de instalação avisando "primeiro
      comando pode pedir a senha do sistema — escolher "sempre permitir"";
      se pedir de novo a cada atualização, é fricção real a resolver.

## Referências

- [[docs/arquitetura.md]] — mapa estrutural do repo (mapa fino, isento — carga sob demanda)
- [[docs/explicacoes/visao-geral.md]] — o quê e por quê (quadrante explicação, carga sob demanda)
- [[docs/decisoes/]] — ADRs locais
