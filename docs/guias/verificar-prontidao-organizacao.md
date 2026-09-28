---
id: 202609271700
projeto: scriba
tipo: guia
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: Checklist para saber se a organização está pronta para o scriba, e o que fazer quando não está.
dominios: [tecnologia]
tags: [guia, scriba, instalacao, prontidao]
---

# Verificar se a organização está pronta para o scriba

Guia para o agente de IA que opera em nome do usuário, e para o usuário
consultar junto com a TI da própria organização. Antes de instalar, vale a
pena confirmar seis pontos — cada "não" tem uma ação concreta, não é motivo
para desistir.

## O checklist

| # | Pergunta | Como checar |
|---|---|---|
| 1 | A conta usa Microsoft 365/Exchange Online (não Gmail, não M365 sem caixa de e-mail)? | Perguntar à TI, ou tentar abrir o Outlook na web com a conta. |
| 2 | O usuário pode consentir sozinho a um app de terceiro, ou só um admin pode? | Perguntar à TI: "usuários podem consentir a aplicativos OAuth, ou isso é restrito a administradores?" |
| 3 | A política de acesso condicional (Conditional Access) permite sessão persistente? | Perguntar à TI: existe uma política de "sign-in frequency" curta (força login a cada poucas horas)? |
| 4 | Existe antivírus/EDR que bloqueia scripts Python ou executáveis não assinados? | Testar rodando `python --version` num terminal da máquina em questão. |
| 5 | Existe "app governance" ou política de terceiros restringindo quais apps OAuth podem ser autorizados? | Perguntar à TI: "existe uma lista de apps permitidos, ou qualquer app pode pedir consentimento?" |
| 6 | O pacote consegue chegar na máquina (rede alcança github.com, e `git` está instalado)? | Testar `git --version` e tentar abrir github.com no navegador da máquina. |

## O que fazer quando a resposta é "não"

| Pergunta | Se "não" | Ação |
|---|---|---|
| 1 | Não é M365/Exchange Online | O scriba não se aplica — ele fala só com o Microsoft Graph. Não há alternativa dentro do produto. |
| 2 | Só admin consente | Pedir para a TI aprovar o consentimento uma vez (o app pede só `Mail.ReadWrite` e `Calendars.ReadWrite`, nunca envio de e-mail — ver [permissões e limites](permissoes-e-limites.md)). Depois de aprovado, qualquer usuário do tenant pode autenticar. |
| 3a | Sign-in frequency curta | Perguntar login de novo com mais frequência é esperado nesse caso — não é bug. Ver [reautenticação](reautenticacao.md). |
| 4 | Antivírus/EDR bloqueia Python | Pedir liberação do interpretador Python e do diretório de instalação à TI. |
| 5 | App governance restrito | Pedir à TI para adicionar o `client_id` do app à lista de apps permitidos. |
| 6 | Rede/git indisponível | Baixar o repositório como arquivo zip por outro meio (pendrive, e-mail) e instalar localmente a partir dele — ver [instalação](instalar.md). |

## O critério real de "pronto"

Nenhuma resposta ao checklist substitui a confirmação real. "Pronto" significa
rodar, na máquina de destino:

```
scriba auth login --client-id <client-id>
scriba auth status
```

E ver `OK: Autenticado.` na saída do segundo comando. Um checklist todo "sim"
mas sem essa confirmação ainda não é prontidão confirmada — só ausência de
bloqueio conhecido.
