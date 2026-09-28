---
id: 202609282100
projeto: scriba
tipo: guia
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: Como a equipe de TI cadastra e configura o aplicativo do scriba no Microsoft Entra, para liberar o acesso de um usuário da organização.
dominios: [tecnologia]
tags: [guia, scriba, entra, instalacao]
---

# Cadastrar e configurar o aplicativo do scriba no Microsoft Entra

Este guia é para quem administra o Microsoft Entra (Azure AD) da organização
— normalmente a equipe de TI. Ele cobre o cadastro único que libera o
`scriba` para um usuário autenticar e acessar o próprio e-mail e agenda.

## O que este cadastro autoriza, e o que não autoriza

- O `scriba` lê mensagens, cria rascunhos e respostas (nunca envia
  mensagem), e lê/cria eventos de calendário — só da conta do usuário que
  fizer login, nunca de outras contas da organização.
- Não usa senha nem client secret. A autenticação é feita pelo próprio
  usuário, no navegador, com a conta Microsoft dele — o mesmo fluxo de
  login que ele já usa no Outlook.
- Este cadastro, sozinho, não dá a ninguém acesso a nada. Ele só declara
  quais permissões o aplicativo pode pedir. O usuário aprova (ou a
  organização aprova por ele, dependendo da política de consentimento) no
  primeiro login.

## Passo 1 — Criar o registro do aplicativo

No [Microsoft Entra admin center](https://entra.microsoft.com):

1. **App registrations** → **New registration**.
2. **Name**: qualquer nome reconhecível (ex.: `scriba`).
3. **Supported account types**: "Accounts in this organizational directory
   only" — a menos que exista motivo específico para permitir outras
   organizações.
4. Deixe o campo de Redirect URI em branco aqui — ele é configurado no
   próximo passo.
5. **Register**.

## Passo 2 — Configurar o tipo de cliente e o Redirect URI

Dentro do aplicativo recém-criado:

1. **Authentication** → aba **Redirect URI configuration** → **Add
   Redirect URI**.
2. **Platform**: **Mobile and desktop applications**.
3. **Redirect URI**: `http://localhost` — exatamente assim, **sem porta**.
   O `scriba` usa uma porta local diferente a cada login; o Microsoft Entra
   aceita qualquer porta quando o valor cadastrado não tem porta nenhuma.
4. Ainda em **Authentication**, aba **Settings**: confirme que **Allow
   public client flows** está **Enabled**. Sem isso, o login falha mesmo
   com o Redirect URI certo.

## Passo 3 — Conceder as permissões da API

1. **API permissions** → **Add a permission** → **Microsoft Graph** →
   **Delegated permissions**.
2. Adicionar:
   - `Mail.ReadWrite`
   - `Calendars.ReadWrite`
3. **Não é preciso adicionar** `offline_access` nem `openid`/`profile` — o
   Microsoft Entra concede esses automaticamente para este tipo de
   aplicativo.
4. Se a política da organização exigir aprovação de administrador para
   permissões novas: clique em **Grant admin consent for
   `<organização>`**. Se os usuários podem consentir sozinhos, este passo
   não é necessário — cada usuário aprova no próprio primeiro login.

## O que este cadastro nunca deve ter

- **Nenhum client secret.** O `scriba` não usa e nunca vai pedir um. Se
  alguém pedir um client secret para configurar o `scriba`, é sinal de
  configuração errada.
- **Nenhuma permissão de envio de e-mail** (`Mail.Send`). O `scriba` cria
  rascunhos e respostas; quem envia é sempre a pessoa, dentro do Outlook.
  Se `Mail.Send` aparecer na lista de permissões pedidas, é sinal de que
  o aplicativo cadastrado não é o `scriba` — ou de uma versão alterada
  dele.

## Sobre políticas de segurança da organização

Se a organização usa **Padrões de Segurança (Security Defaults)** ou
**Conditional Access**: o fluxo de login que o `scriba` usa (authorization
code com PKCE, pelo navegador) **não é bloqueado** por essas políticas —
diferente de fluxos mais antigos de "digitar um código", que a Microsoft
passou a bloquear por padrão em tenants novos. Nenhuma exceção ou ajuste de
política é necessário para o `scriba` funcionar.

## Repassar ao usuário (ou a quem for configurar o `scriba` para ele)

Depois do cadastro, dois valores da tela **Overview** do aplicativo:

- **Application (client) ID**
- **Directory (tenant) ID**

Nenhum dos dois é segredo — são identificadores, não credenciais. Repassar
por qualquer canal (e-mail, chat) é seguro.

## Como revogar o acesso

- **Revogar de um usuário específico**: **Enterprise applications** →
  localizar o aplicativo → **Users and groups** ou a sessão do usuário em
  **Users** → **Sign-in logs**, ou simplesmente pedir que o usuário revogue
  o próprio consentimento (conta Microsoft → Privacidade → Aplicativos e
  serviços conectados).
- **Revogar por completo** (todos os usuários): **App registrations** →
  localizar o aplicativo → **Delete**. Todos os tokens emitidos param de
  funcionar.
