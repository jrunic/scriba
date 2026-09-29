---
id: 202609271715
projeto: scriba
tipo: guia
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: O que cada permissão concedida ao scriba cobre, e o que ela não impede — auditado contra o mecanismo real, não contra a intenção do produto.
dominios: [tecnologia]
tags: [guia, scriba, permissoes, seguranca]
---

# Permissões concedidas e o que elas não cobrem

Uma garantia de segurança vale pelo que ela **não** cobre, não só pelo que
promete. Este guia audita cada permissão contra o mecanismo real da lib
Microsoft Graph que o `scriba` usa — não contra a descrição da intenção do
produto.

## Os dois escopos que o código pede

Medido diretamente no código-fonte do `scriba` — não é uma lista teórica:

**`Mail.ReadWrite`**
- Cobre: ler mensagens da caixa de correio, e criar/editar rascunhos
  (incluindo rascunhos de resposta a mensagens existentes).
- Não impede: tecnicamente, este escopo permite ler, editar e apagar
  **qualquer** mensagem da caixa — não só as que o `scriba` cria. O
  `scriba` nunca chama a operação de enviar mensagem (`Mail.Send` nunca é
  solicitado — é decisão de segurança do produto, mudar isso exige uma
  decisão arquitetural registrada, não um ajuste de código direto), mas o
  escopo concedido pela conta permitiria isso se o código pedisse.

**`Calendars.ReadWrite`**
- Cobre: ler, criar e editar eventos em qualquer calendário que a conta
  autenticada tenha acesso de escrita — incluindo o calendário padrão e
  outros calendários da própria conta.
- Não impede: se a conta tiver acesso de editor a um calendário
  **compartilhado por outra pessoa**, este escopo permite ao `scriba`
  criar/editar eventos nesse calendário também — não é limitado ao
  calendário do próprio usuário.

## Os dois que aparecem, mas não são pedidos pelo código

**`offline_access`** — não está na lista de escopos que o código declara.
É um escopo reservado que o MSAL concede implicitamente para aplicações
públicas em fluxos delegados (como o authorization code + PKCE que o
`scriba` usa). É o que permite a sessão persistir sem pedir login a cada
uso — ver [reautenticação](reautenticacao.md). Na prática funciona como uma
permissão concedida, mesmo sem aparecer na lista que o código pede
explicitamente.

**`User.Read`** — não aparece em nenhuma chamada do código. Pode ou não
aparecer na tela de consentimento dependendo de como o app foi registrado no
portal do Entra pela organização que hospeda o app — quando presente, é
leitura do próprio perfil básico (nome, e-mail), sem escrita.

## O que o token em disco realmente é

**Em Windows e macOS**, o conteúdo do arquivo de token é protegido pelo
cofre de credenciais do sistema operacional (DPAPI/Keychain) — o arquivo,
sozinho, não é mais equivalente a acesso à conta; decifrar o conteúdo
exige rodar como o mesmo usuário do sistema operacional que autenticou
(a garantia é do SO, não do `scriba`).

**Em Linux**, essa proteção ainda não existe (achado F1 da auditoria de
segurança externa, Fase 2 parcial): o token de acesso e o de atualização
(`refresh_token`) ficam em texto puro, protegidos só por permissão de
arquivo (leitura/escrita restrita ao dono). **Esse arquivo, sozinho, é
equivalente a acesso à conta — sem precisar da senha — até ser
revogado.** Quem tiver acesso de leitura como o mesmo usuário do sistema
tem, na prática, o mesmo alcance que os dois escopos acima permitem.

## Resumo

| Escopo | Pedido pelo código? | Cobre | Não impede |
|---|---|---|---|
| `Mail.ReadWrite` | Sim | Ler mensagens, criar/editar rascunho e resposta | Ler/editar/apagar qualquer mensagem da caixa (não só rascunhos do scriba) |
| `Calendars.ReadWrite` | Sim | Ler/criar/editar eventos em calendários com acesso de escrita | Inclui calendários compartilhados por terceiros, não só os próprios |
| `offline_access` | Implícito (MSAL) | Sessão persiste sem novo login | Em Windows/macOS, o token em disco é protegido pelo cofre do SO; em Linux, ainda equivale a acesso sem senha até ser revogado |
| `User.Read` | Não, no código; possível no app registration | Leitura do próprio perfil | — |
