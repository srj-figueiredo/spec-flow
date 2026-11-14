# spec-flow

Uma skill do Claude Code para tocar projetos de software de forma simples e bem documentada, do zero ao deploy,
usando **spec-driven development** com **um único documento como fonte de verdade**: o `SPEC.md`.

Serve para quem presta serviço, constrói pequenos apps/SaaS e precisa, meses depois, abrir o projeto e saber exatamente
o que foi feito e por quê (o próprio Claude também).

## O que ela faz

1. **Entrevista de requisitos** adaptada ao escopo: perguntas por blocos (negócio, stack, arquitetura, testes...), com
   múltipla escolha, uma opção recomendada, resposta livre e "pular". Perguntas novas surgem do briefing e das respostas.
   Pode ser respondida **em momentos diferentes, pelo celular**, com salvamento automático.
2. **SPEC.md** com objetivo, escopo, decisões, como o sistema está hoje, entregas, features (com estado), change requests e histórico.
3. **Features em entregas faseadas** e **tasks** que agentes independentes conseguem executar (opcionalmente em paralelo).
4. **Painel visual** (`docs/painel.html`) e **documento legível** (`docs/spec.html`) gerados a partir do SPEC.md.
5. **Change requests**: uma mudança daqui a meses vira mini-entrevista, atualiza as features e fica no histórico.
6. **Retomada automática**: toda sessão nova mostra em que fase o projeto está e continua de onde parou.

Fases: Entrada → Entrevista → Spec → Features → Tasks → Construção → Deploy → Manutenção. Só avança com tudo definido ou com bypass registrado.

## Instalar

Requisito: `python3` (somente biblioteca padrão).

**Em um projeto específico** (recomendado; funciona também em sessões do Claude Code na nuvem, depois do commit):

```bash
curl -fsSL https://raw.githubusercontent.com/srj-figueiredo/spec-flow/main/install.sh | bash -s -- --projeto
```

**Em todos os projetos da sua máquina:**

```bash
curl -fsSL https://raw.githubusercontent.com/srj-figueiredo/spec-flow/main/install.sh | bash -s -- --global
```

**Como plugin** (máquina local; a documentação do Claude Code informa que plugins não carregam em sessões na nuvem):

```
/plugin marketplace add srj-figueiredo/spec-flow
/plugin install spec-flow@spec-flow
```

Atualizar = rodar o instalador de novo. Seus projetos não são afetados: os dados ficam no `SPEC.md` e em `.spec/` de cada projeto.

## Usar

No projeto, abra o Claude Code e diga: *"quero começar um projeto com a spec-flow"* e cole a ideia, o anúncio do freelancer
ou as anotações da reunião. Depois, em qualquer sessão: *"retomar"*, *"painel"*, *"quero uma mudança"*.

## Entrevista pelo celular

O Claude publica uma página **privada** (só você abre) e você responde pelo navegador do celular, quando quiser.
As respostas ficam guardadas no serviço da Anthropic. Se o cliente exige sigilo, peça a entrevista **pelo chat**.

## Estrutura criada em cada projeto

```
SPEC.md               fonte de verdade
.spec/interview.json  estado da entrevista
docs/spec.html        SPEC.md para leitura
docs/painel.html      controle visual do projeto
CLAUDE.md             linha que faz toda sessão retomar a spec-flow
```

## Desenvolvimento

O motor é `plugins/spec-flow/skills/spec-flow/scripts/spec.py` (Python, sem dependências). Banco de perguntas em
`data/question-bank.json`; molde do SPEC.md em `templates/`.
