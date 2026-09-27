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
