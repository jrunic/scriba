---
id: 202609271710
projeto: scriba
tipo: guia
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: Por que a autenticação do scriba pode expirar e pedir login de novo, e o que é esperado.
dominios: [tecnologia]
tags: [guia, scriba, autenticacao, token]
---

# Por que o scriba às vezes pede login de novo

Este guia é sobre o **mecanismo geral** — não é o registro de um incidente
específico. Se o `scriba` pedir `scriba auth login` de novo, isso pode ser
normal ou pode ser sintoma de uma política da organização; este guia ajuda a
diferenciar as duas coisas sem inventar uma causa que não foi confirmada.

## O que acontece por baixo, em uso normal

Quando você autentica uma vez, o `scriba` guarda em disco um token de acesso
e um token de atualização (`refresh_token`). Antes de cada comando, ele tenta
renovar o token de acesso sozinho usando o token de atualização — sem pedir
login de novo. Isso acontece de forma silenciosa; **em uso diário ou semanal,
não se espera pedir login outra vez**.

## O que força uma nova autenticação

Nenhuma delas é falha de segurança do `scriba` — são limites do mecanismo ou
decisões de terceiros fora do alcance do produto:

- **Inatividade muito longa.** Existe uma janela comum citada para tokens de
  atualização (algo na casa de meses), mas ela não é uma garantia fixa nem
  documentada como número exato pela Microsoft — tratar como referência, não
  promessa.
- **Política de Conditional Access do tenant** (a organização do usuário, não
  o `scriba`) — uma configuração de "sign-in frequency" pode forçar login a
  cada X horas/dias, independente do refresh token existir. Isso é decisão da
  TI da organização; o `scriba` não tem como contornar.
- **Revogação de consentimento** — se um administrador revogar o
  consentimento do app (via Entra), ou o próprio usuário revogar o acesso
  do app nas configurações de aplicativos da sua conta Microsoft, o token
  para de funcionar.
- **Reset de senha da conta** — dependendo da política do tenant, isso pode
  invalidar sessões existentes.

## O que fazer quando pedir login de novo

É o comportamento esperado do produto, não um erro — rodar `scriba auth
login` de novo resolve. Se isso estiver acontecendo com frequência incomum
(todo dia, por exemplo), a causa mais provável é uma política de Conditional
Access do tenant — ver o [checklist de prontidão](verificar-prontidao-organizacao.md),
pergunta 3, e reportar a suspeita à TI da organização para confirmar.

## O que não afirmamos aqui

Este guia não promete um número de dias exato antes de expirar, e não
descreve nenhum episódio específico de reautenticação observada — o
mecanismo é auditável no código (`O365`/MSAL), mas a causa exata de uma
reautenticação individual depende do histórico daquela máquina/conta
específica, que este guia não tem como conhecer de antemão.
