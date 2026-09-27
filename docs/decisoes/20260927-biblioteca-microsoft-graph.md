---
id: 202609270950
projeto: scriba
tipo: decisao
status: aprovado
data: 2026-09-27
escopo: repo:scriba
plataforma: "*"
dominios: [tecnologia]
descricao: "ADR — scriba usa a lib O365 sobre MSAL para acesso ao Microsoft Graph, com escopo de mensagem explícito em vez do preset message_all"
tags: [adr, decisao, microsoft-graph, o365, msal]
---

# ADR — biblioteca de acesso ao Microsoft Graph

## Status

Aprovado em 2026-09-27.

## Contexto

O `scriba` precisa autenticar via device code flow (permissões delegadas,
sem client secret) e operar sobre mensagens (leitura, criação de rascunho —
nunca envio) e eventos de calendário (leitura, listagem, criação) do
Microsoft Graph.

Três caminhos foram avaliados: SDK oficial `msgraph-sdk` (gerado via Kiota
a partir da spec OpenAPI do Graph), Microsoft Graph PowerShell SDK, e a lib
comunitária `O365` (wrapper Pythonic sobre `msal` e o Graph).

## Decisão

`O365` sobre `msal`. Razões:

- API de alto nível (query builder, objetos) reduz código próprio a manter,
  frente ao SDK oficial gerado, que é verboso e boilerplate-heavy.
- Ativa e mantida: repositório com milhares de estrelas, commits e releases
  contínuos, licença MIT.
- Um projeto de código aberto equivalente (mesma lib, device code flow,
  leitura de e-mail, leitura/criação/listagem de evento) prova em campo
  parte do escopo — mas não a criação de rascunho, que é a operação central
  e nova deste projeto.

## O que a evidência de campo NÃO cobre

O caso de referência usado na avaliação não implementa rascunho — os
comandos dele são busca, leitura, envio e resposta, e ele solicita
`Mail.Send`. A criação de rascunho sem envio foi validada empiricamente
neste repositório em **27/09/2026**, via `scripts/rascunho_smoke.py` contra
um tenant Microsoft 365 Business Standard real (trial de 30 dias) — não por
reuso de prova alheia, e não pelo unit test mockado (que só valida a
fiação da CLI, não o comportamento real da lib contra o Graph).
`save_draft()` retornou `True` e o rascunho foi confirmado visualmente na
pasta Rascunhos do Outlook da conta autenticada.

## Risco conhecido e mitigado

A lib `O365` tem um preset de conveniência (`message_all`) que agrupa
`Mail.ReadWrite` com `Mail.Send`. Este projeto nunca usa esse preset — o
escopo de mensagem é passado explícito (`Mail.ReadWrite`), e um teste
automatizado pina a lista de escopos Graph resultantes, afirmando que
`Mail.Send` nunca está presente.

## Alternativas recusadas

- **`msgraph-sdk` oficial:** first-party, mas verboso; sem prova de campo
  própria melhor que a do `O365` no escopo deste projeto. Permanece
  alternativa caso `O365` pare de ser mantida.
- **Microsoft Graph PowerShell SDK:** exigiria PowerShell como segunda
  dependência de runtime, ao lado do Python.
- **`cli-microsoft365`:** não tem comando de criação de rascunho.

## Referências

- github.com/O365/python-o365
- Caso de referência (device code flow, leitura de e-mail, calendário):
  github.com/mhattingpete/outlook-cli
