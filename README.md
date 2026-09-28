---
id: 202609171425
projeto: scriba
tipo: nota
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: README do repo scriba — entrypoint humano.
tags: [readme, Python]
---

# scriba

CLI que dá a um agente de IA acesso a e-mail e agenda do Microsoft 365 via
Microsoft Graph — leitura de mensagens, criação de rascunho e resposta, e
leitura/criação de eventos de calendário (múltiplos calendários, não só o
padrão). Autenticação delegada por authorization code flow com PKCE (login
pelo navegador), sem client secret.
Nunca envia e-mail — decisão de segurança, não limitação técnica.

## Guias

- [Verificar se a organização está pronta](docs/guias/verificar-prontidao-organizacao.md)
- [Cadastrar e configurar o app no Microsoft Entra](docs/guias/cadastrar-app-entra.md) — para a equipe de TI
- [Instalar](docs/guias/instalar.md)
- [Por que pede login de novo](docs/guias/reautenticacao.md)
- [Permissões e limites](docs/guias/permissoes-e-limites.md)

## Para agentes e desenvolvedores

- `CONTEXTO.md` — padrões técnicos e restrições (comece aqui)
- `GLOSSARIO.md` — linguagem do domínio
- `roadmap.md` — incrementos e estado
- `CHANGELOG.md` — histórico de versões
- `docs/` — arquitetura, domínio, decisões e documentação (Diátaxis)
