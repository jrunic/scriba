---
id: 202609272000
projeto: scriba
tipo: nota
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: Histórico de versões do scriba, formato Keep a Changelog.
tags: [changelog, scriba]
---

# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [0.2.0] — 2026-09-28

### Alterado

- **Autenticação trocada de device code flow para authorization code flow
  com PKCE, via loopback local** — device code passou a ser bloqueado por
  padrão pelo Microsoft Entra Security Defaults em todo tenant criado a
  partir de 01/07/2026 (`AADSTS530035`/`BlockedBySecurityDefaults`), o que
  tornava `auth login` inutilizável em qualquer tenant novo. `scriba auth
  login` agora abre o navegador padrão da máquina sozinho — o usuário só
  confirma o login e o consentimento, sem copiar URL nem digitar código.
  Detalhe da decisão: ADR
  `20260928-fluxo-de-auth-troca-device-code-por-auth-code-pkce.md`.

### Corrigido

- Callback de autenticação com `state` incorreto (requisição espúria no
  listener local, ou URL de callback corrompida) não derruba mais o
  comando com traceback — retorna erro legível e código de saída 1.

### Segurança

- App registration do `scriba` (e de qualquer app cliente que use este
  fluxo) precisa ter o Redirect URI `http://localhost` (sem porta fixa)
  cadastrado — pré-condição nova, documentada em
  [instalar](docs/guias/instalar.md) e em `CONTEXTO.md`.
- Login por um canal sem sessão gráfica interativa (SSH puro, tarefa
  agendada) não funciona — o navegador não abre visivelmente. Documentado
  em [instalar](docs/guias/instalar.md), achado de validação de campo na
  bancada Windows.

## [0.1.0] — 2026-09-27

Primeira versão publicada.

### Adicionado

- Autenticação delegada via device code flow (MSAL), sem client secret:
  `auth login`, `auth status`, `auth logout`.
- E-mail: `mail read`, `mail search` (filtros por não-lido, remetente,
  assunto, anexo, importância, intervalo de data), `mail draft` (rascunho
  novo), `mail reply`/`--reply-all` (rascunho de resposta a mensagem
  existente).
- Agenda: `cal list`, `cal read`, `cal create`, `cal calendars` (lista
  calendários da conta); `--calendar` em `list`/`read`/`create` para operar
  em calendário não-padrão, por nome ou id.
- Config e token em disco seguindo XDG Base Directory (`SCRIBA_HOME` como
  válvula de escape).
- Quatro guias em `docs/guias/`: verificação de prontidão da organização,
  instalação (com trilha separada para agente de IA e para humano),
  reautenticação, e permissões/limites concedidos ao app.
- CI (GitHub Actions): lint, checagem de formatação e suíte de testes em
  todo push/PR para `main`.

### Segurança

- `Mail.Send` nunca é solicitado nem implementado — o `scriba` cria
  rascunhos e respostas, nunca envia. Mudar isso é decisão arquitetural
  registrada (ADR), não ajuste de código direto.
- Escopos delegados pedidos explicitamente pelo app:
  `Mail.ReadWrite`, `Calendars.ReadWrite`. Ver
  [permissões e limites](docs/guias/permissoes-e-limites.md) para o que cada
  um cobre e o que não impede.
