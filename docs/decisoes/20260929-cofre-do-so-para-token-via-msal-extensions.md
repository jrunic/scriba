---
id: 202609291113
projeto: scriba
tipo: decisao
status: aprovado
data: 2026-09-29
escopo: repo:scriba
plataforma: "*"
dominios: [tecnologia]
descricao: ADR — cofre do sistema operacional para o token via msal-extensions
tags: [adr, decisao, seguranca, dependencia]
---

# ADR — Cofre do sistema operacional para o token, via `msal-extensions`

## Status

Aprovado — 2026-09-29. Decisão de dependência técnica, mesmo padrão das
duas ADRs locais anteriores deste repo (escolha de biblioteca, troca de
fluxo de auth): evidência empírica medida antes da aprovação (pré-condição
2 do apoio da jd-task #1077, ver Referências), não promessa de
documentação. A validação de campo com tenant real (pré-condição 3, prazo
22/10/2026) segue pendente — não bloqueia esta ADR, é gate do `dev-04`.

## Contexto

Uma auditoria de segurança externa apontou que o token OAuth do `scriba`
(access token, refresh token, id token, dados da conta) fica em JSON puro em
disco, sem proteção do cofre de credenciais do sistema operacional (DPAPI no
Windows, Keychain no macOS, libsecret no Linux). Quem tiver leitura no
sistema de arquivos do usuário lê o token inteiro.

A biblioteca cliente do Graph já usada pelo projeto (`O365`, sobre `MSAL`) já
expõe o ponto de extensão para isso: `BaseTokenBackend` tem um atributo
opcional `cryptography_manager`, e os métodos internos `serialize()`/
`deserialize()` — chamados por `FileSystemTokenBackend.save_token()`/
`load_token()` — aplicam `.encrypt(data)`/`.decrypt(data)` nesse objeto
quando ele não é `None`, antes de escrever/ler o arquivo. A peça que falta é
fornecer esse objeto — não reescrever o backend.

A política de bibliotecas do `CONTEXTO.md` deste repo exige ADR local para
dependência nova não trivial/transitiva, dado que o projeto opera sobre dado
sensível de terceiros (e-mail/agenda). Daí esta ADR, antes de qualquer
código.

## Decisão

1. **Adotar `msal-extensions`** como dependência nova, usada só como fonte
   do primitivo de criptografia por plataforma — não como gerenciador de
   arquivo (não trocamos o `FileSystemTokenBackend` nem o layout de token em
   XDG já documentado no `CONTEXTO.md`).
2. **No Windows**, o adaptador embrulha
   `msal_extensions.windows.WindowsDataProtectionAgent` — `.protect(data)`
   vira `encrypt()`, `.unprotect(data)` vira `decrypt()`. Medido nesta
   sessão, não é leitura de documentação: instalação limpa sob
   `koine-restrito` (Python 3.14.7 ARM64, AppLocker — o cenário mais restrito
   já medido na frota para este projeto) e round-trip real — o arquivo
   gravado por `protect()` não contém o JSON em claro, e `unprotect()`
   devolve o conteúdo original byte a byte.
3. **Em macOS/Linux**, o formato do `msal-extensions` diverge do par
   `encrypt`/`decrypt`: `msal_extensions.osx.Keychain` expõe
   `set_generic_password`/`get_generic_password` (armazenamento chave-valor
   por serviço/conta), e o backend de Linux (`libsecret`) segue o mesmo
   padrão. O adaptador nessas plataformas embrulha o blob serializado
   inteiro como um único item do cofre (`set_generic_password` em
   `encrypt()`, devolvendo um marcador; `get_generic_password` em
   `decrypt()`, ignorando o marcador). Não medido em campo nesta ADR — só a
   forma da API foi confirmada por inspeção. A bancada do cliente que motivou
   a auditoria é Windows; medir macOS/Linux fica no plano de execução
   (`dev-03`/`dev-04`), não bloqueia esta decisão.
4. **Rejeitar `keyring`** como alternativa (ver Alternativas Consideradas).

## Consequências

### Positivas

- Fecha a lacuna do achado de auditoria sem reescrever o backend de token
  nem o contrato de onde o token mora (`$XDG_STATE_HOME/scriba/token`
  continua valendo — só o conteúdo do arquivo passa a ser opaco).
- O ponto de extensão (`cryptography_manager`) já existe na lib atual — o
  código novo é um adaptador pequeno por plataforma, não uma reescrita.
- Validado sob a condição mais hostil já medida para este projeto
  (AppLocker, Python 3.14 ARM64) — reduz o risco de a Fase 2 descobrir tarde
  que a dependência não instala no ambiente real do cliente.

### Negativas

- Três adaptadores de plataforma em vez de um — Windows usa
  `protect`/`unprotect` direto; macOS/Linux precisam de uma camada extra
  para encaixar o formato chave-valor no Protocol `encrypt`/`decrypt` que o
  `O365` espera. Mais superfície de código e de teste do que uma lib com API
  uniforme teria.
- Dependência nova de terceiro (mais `msal`, `cryptography`, `cffi`
  transitivas) — mantida sob a mesma disciplina de pin de versão do
  `CONTEXTO.md`.
- macOS/Linux ficam sem validação de campo até o `dev-04` desta fase —
  risco conhecido, não medido, declarado aqui em vez de presumido benigno.

### Implementação

- Fase 2 do incremento de endurecimento pós-auditoria (jd-task #1077,
  ciclo separado da Fase 1 no `roadmap.md` da pasta de trabalho).
- Adaptador Windows primeiro (bancada do cliente); macOS/Linux entram no
  mesmo incremento, com validação de campo própria antes do `dev-09`.
- Validação de campo com tenant real precisa rodar antes de 22/10/2026
  (expiração do tenant de teste, jd-task #1055) — gate declarado no apoio da
  tarefa, não desta ADR.

## Escopo

Aplica-se só à proteção em repouso do arquivo de token do `scriba`. Não
aplica-se a: revogação de sessão no provedor de identidade (fora de escopo
do projeto — o usuário revoga na própria conta Microsoft), nem a qualquer
mudança no fluxo de autenticação (authorization code + PKCE, já decidido em
ADR anterior), nem à Fase 1 (achados sem dependência nova, ciclo separado).

## Alternativas Consideradas

### `keyring`

API uniforme entre as três plataformas (`set_password`/`get_password`/
`delete_password`, backend resolvido automaticamente — Windows Credential
Locker, macOS Keychain, SecretService/libsecret no Linux). Medido nesta
sessão em macOS: instala, grava, lê e apaga uma credencial de teste sem
fricção.

Rejeitado: a API do `keyring` é de armazenamento chave-valor completo, não
de criptografia de um blob que outro código grava em arquivo — usá-la exige
descartar o `cryptography_manager` do `O365` e mover o próprio token inteiro
para dentro do cofre, abandonando o layout de arquivo em XDG que o
`CONTEXTO.md` já documenta como contrato deste repo. Isso muda a arquitetura
de armazenamento, não só adiciona uma proteção — escopo maior do que o
achado da auditoria pede. Reavaliar se um achado futuro exigir abandonar o
arquivo de token de vez (não é o caso aqui).

### Reescrever o backend de token sem dependência nova (DPAPI/Keychain via
binding próprio, sem `msal-extensions`)

Rejeitado: reimplementar chamada nativa a DPAPI (Windows), Keychain
(macOS) e libsecret (Linux) na mão é justamente o trabalho que
`msal-extensions` já resolve e testa — reescrever do zero é mais superfície
de manutenção pelo mesmo resultado, e perde a validação de campo que a lib
já tem no ecossistema MSAL.

### Não fazer nada (aceitar o risco como está)

Rejeitado: é o achado F1 da auditoria, classificado como risco real pelo
avaliador externo — token completo (incluindo refresh token, que renova
acesso por meses) em texto puro em disco, legível por qualquer processo com
permissão de leitura do usuário.

## Referências

- Apoio da jd-task #1077, seção "Spike de bancada — 29/09/2026" —
  `13-processos/manter-scriba/11-tarefas/20260929-1077-endurecimento-p-s-auditoria-do-scriba-fase-2-cofre-do-so-par.md`
  (fora deste repositório — documentos internos do autor).
- ADR local anterior de escolha de biblioteca:
  `docs/decisoes/20260927-biblioteca-microsoft-graph.md`.
- ADR local anterior de fluxo de autenticação:
  `docs/decisoes/20260928-fluxo-de-auth-troca-device-code-por-auth-code-pkce.md`.
- `CONTEXTO.md` §Bibliotecas e §Estrutura (contrato de XDG para token).
