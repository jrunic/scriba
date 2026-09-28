---
id: 202609171610
projeto: scriba
tipo: referencia
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: Vocabulário do domínio do scriba — usar estes termos, nunca sinônimos.
dominios: [tecnologia]
tags: [glossario, scriba]
---

# GLOSSARIO.md — scriba

Vocabulário mínimo do domínio. O código e a documentação usam estes termos —
nunca sinônimo ("e-mail" no lugar de "mensagem", "compromisso" no lugar de
"evento").

- **Conta** — a identidade Microsoft 365 autenticada pelo usuário via
  authorization code flow com PKCE. Uma sessão do `scriba` opera sobre uma
  única conta por vez.
- **Mensagem** — um e-mail na caixa de correio da conta. `scriba mail
  search`/`read` operam sobre mensagens.
- **Rascunho** — uma mensagem criada mas não enviada, visível na pasta
  Rascunhos do Outlook. `scriba mail draft` cria rascunho; o `scriba` nunca
  envia mensagem.
- **Evento** — um item da agenda de um calendário da conta. `scriba cal
  list`/`read`/`create` operam sobre eventos.
- **Calendário** — contêiner de eventos, identificado por nome e id
  próprios. Toda conta tem um calendário padrão; pode ter outros.
  `scriba cal calendars` lista os calendários da conta; os demais comandos
  `cal` aceitam `--calendar` pra apontar pra um específico, e usam o padrão
  quando omitido.
- **Resposta** — um rascunho vinculado a uma mensagem existente (distinto
  de rascunho de mensagem nova), pré-preenchido pelo Graph com
  destinatário/assunto/citação. `scriba mail reply` cria resposta; como
  todo rascunho, nunca é enviada automaticamente.
