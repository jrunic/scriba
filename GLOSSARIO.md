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

- **Conta** — a identidade Microsoft 365 autenticada pelo usuário via device
  code flow. Uma sessão do `scriba` opera sobre uma única conta por vez.
- **Mensagem** — um e-mail na caixa de correio da conta. `scriba mail
  search`/`read` operam sobre mensagens.
- **Rascunho** — uma mensagem criada mas não enviada, visível na pasta
  Rascunhos do Outlook. `scriba mail draft` cria rascunho; o `scriba` nunca
  envia mensagem.
- **Evento** — um item da agenda (calendário padrão) da conta. `scriba cal
  list`/`read`/`create` operam sobre eventos.
