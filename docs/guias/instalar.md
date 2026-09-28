---
id: 202609271705
projeto: scriba
tipo: guia
escopo: repo:scriba
plataforma: "*"
status: ativo
descricao: Passo a passo de instalação do scriba, com trilha separada para o agente de IA e para o humano.
dominios: [tecnologia]
tags: [guia, scriba, instalacao]
---

# Instalar o scriba

O `scriba` ainda não está publicado no PyPI. A instalação hoje é por clonar o
repositório e instalar localmente — se isso mudar, este guia é atualizado com
o comando novo.

Duas trilhas abaixo: uma para o agente de IA que executa os passos técnicos,
outra para o humano que só faz a parte que só ele pode fazer.

## Trilha do agente

Cada passo tem o comando exato e a saída esperada. Se a saída divergir do
esperado, o passo indicado resolve — não improvisar.

**1. Confirmar Python 3.12+**

```
python3 --version
```
Esperado: `Python 3.12` ou superior. Se faltar ou for anterior, instalar
Python 3.12+ está fora deste guia — resolver com a distribuição do sistema
operacional em questão antes de continuar.

**2. Clonar e instalar**

```
git clone https://github.com/jrunic/scriba.git
cd scriba
pip install --user .
```
Esperado: instalação sem erro, terminando com `Successfully installed scriba-<versão>`.

Se `git` não estiver disponível ou a rede não alcançar o GitHub (ver
[checklist de prontidão](verificar-prontidao-organizacao.md), pergunta 6):
baixar o repositório como zip por outro meio, extrair, e rodar
`pip install --user .` de dentro da pasta extraída — o restante do guia
segue igual.

Em Python gerenciado pelo sistema (comum em macOS com Homebrew, ou Linux com
Python de distro), `pip install --user` pode recusar com
`error: externally-managed-environment`. Quando isso acontecer, criar um
ambiente virtual dedicado (`python3 -m venv .venv-scriba && .venv-scriba/bin/pip
install .`) é o caminho seguro — os comandos abaixo então rodam com o
Python desse ambiente (`.venv-scriba/bin/scriba` em vez de `scriba`), não com
`--break-system-packages`.

**3. Localizar o executável (importante em Windows)**

Em Windows, `pip install --user` frequentemente não coloca o script no PATH.
Confirmar antes de seguir:

```
scriba --version
```

Se der `scriba não é reconhecido como um comando`, o script foi instalado mas
não está no PATH — localizar o executável e usar o caminho completo dali em
diante (típico: `%APPDATA%\Python\Python312\Scripts\scriba.exe`; `pip`
avisa esse caminho exato na saída do passo 2, procurar a linha
`WARNING: The script scriba.exe is installed in ...`). Em Linux/macOS o
mesmo problema ocorre se `~/.local/bin` não estiver no PATH — mesma solução,
caminho completo até resolver o PATH.

Quando não houver executável instalado em lugar nenhum que se consiga
localizar (medido nesta sessão: `python -m scriba` **não funciona** — o
pacote não expõe `__main__`, e devolve `No module named scriba.__main__`), a
alternativa real é chamar o app Typer diretamente:
```
python3 -c "from scriba.main import app; app()" --version
```
Isso funciona porque o Python enxerga o pacote instalado independente do
script de linha de comando estar no PATH ou não.

**Nos passos 4-6 abaixo, `scriba <comando>` é atalho** — trocar pelo que
funcionou neste passo (caminho completo do executável, `.venv-scriba/bin/scriba`,
ou o `python3 -c "from scriba.main import app; app()" <comando>`).

**4. Autenticar**

```
scriba auth login --client-id <client-id>
```
Esperado: o comando abre o navegador padrão da máquina sozinho, numa tela
de login da Microsoft. **Este é o ponto em que o humano entra — confirmar
o login e o consentimento na janela que abriu** (ver Trilha do humano
abaixo). O comando só retorna depois que o humano completa o login no
navegador, ou depois de 5 minutos sem resposta (timeout).

Ao retornar: `OK: Autenticado com sucesso.`

**Este passo precisa rodar numa sessão com acesso à tela** — o comando não
funciona disparado por um canal que roda fora da sessão gráfica do usuário
(SSH puro, tarefa agendada, execução remota sem `-interactive`). Medido em
validação de campo: o processo sobe, o navegador chega a ser lançado, mas
nenhuma janela aparece — o comando trava até o timeout de 5 minutos, sem
erro claro do motivo. Se o agente de IA opera por um desses canais, rodar
este passo específico de outra forma — direto no console da máquina, ou por
um agente que já executa dentro da sessão gráfica.

**5. Confirmar**

```
scriba auth status
```
Esperado:
```
Client ID: <o client-id usado>
Tenant ID: common (ou o tenant configurado)
OK: Autenticado.
```

**6. Smoke-test de leitura**

```
scriba mail search --limit 1
```
Duas saídas são sucesso — nenhuma das duas é falha:
- Uma tabela com 1 mensagem.
- `Nenhuma mensagem encontrada.` (caixa de entrada vazia ou sem mensagens
  que casem o filtro padrão — ainda assim confirma que a leitura funcionou).

Qualquer outra saída (erro de autenticação, erro de rede, traceback) indica
que algo do checklist de [prontidão da organização](verificar-prontidao-organizacao.md)
não foi atendido.

## Trilha do humano

O agente de IA vai instalar tudo por você. A única parte que só você pode
fazer:

1. Uma janela do seu navegador vai abrir sozinha, numa tela de login da
   Microsoft.
2. Faça login com a sua conta Microsoft normal (a mesma que você usa no
   Outlook/Teams do trabalho) e confirme o acesso quando pedido.
3. A aba mostra uma confirmação de que o login terminou — pode fechá-la.

É só isso — depois de confirmar, volte a deixar o agente continuar.
