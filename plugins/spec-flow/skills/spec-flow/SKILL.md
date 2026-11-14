---
name: spec-flow
description: Conduz um projeto de software do zero ao deploy com spec-driven development. Entrevista de requisitos adaptada ao escopo (pode ser respondida depois, pelo celular), SPEC.md como fonte de verdade única, features em entregas faseadas, tasks para agentes independentes, painel visual e change requests. Use SEMPRE que o projeto tiver SPEC.md ou .spec/, no início de qualquer sessão desse projeto, e quando o usuário trouxer uma ideia, briefing de freelancer ou demanda de cliente para virar projeto, ou pedir "retomar", "status", "painel", "mudança" ou "change request".
---

# spec-flow

Uma skill para tocar projetos pequenos e médios com **um documento só como fonte de verdade**: o `SPEC.md`. Quem abrir o projeto daqui a 6 meses (o usuário ou você) lê esse arquivo e sabe o que foi feito, por quê e em que estado está.

Comando do motor (use sempre este caminho; ele já aponta para a pasta da skill):

```
python3 ${CLAUDE_SKILL_DIR}/scripts/spec.py <comando>
```

Se `${CLAUDE_SKILL_DIR}` aparecer sem substituir, ache o script com `find / -name spec.py -path "*spec-flow*" 2>/dev/null` e use o caminho real. Daqui em diante, `SPEC` = esse comando completo. A lista de comandos está no fim.

## Regras que valem sempre

1. **`SPEC.md` é a única verdade.** Leia-o antes de mexer no projeto e atualize-o junto com cada mudança. Estados de feature e task mudam pelos comandos (`set-feature`, `set-task`), não à mão.
2. **Inferir o mínimo.** Nunca preencha por conta própria uma decisão técnica ou funcional que a entrevista deveria ter respondido. Se faltar, pergunte. O que o briefing já diz entra como *dica para confirmar* (`dica`), não como resposta.
3. **Não pule fase.** Só avance com `SPEC fase <próxima>` (ele valida). Se faltar algo, mostre a lista exata e resolva ou faça bypass. O usuário pode fazer bypass de uma pergunta, de um bloco ou do questionário todo; isso fica registrado como pendência, nunca some.
4. **Ações que saem do computador** (deploy, publicar, enviar e-mail, mexer em contas) só com confirmação explícita do usuário.
5. **Respostas curtas e diretas**, em português do Brasil. Mostre o que mudou e o que falta.
6. **Toda resposta do cliente exige verificação de impacto.** As respostas do dono do negócio podem mudar decisões que já estavam fechadas na lista completa. Depois de `import-cliente`, rode `SPEC impacto`, confira cada resposta nova contra TODAS as decisões já tomadas, marque as afetadas com `SPEC revisar` e só então `SPEC impacto-ok`. A entrevista não fecha com decisão em revisão ou resposta sem verificação (`reference/cliente.md`, seção "Verificação de impacto").
7. **Perguntas de design ao cliente sempre levam opções visuais e/ou links de referência** (pelo menos um). Arquivos: o formulário aceita upload de até 8 MB por envio; acima disso o desenvolvedor combina a entrega (`reference/cliente.md`, seção "Arquivos e design").
8. Depois de qualquer mudança relevante rode `SPEC render` e, se o git for usado no projeto, faça commit com o `SPEC.md` e a pasta `docs/`.

## Ao abrir uma sessão (retomada automática)

1. Procure `SPEC.md` na raiz. **Existe:** rode `SPEC status`, mostre em 4 linhas a fase, o progresso e a próxima ação, e **retome de onde parou** (tabela abaixo). **Não existe** e o usuário trouxe uma ideia, um briefing ou uma demanda: comece pela *Fase 0*.
2. Se a entrevista tiver `entrevista_web` na ficha, **traga as respostas do celular antes de qualquer coisa** (`reference/celular.md`, seção "Retomar").
3. Se houver change request aberto, retome-o.

| Fase | O que fazer ao retomar |
|---|---|
| entrada | terminar o registro do briefing e começar a entrevista |
| entrevista | importar respostas do celular, seguir com `SPEC next` |
| spec | consolidar seções 1, 2 e 4 e pedir aprovação |
| features | propor ou ajustar features e entregas |
| tasks | quebrar features aprovadas em tasks |
| construcao | `SPEC ready` e tocar as próximas tasks |
| deploy | checklist de deploy |
| manutencao | change requests |

## Fase 0 · Entrada

Objetivo: transformar o que o usuário trouxe em ponto de partida, sem inventar nada.

1. Peça (ou use o que já foi colado): a ideia, o anúncio do freelancer ou as anotações da conversa com o cliente.
2. Defina com o usuário, em uma única rodada curta: **nome do projeto**, **tipo** (`site`, `app-web`, `saas`, `mobile`, `api`, `automacao`) e **profundidade** da entrevista (`p` pequeno, `m` médio, `c` completo; padrão `m`).
3. `SPEC init "<nome>" --tipo <tipo> --prof <p|m|c>` (cria `SPEC.md`, `.spec/`, `docs/` e a linha de retomada no `CLAUDE.md`).
4. Escreva na seção 1 (Objetivo) um resumo fiel do briefing, com a frase "Fonte: <origem do briefing>". Se o briefing for longo, guarde o texto original em `docs/briefing.md` e referencie.
5. `SPEC fase entrevista`.

## Fase 1 · Entrevista de requisitos

Leia `reference/entrevista.md` antes de começar: ele diz como personalizar a base, como escrever perguntas do escopo e o roteiro da varredura de lacunas.

Resumo do processo:

1. **Personalize a base.** Para cada pergunta em que o briefing já diz algo, `SPEC dica <ID> "<o que o briefing diz>"`. Onde o contexto do projeto torna outra opção a melhor, `SPEC rec <ID> <n> --nota "<por quê>"`.
2. **Gere as perguntas do escopo.** Releia o briefing procurando tudo que é específico daquele negócio e ainda não está coberto pela base. Adicione com `SPEC add --bloco <id> --q "..." --opt "<a que você faria>" --opt "<alternativa>" --opt "<alternativa>" --why "..." --motivo "briefing: <trecho>"`. Faça isso de novo depois de cada rodada de respostas: respostas abrem novas perguntas.
3. **Direcione ao dono do negócio o que for dele.** Muita pergunta é de negócio, não técnica. Perguntas da base que têm versão pronta em linguagem de negócio (campo `neg`) são sugeridas ao usuário; para as técnicas, ofereça uma reescrita quando ele pedir. O usuário decide, pergunta a pergunta, e o link do cliente recebe só as direcionadas. Procedimento (publicar, receber, traduzir) em `reference/cliente.md`. Perguntas direcionadas ficam em **aguardando cliente**.
4. **Escolha o canal:**
   - **Celular/assíncrono (recomendado):** página privada com salvamento automático. Procedimento completo em `reference/celular.md`.
   - **Chat:** `SPEC next -n 4 --json` e `AskUserQuestion` com até 4 perguntas por vez. Em cada pergunta: opção 1 = recomendada (rótulo com "(Recomendada)"), no máximo 2 alternativas adequadas e a opção "Pular (decidir depois)"; a resposta livre o próprio `AskUserQuestion` oferece em "Other". Registre com `SPEC answer <ID> --opt N`, `--text "..."` ou `--bypass`. **Use sempre o chat** quando o cliente exigir sigilo: a página do celular guarda as respostas no serviço da Anthropic.
5. **Mostre o contador**: "Bloco Stack · pergunta 7 de 31 (podem surgir mais)". `SPEC status` dá os números.
6. **Varredura de lacunas (obrigatória)** quando as pendentes acabarem: siga o roteiro de `reference/entrevista.md`, adicione o que faltar, e só então `SPEC varredura`.
7. `SPEC gate` diz se pode sair. Para sair: `SPEC fase spec`. Para pular o questionário todo, o usuário precisa pedir: `SPEC bypass-all --motivo "..."` e depois `SPEC varredura` e `SPEC fase spec --forcar` se necessário. Avise que cada bypass vira pendência no painel.

## Fase 2 · Spec

1. Leia o bloco de decisões (seção 3, gerado por `SPEC sync`) e escreva:
   - **Seção 1 (Objetivo)**: o problema, para quem, e como medir sucesso.
   - **Seção 2 (Escopo)**: o que está dentro e o que está **fora** do escopo.
   - **Seção 4 (Como está hoje)**: stack, arquitetura, como rodar, como publicar; só com o que foi decidido. Lacuna vira "A definir" com o ID da pergunta pendente.
2. Mostre um resumo ao usuário e peça aprovação. `SPEC fase features` só depois do "ok".

## Fase 3 · Features e entregas

Leia `reference/features-tasks.md` (como cortar, formato, exemplos).

1. Quebre o escopo em **features funcionais que façam sentido para o negócio** (uma fatia vertical que o cliente reconhece como valor), não em camadas técnicas.
2. Agrupe em **entregas** (`E1 · MVP`, `E2 · ...`) na seção 5, para entregar em fases. Se o usuário quiser entrega única, use uma só.
3. Cada feature tem `estado`, `entrega`, `valor` e critérios de **aceite verificáveis**. Todas nascem `proposta`.
4. Apresente as entregas e features ao usuário. Cada uma aprovada vira `aprovada` (`SPEC set-feature F-001 aprovada`). `SPEC fase tasks`.

## Fase 4 · Tasks

1. Para cada feature aprovada, escreva as tasks dentro dela, no formato do molde (comentário da seção 6 do `SPEC.md`).
2. Cada task precisa poder ser feita **por um agente independente**, só com a task e o `SPEC.md`: `dono`, `toca` (arquivos que ela é dona), `depende`, `aceite`, `teste`.
3. Pergunte uma vez: **tasks em paralelo?** (padrão: não). Se sim, `tasks_paralelas: sim` na ficha; o `check` passa a barrar tasks que disputam os mesmos arquivos sem dependência.
4. `SPEC check` até passar. `SPEC fase construcao`.

## Fase 5 · Construção e testes

- **Sequencial** (padrão): `SPEC ready`, pegue a primeira task, `SPEC set-task T-00X andamento`, implemente **com o teste da task**, rode o teste, `SPEC set-task T-00X feita`.
- **Paralelo** (só se `tasks_paralelas: sim`): `SPEC ready --json` devolve o lote que pode rodar junto. Dispare um subagente por task, cada um em worktree próprio (`isolation: "worktree"`), com o texto da task, as seções 1, 3 e 4 do `SPEC.md` e a ordem **"não edite o SPEC.md"**. Quem atualiza estados e integra é você, depois de conferir o teste de cada um. Avise o usuário que paralelo gasta mais tokens.
- Quando todas as tasks de uma feature terminam: `SPEC set-feature F-00X em-teste`. O **aceite é do usuário**: só ele move para `entregue`.
- Mudou algo estrutural (stack, arquitetura, como rodar)? Atualize a seção 4 na mesma hora.
- Tudo o que for relevante vai para o histórico: `SPEC hist "..."`.

## Fase 6 · Deploy

1. Releia as decisões de deploy (DP-*, S-02, A-03, SG-03) e monte um checklist curto: ambiente, variáveis e segredos, domínio e DNS, banco e migrações, backup, monitoramento, rollback.
2. Rode o checklist com o usuário. **Confirme antes de cada ação externa.** Credenciais: o usuário fornece pelo meio seguro do ambiente; nunca peça para colar segredos no chat.
3. Depois do deploy: atualize a seção 4 (URL, como publicar de novo, como reverter), marque as features como `entregue` com o aceite do usuário e `SPEC fase manutencao`.

## Fase 7 · Manutenção e change requests

Quando o usuário pedir uma mudança (daqui a dias ou meses):

1. **Leia o `SPEC.md` inteiro** antes de responder.
2. `SPEC cr-new "<título>" --features F-00X --motivo "..."`.
3. **Mini-entrevista só dos blocos afetados**: `SPEC add` com perguntas sob medida (bloco `mudanca` e os blocos tocados), pelo canal de sempre. Varredura de lacunas curta. `SPEC varredura`.
4. Com respostas fechadas: `SPEC cr-set CR-001 aprovada` (marca as features afetadas como `alterada`), crie ou ajuste features com `origem: CR-001`, tasks, construa e teste como nas fases 3 a 6.
5. Ao entregar: `SPEC cr-set CR-001 entregue`, features voltam a `entregue`, seção 4 atualizada, histórico registrado.

## Link do cliente (Netlify)

`NETLIFY` = `python3 ${CLAUDE_SKILL_DIR}/scripts/netlify.py` (`site-ensure`, `deploy`, `forms`, `submissions`, `delete-site`). Fluxo completo e cuidados em `reference/cliente.md`.

## Painel e documento (visual)

- `SPEC render` gera `docs/painel.html` (controle ponta a ponta: fase, entrevista, entregas, features, tasks, pendências, change requests, histórico) e `docs/spec.html` (o SPEC.md formatado para leitura).
- Sempre que o usuário pedir "painel" ou "status visual", rode `render` e informe os caminhos. Para ver no celular, ofereça publicar como artifact privado (`publish_files` com `docs/painel.html` como `index.html`, sem capacidades) e entregue o link.

## Comandos do motor (`SPEC ...`)

| Comando | Para quê |
|---|---|
| `init "nome" --tipo T --prof p\|m\|c` | cria o projeto |
| `status [--json]` | fase, entrevista, features, tasks, change requests |
| `next [-n 4] [--bloco B] [--json]` | próximas perguntas pendentes |
| `answer ID --opt N \| --text "..." \| --bypass` | registra resposta (`--opt 2,3` em multi) |
| `dica ID "texto"` / `rec ID N [--nota ".."]` | personaliza pergunta da base |
| `add --bloco B --q ".." --opt ".." [--opt ..] [--why ..] [--motivo ..] [--multi]` | pergunta do escopo |
| `bypass-all [--bloco B] [--motivo ..]` | pula pendentes em lote |
| `varredura` | registra a varredura de lacunas |
| `export-web` | gera `.spec/entrevista.html` (página do celular) |
| `import-answers arquivo.json` | importa respostas do celular |
| `sync` | regrava o bloco de decisões do SPEC.md |
| `cliente ID [--texto ..] [--opt ..] [--arquivo] [--design --visual paleta\|layout\|tipografia --ref URL] [--sugerir] [--remover]` | direciona a pergunta ao dono do negócio (upload, opções visuais e referências) |
| `export-cliente [--intro ..]` | gera a página do cliente (`.spec/cliente/`) |
| `import-cliente envios.json` | importa as respostas do cliente (a traduzir) |
| `impacto [--json]` / `impacto-ok` | checklist de impacto das respostas do cliente sobre decisões já tomadas / registra que foi feito |
| `revisar ID --motivo ".." --origem ID` / `revisao-ok ID [--nota ..]` | marca decisão afetada para revisão / encerra mantendo |
| `ficha [chave] [valor]` | lê ou grava campos da Ficha (ex.: `entrevista_web`, `entrevista_slug`, `tasks_paralelas`) |
| `gate` / `fase DESTINO [--forcar]` | valida e muda de fase |
| `check` | valida o SPEC.md (ids, dependências, ciclos, arquivos em disputa) |
| `ready [--json]` | tasks prontas e lote paralelo |
| `set-feature ID estado` / `set-task ID estado` | muda estados (task: pendente, andamento, feita, bloqueada) |
| `hist "texto"` / `new-id F\|T\|CR\|E` | histórico / próximo id |
| `cr-new` / `cr-set ID estado` | change requests |
| `render` | gera os HTMLs |
