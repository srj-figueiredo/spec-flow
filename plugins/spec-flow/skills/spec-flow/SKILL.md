---
name: spec-flow
description: Conduz um projeto de software do zero ao deploy com spec-driven development. Entrevista de requisitos adaptada ao escopo (pode ser respondida depois, pelo celular), SPEC.md como fonte de verdade única, features em entregas faseadas, tasks para agentes independentes, testes autônomos no momento certo, painel visual e change requests. Use SEMPRE que o projeto tiver SPEC.md ou .spec/, no início de qualquer sessão desse projeto, e quando o usuário trouxer uma ideia, briefing de freelancer ou demanda de cliente para virar projeto, ou pedir "retomar", "status", "painel", "mudança" ou "change request".
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
2. Se a entrevista tiver `entrevista_slug` na ficha, **traga as respostas do celular antes de qualquer coisa** (`reference/celular.md`, seção "Retomar"). Se tiver `cliente_site_id`, **traga também as respostas do cliente** e faça a verificação de impacto (`reference/cliente.md`).
3. Se houver change request aberto, retome-o.

| Fase | O que fazer ao retomar |
|---|---|
| entrada | terminar o registro do briefing e começar a entrevista |
| entrevista | importar respostas do celular (`celular.md`) **e as do cliente** (`NETLIFY submissions` → `import-cliente`), rodar a **verificação de impacto**, seguir com `SPEC next` |
| spec | consolidar seções 1, 2 e 4 e pedir aprovação |
| features | propor ou ajustar features e entregas |
| tasks | quebrar features aprovadas em tasks e escrever o plano de testes |
| construcao | `SPEC ready`, tocar as próximas tasks e rodar os testes `durante-build` |
| testes | `SPEC testes` e rodar sozinho o que falta |
| deploy | checklist de deploy e testes `pos-deploy` |
| manutencao | change requests |

## Fase 0 · Entrada

Objetivo: partir do escopo, em texto livre, sem formulário prévio.

1. **A primeira pergunta é livre, no chat:** "Descreva o escopo do projeto. Pode colar o briefing, o anúncio do freelancer ou as anotações da conversa com o cliente." Não pergunte nome, tipo nem profundidade antes.
2. **Infira e confirme em uma linha.** Da resposta, deduza o **nome**, o **tipo** (`site`, `app-web`, `saas`, `mobile`, `api`, `automacao`) e a **profundidade** (`p` para algo pequeno e claro, `m` padrão, `c` para escopo grande ou de risco). Confirme: "Entendi: app web 'X', entrevista média. Segue?" Só pergunte algo se não der para deduzir.
3. `SPEC init "<nome>" --tipo <tipo> --prof <p|m|c>` (cria `SPEC.md`, `.spec/`, `docs/` e a linha de retomada no `CLAUDE.md`).
4. Escreva na seção 1 (Objetivo) um resumo fiel do que o usuário disse, com "Fonte: <origem>". Briefing longo: guarde o texto original em `docs/briefing.md`.
5. `SPEC fase entrevista`.

## Fase 1 · Entrevista de requisitos (guiada pelo escopo)

Leia `reference/entrevista.md` antes de começar. **O escopo comanda a entrevista**; o banco de perguntas é só um checklist para não esquecer o básico.

1. **Monte o plano de perguntas a partir do escopo.**
   - **Perguntas do escopo primeiro:** tudo que é específico daquele negócio e que o escopo deixou aberto, em quantas forem necessárias: `SPEC add --bloco <id> --q "..." --opt "<a que você faria>" --opt "<alternativa>" --why "..." --motivo "escopo: <trecho>" --neg "<a mesma pergunta em linguagem de NEGÓCIO>" [--neg-opt "..."]` (elas ficam antes da base no bloco). **`--neg` é obrigatório:** toda pergunta precisa ter a versão para o dono do negócio, mesmo as técnicas (reescreva como uma pergunta sobre o negócio dele que lhe permita decidir o ponto técnico: ex. banco de dados → "quanta informação você espera guardar nos próximos anos?").
   - **A base como checklist:** para cada pergunta da base, ou o escopo já responde (`SPEC dica <ID> "<o que o escopo diz>"`, o usuário confirma), ou **não se aplica** (`SPEC descartar <ID> --motivo "..."`: fica registrada no SPEC com o motivo), ou fica. Onde o contexto troca a melhor opção, `SPEC rec <ID> <n> --nota "..."`.
   - `SPEC plano` mostra o resultado por bloco (escopo × base × descartadas × para o cliente).
2. **Proponha a lista inicial do cliente e marque-a na lista completa.** Separe o que é de **negócio** (o dono do negócio responde melhor que o desenvolvedor). `SPEC lista-cliente` mostra o que já está direcionado, o que **você pré-selecionou** e as demais perguntas com texto pronto. Sua pré-seleção: `SPEC sugerir-cliente --ids A,B,C` (usa o texto pronto do banco) ou, para perguntas do escopo, reescreva em linguagem de negócio com `SPEC cliente <ID> --sugerir --texto "..." [--opt ...]`. Na lista completa as pré-selecionadas aparecem marcadas com **📌** e com o texto pronto à vista, e há um filtro "📌 Sugeridas p/ cliente". **Mostre a lista ao usuário e peça aprovação.**
   - **A escolha continua do usuário, pergunta a pergunta:** botão **Enviar ao cliente (texto sugerido)** (um toque) ou **Direcionar ao dono do negócio** (abre o texto para editar, com opções e upload). **Toda pergunta tem texto pronto em linguagem de negócio, inclusive as técnicas, e qualquer uma pode ir ao cliente, mesmo fora da sua seleção**; e ele pode simplesmente não enviar as que você marcou.
   - Aprovadas: `SPEC cliente-lote --sugeridas` (as 📌 ainda não enviadas) ou `--ids A,B,C`; use `SPEC cliente <ID> ...` quando precisar de upload (`--arquivo`) ou design (`--visual`, `--ref`). Depois `SPEC export-cliente` e publique (`reference/cliente.md`).
3. **Entregue os dois links:** a entrevista completa (só dele) e a página do cliente. Diga qual é qual e que o link do cliente não deve ser divulgado.
4. **Escolha o canal da entrevista completa:**
   - **Celular/assíncrono (recomendado):** página privada com salvamento automático (`reference/celular.md`).
   - **Chat:** `SPEC next -n 4 --json` e `AskUserQuestion` com até 4 perguntas por vez. Em cada pergunta: opção 1 = recomendada (rótulo "(Recomendada)"), no máximo 2 alternativas e "Pular (decidir depois)"; resposta livre via "Other". Registre com `SPEC answer <ID> --opt N`, `--text "..."` ou `--bypass`. **Use sempre o chat** se o cliente exigir sigilo.
5. **Retroalimente a cada resposta (do usuário ou do cliente).** Respostas abrem perguntas novas (`add`, e `cliente` se forem de negócio) e podem mudar decisões já tomadas (`impacto`, `revisar`; regra 6). Mostre o contador: "Bloco Stack · pergunta 7 de 31 (podem surgir mais)".
6. **Varredura de lacunas (obrigatória)** quando as pendentes acabarem: roteiro em `reference/entrevista.md`; adicione o que faltar; só então `SPEC varredura`.
7. `SPEC gate` diz se pode sair (barra pendência, bypass não resolvido, decisão em revisão e resposta do cliente sem verificação de impacto). Para sair: `SPEC fase spec`. Pular o questionário todo só se o usuário pedir: `SPEC bypass-all --motivo "..."`, `SPEC varredura` e, se preciso, `SPEC fase spec --forcar`. Cada bypass vira pendência no painel.

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

## Fase 4 · Tasks e plano de testes

1. Para cada feature aprovada, escreva as tasks dentro dela, no formato do molde (comentário da seção 6 do `SPEC.md`).
2. Cada task precisa poder ser feita **por um agente independente**, só com a task e o `SPEC.md`: `dono`, `toca` (arquivos que ela é dona), `depende`, `aceite`, `teste`.
3. **Escreva o plano de testes (seção 7)** junto com as tasks. Leia `reference/testes.md`: para **cada caso você decide o melhor momento** (durante a construção, antes do deploy ou só depois dele) e o modo (autônomo sempre que possível; manual só quando depende de uma pessoa). Toda feature precisa de ao menos um teste, ou um `n-a` com o motivo.
4. Pergunte uma vez: **tasks em paralelo?** (padrão: não). Se sim, `tasks_paralelas: sim` na ficha; o `check` passa a barrar tasks que disputam os mesmos arquivos sem dependência.
5. `SPEC check` até passar. `SPEC fase construcao`.

## Fase 5 · Construção

- **Sequencial** (padrão): `SPEC ready`, pegue a primeira task, `SPEC set-task T-00X andamento`, implemente **com o teste da task**, rode, `SPEC set-task T-00X feita`.
- **Paralelo** (só se `tasks_paralelas: sim`): `SPEC ready --json` devolve o lote que pode rodar junto. Dispare um subagente por task, cada um em worktree próprio (`isolation: "worktree"`), com o texto da task, as seções 1, 3 e 4 do `SPEC.md` e a ordem **"não edite o SPEC.md"**. Quem atualiza estados e integra é você, depois de conferir o teste de cada um. Avise que paralelo gasta mais tokens.
- **Testes marcados `durante-build` rodam aqui, sozinhos**, assim que fazem sentido: `SPEC set-teste TS-00X passou --evidencia <arquivo>`.
- Quando todas as tasks de uma feature terminam: `SPEC set-feature F-00X em-teste`.
- Mudou algo estrutural (stack, arquitetura, como rodar)? Atualize a seção 4 na hora. Registre o relevante: `SPEC hist "..."`.
- Tudo pronto: `SPEC fase testes`.

## Fase 6 · Testes

Seja o mais **autônomo** possível. Procedimento e regras em `reference/testes.md`.

1. `SPEC testes` mostra o plano por momento. Rode, **sem pedir licença**, todos os testes autônomos de `antes-deploy` (e qualquer `durante-build` que sobrou), guarde a evidência em `docs/evidencias/` e registre: `SPEC set-teste ID passou|falhou --evidencia <caminho>`.
2. **Falhou:** não avance. Descubra a causa, crie a task de correção, conserte, rode de novo. Depois de 3 tentativas sem sucesso, mostre ao usuário o que tentou.
3. **Testes manuais** (aceite do dono, olhar de design): entregue um roteiro curto e objetivo; o usuário executa e você registra o resultado. É o **aceite** que move a feature para `entregue`.
4. **Reavalie o plano:** se um teste só faz sentido depois do deploy, mude `quando: pos-deploy` e explique em `motivo_momento`; se surgiu risco novo, crie teste novo (`SPEC new-id TS`).
5. `SPEC fase deploy` só com tudo de `antes-deploy` passado (ou `n-a` justificado).

## Fase 7 · Deploy

1. Releia as decisões de deploy (DP-*, S-02, A-03, SG-03) e monte um checklist curto: ambiente, variáveis e segredos, domínio e DNS, banco e migrações, backup, monitoramento, rollback.
2. Rode o checklist com o usuário. **Confirme antes de cada ação externa.** Credenciais: o usuário fornece pelo meio seguro do ambiente; nunca peça para colar segredos no chat.
3. **Logo depois de publicar, rode sozinho os testes `pos-deploy`** (disponibilidade, HTTPS, domínio, fluxo principal em produção, e-mail e pagamento em modo de teste quando houver). Falha em produção: avise na hora e proponha o rollback decidido na entrevista.
4. Atualize a seção 4 (URL, como publicar de novo, como reverter), marque as features como `entregue` com o aceite e `SPEC fase manutencao` (só passa com os testes `pos-deploy` passados).

## Fase 8 · Manutenção e change requests

Quando o usuário pedir uma mudança (daqui a dias ou meses):

1. **Leia o `SPEC.md` inteiro** antes de responder.
2. `SPEC cr-new "<título>" --features F-00X --motivo "..."`.
3. **Mini-entrevista só dos blocos afetados**: `SPEC add` com perguntas sob medida (bloco `mudanca` e os blocos tocados), pelo canal de sempre; direcione ao cliente o que for dele. Varredura curta e `SPEC varredura`.
4. Com respostas fechadas: `SPEC cr-set CR-001 aprovada` (marca as features afetadas como `alterada`), crie ou ajuste features (`origem: CR-001`), tasks **e testes** (inclua regressão do que a mudança pode quebrar) e construa, teste e publique como nas fases 3 a 7.
5. Ao entregar: `SPEC cr-set CR-001 entregue`, features voltam a `entregue`, seção 4 atualizada, histórico registrado.

## Link do cliente (Netlify)

`NETLIFY` = `python3 ${CLAUDE_SKILL_DIR}/scripts/netlify.py` (`site-ensure [--aleatorio]`, `deploy`, `forms`, `submissions`, `delete-site`). Precisa do token do Netlify (nuvem: credencial salva para `api.netlify.com`; local: `NETLIFY_AUTH_TOKEN`). Fluxo completo e cuidados em `reference/cliente.md`.

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
| `plano [--json]` | como a entrevista está montada (escopo × base × descartadas × para o cliente × 📌 sugeridas) |
| `descartar ID --motivo ".." [--desfazer]` | pergunta da base que não se aplica (fica registrada) |
| `lista-cliente [--json]` | direcionadas, 📌 sugeridas por você e demais com texto pronto |
| `sugerir-cliente --ids A,B [--remover]` / `cliente-lote --ids A,B \| --sugeridas` | marca/desmarca a pré-seleção / direciona várias de uma vez |
| `add --bloco B --q ".." --opt ".." --neg ".." [--neg-opt ..] [--bloco-nome N] [--why ..] [--motivo ..] [--multi] [--design]` | pergunta do escopo; `--neg` (versão de negócio) é obrigatório; `--design` = pergunta de design |
| `atualizar-textos` | dá às perguntas da base os textos de negócio que ainda não tinham (também roda no `export-web`) |
| `bypass-all [--bloco B] [--motivo ..]` | pula pendentes em lote |
| `varredura` | registra a varredura de lacunas |
| `export-web` | gera `.spec/entrevista.html` (página do celular) |
| `import-answers arquivo.json` | importa respostas do celular |
| `sync` | regrava o bloco de decisões do SPEC.md |
| `cliente ID [--texto ..] [--opt ..] [--arquivo [--arquivo-desc ..]] [--design] [--visual paleta\|layout\|tipografia] [--visual-opt "tipo\|Rótulo\|dado"] [--ref "Rótulo\|URL"] [--sugerir] [--remover]` | direciona a pergunta ao dono do negócio (upload, opções visuais e referências) |
| `export-cliente [--intro ..]` | gera a página do cliente (`.spec/cliente/`) |
| `import-cliente envios.json` | importa as respostas do cliente (a traduzir) |
| `impacto [--json]` / `impacto-ok` | checklist de impacto das respostas do cliente sobre decisões já tomadas / registra que foi feito |
| `revisar ID --motivo ".." --origem ID` / `revisao-ok ID [--nota ..]` | marca decisão afetada para revisão / encerra mantendo |
| `ficha [chave] [valor]` | lê ou grava campos da Ficha (ex.: `entrevista_web`, `entrevista_slug`, `cliente_site_id`, `cliente_url`, `tasks_paralelas`) |
| `gate` / `fase DESTINO [--forcar]` | valida e muda de fase |
| `check` | valida o SPEC.md (ids, dependências, ciclos, arquivos em disputa) |
| `ready [--json]` | tasks prontas e lote paralelo |
| `testes [--quando Q] [--json]` / `set-teste ID estado [--evidencia ..]` | plano de testes por momento / registra resultado com evidência |
| `set-feature ID estado` / `set-task ID estado` | muda estados (task: pendente, andamento, feita, bloqueada) |
| `hist "texto"` / `new-id F\|T\|CR\|E\|TS` | histórico / próximo id |
| `cr-new` / `cr-set ID estado` | change requests |
| `render` | gera os HTMLs |
