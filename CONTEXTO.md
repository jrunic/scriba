---
id: 202609171425
projeto: scriba
tipo: index
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: Padrões técnicos canônicos e restrições do repo scriba — carga default da sessão.
tags: [contexto, dev-skills, Python]
---

# CONTEXTO.md — scriba

## Propósito

[A ser preenchido pela primeira spec via dev-02-escreve-spec.]

## Agente padrão

**Tech** (SRE Agentic) — guardião deste repositório. Modo de atuação: Código + SRE Agentic
(Autocura Assistida). Outros agentes podem ler/contribuir; mudanças estruturais passam por Tech.

## Stack

- **Linguagem:** Python
- **Framework:** [a definir]
- **Banco:** [a definir]
- **Deploy:** [a definir]

## Padrões Técnicos

### Naming

[Preenchido pela skill dev-01-define-padroes conforme convenção da stack.
Ver PADROES-COMUNIDADE.md da skill para tabela completa.]

### Linguagem

- **Slug do repo/CLI:** [definir conforme a audiência do artefato]
- **Identificadores no código:** convenção da stack (inglês para Python/JS/Go)
- **Comentários inline:** pt-BR
- **Commits:** tipo conventional em inglês (`feat:`, `fix:`...), descrição em pt-BR

### Segredos

- **Onde:** [jedi-secrets / .env local / GCP Secret Manager / ...]
- **Convenção de nomes:** [definir]

### Bibliotecas

- **Política:** [livre / requer ADR / lista permitida]
- **Atuais:** [lista inicial]

### Estrutura

```
CONTEXTO.md GLOSSARIO.md — contratos vivos (raiz)
docs/arquitetura.md — mapa fino
docs/decisoes/  — ADRs locais
docs/dominio/   — modelo de domínio (neg-02)
docs/{tutoriais,guias,referencias,explicacoes}/ — quadrantes Diátaxis (ADR 20260620)

src/scriba/         — [descrever]
src/scriba/commands/         — [descrever]
tests/         — [descrever]
scripts/         — [descrever]
```

### Testes

- **Framework:** [a definir]
- **Pasta:** `tests/`

### Build/Run

- **Setup:** [comando]
- **Testes:** [comando]
- **Run:** [comando]
- **Build:** [comando]

### Lint/Format

- **Lint:** [comando]
- **Format:** [comando]

## Onde o trabalho acontece

**O trabalho de desenvolvimento acontece fora deste repositório**, nos
documentos internos do autor.

| Artefato | Lar canônico |
|---|---|
| Roadmap de ciclos, spec, plano | fora deste repositório |
| Arquivo de apoio de tarefa, diário de sessão | fora deste repositório |
| Discussão de negócio, issue | fora deste repositório |
| **Código, testes, migrations** | **este repo** |
| **Documentação do produto** (Diátaxis) | **este repo**, `docs/` |
| **Modelo de domínio, GLOSSARIO.md** | **este repo** |
| **ADR de contrato da ferramenta** | **este repo**, `docs/decisoes/` |
| **README, CHANGELOG** | **este repo** |

**As skills leem esta seção** em vez de inferir por visibilidade.

## Leitura obrigatória antes de spec/plano

- `docs/arquitetura.md` — mapa estrutural
- `GLOSSARIO.md` — vocabulário do domínio (usar estes termos, nunca sinônimos)
- `roadmap.md` — incremento ativo e fronteiras (contrato do Passo 0 do dev-02)
- `docs/dominio/` — modelo formal dos contextos que o trabalho toca

## Restrições

Hard limits sempre relevantes durante a sessão (ADR `20260609-eliminacao-do-84-ia.md` — substitui antigo `docs/84-ia/restricoes.md`).

- **Runner de testes canônico:** [comando — ex: `.venv/bin/pytest`]
- **Idioma da saída para humano:** pt-BR
- **Comentários inline:** pt-BR
- **Slug do repo/CLI:** [definir conforme a audiência do artefato]
- **Implementação que contradiz `docs/dominio/` ou `GLOSSARIO.md` atualiza o doc no mesmo commit;** divergência que vira decisão arquitetural → dev-07-cria-adr (ADR `20260705-familia-neg-skills-negocio`)
- [Instanciar por CÓPIA as Restrições do documento de padrões da classe de app, quando houver — herança explícita]
- [Adicionar regras com histórico ou alto custo de violar — não documentar o óbvio]


## Decisões Herdadas (explícitas)

- Kebab-case em paths; identificadores seguem a convenção da stack
- Comentários inline em pt-BR
- Sem segredos no repositório
- Sem comandos destrutivos sem confirmação
- Conhecimento destilado em `docs/`; restrições em `CONTEXTO.md`

## Decisões Locais Divergentes

[Listar onde este projeto diverge de regras globais. Cada divergência idealmente tem ADR em docs/decisoes/.]

## Estado Atual

Projeto criado em 2026-09-17 via `dev-01-define-padroes`. Aguardando primeira spec via `dev-02-escreve-spec`.

## Pendências

- [ ] Primeira spec via dev-02-escreve-spec
- [ ] Primeiro plano via dev-03-escreve-plano
- [ ] Setup de testes (framework + pasta + primeiro teste exemplar)

## Referências

- [[docs/arquitetura.md]] — mapa estrutural do repo (mapa fino, isento — carga sob demanda)
- [[docs/explicacoes/visao-geral.md]] — o quê e por quê (quadrante explicação, carga sob demanda)
- [[docs/decisoes/]] — ADRs locais
