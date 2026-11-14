# Guia de uso da spec-flow

Tudo o que a skill tem e como usar. Você conversa com o Claude em linguagem natural; ele roda os comandos (`SPEC` = `python3 <skill>/scripts/spec.py`). Os comandos aparecem aqui só para referência.

## 1. Visão geral

Cada projeto tem **um documento só como fonte de verdade**: o `SPEC.md`. A skill conduz o projeto por 9 fases e só deixa avançar com tudo definido ou com bypass registrado:

`Entrada → Entrevista → Spec → Features → Tasks → Construção → Testes → Deploy → Manutenção`

Arquivos criados em cada projeto: `SPEC.md` (fonte de verdade), `.spec/interview.json` (estado da entrevista), `docs/spec.html` (SPEC legível), `docs/painel.html` (controle visual) e uma linha no `CLAUDE.md` que faz toda sessão nova retomar a skill.

## 2. Instalação

Requisito: `python3` (testado em 3.11, 3.12 e 3.13).

| Onde | Comando | Observação |
|---|---|---|
| Só em um projeto | `curl -fsSL https://raw.githubusercontent.com/srj-figueiredo/spec-flow/main/install.sh \| bash -s -- --projeto` | **Faça commit** de `.claude/skills/spec-flow`. É o único modo que funciona em sessões na nuvem |
| Todos os projetos da máquina | mesmo comando com `--global` | Sessões na nuvem não enxergam `~/.claude` |
| Como plugin | `/plugin marketplace add srj-figueiredo/spec-flow` e `/plugin install spec-flow@spec-flow` | Não carrega em sessões na nuvem |

Atualizar = rodar o instalador de novo. Os dados dos projetos não são afetados.

Opcionais: **ferramentas de artifacts** (entrevista pelo celular) e **token do Netlify** (link do cliente). Sem eles, a entrevista roda no chat.

## 3. Começar um projeto (Fase 0)

A **primeira pergunta é livre, no chat**: *"Descreva o escopo do projeto."* Você cola a ideia, o anúncio do freelancer ou as anotações da reunião; o Claude **infere** nome, tipo e profundidade e confirma em uma linha.

Diga: *"quero começar um projeto com a spec-flow"*. O Claude cria o projeto (tipos: `site`, `app-web`, `saas`, `mobile`, `api`, `automacao`; profundidade: `p` 16 a 19 perguntas-base, `m` 41 a 47, `c` 57 a 65, conforme o tipo) e registra o escopo na seção 1.

## 4. Entrevista de requisitos (Fase 1)

- **O escopo comanda a entrevista.** O Claude gera as perguntas a partir do que você descreveu (elas ficam antes, em cada bloco) e usa o banco de 66 perguntas-base só como **checklist**: o que o escopo já responde vira dica para você confirmar, o que não se aplica é **descartado com motivo** (fica registrado no SPEC) e o resto permanece. `plano` mostra o resultado por bloco. O total cresce durante a entrevista (o contador diz "até agora"). Cada pergunta mostra o motivo ("surgiu de: ...").
- **Cada pergunta** tem: opção recomendada (primeira, com motivo), alternativas, resposta livre e **pular** (bypass). O que o escopo já diz aparece como dica ("No briefing: ...") para você confirmar, nunca como resposta.
- **Blocos:** Negócio, Usuários e escopo, Regras de negócio, Dados, Integrações, Stack, Arquitetura, Segurança e LGPD, Testes e aceite, Deploy e infra, Prazo e entrega, Manutenção.
- **Perguntas condicionais** (ex.: meio de pagamento só se houver pagamento).
- **Bypass** de uma pergunta, de um bloco ou do questionário todo (`bypass-all`). Vira pendência no painel e `PENDENTE (bypass)` no SPEC.
- **Varredura de lacunas** obrigatória antes de sair: o Claude relê tudo, adiciona o que faltar e registra.
- **Dois canais:**
  - **Celular (recomendado):** página privada, cada toque salva sozinho, com ditado por voz onde o navegador oferece. Pedir: *"gera a entrevista para o celular"*. Depois, em qualquer sessão: *"retomar"*.
  - **Chat:** até 4 perguntas por vez com múltipla escolha. Obrigatório quando o cliente exige sigilo.

## 5. Os dois links

| Link | Quem usa | Conteúdo |
|---|---|---|
| **Entrevista completa** | você | todas as perguntas, técnicas e de negócio |
| **Página do cliente** | o dono do negócio | só as perguntas que você direcionou, em linguagem de negócio |

### A lista inicial do cliente
Depois de montar o plano, o Claude **propõe a primeira lista para o dono do negócio**: separa o que é de negócio e reescreve em linguagem de negócio (com opções visuais nas de design). Na lista completa, **o que ele pré-selecionou aparece marcado com 📌**, com o texto pronto à vista, e há um filtro "📌 Sugeridas p/ cliente". **A escolha final é sua**, pergunta a pergunta: **Enviar ao cliente (texto sugerido)** com um toque, **Direcionar ao dono do negócio** para editar o texto, mandar uma que ele não marcou (qualquer pergunta com texto pronto serve) ou não mandar uma que ele marcou. Pedir: *"mostra a lista do cliente"*.

### Direcionar ao dono do negócio
Em cada pergunta há o botão **Direcionar ao dono do negócio**: a pergunta vem reescrita em linguagem de negócio (editável), com opções opcionais e a caixa "o cliente precisa enviar um arquivo". 25 perguntas da base já trazem a sugestão pronta. A pergunta fica **aguardando cliente** (roxo).

### Página do cliente (Netlify)
Pedir: *"publica a página do cliente"*. O Claude gera a página, cria um site com **endereço aleatório** (não indexável, sem senha: quem tem o link acessa) e te entrega o link.

- **Registro acumulativo e somente leitura.** As respostas anteriores aparecem travadas no topo (texto, não campo), agrupadas por **rodada**, com data, nome e **código de verificação**; as perguntas novas ficam embaixo. A página serve de registro histórico e de formalização das definições. O mesmo registro vai para o `SPEC.md`.
- **Reenvio** vira "Complemento": a resposta original nunca é alterada.
- **Upload de arquivo:** limite de **8 MB por envio**, um arquivo por pergunta. A página barra arquivo maior, marca "meu arquivo é maior" e avisa que o desenvolvedor entrará em contato para pegar.
- **Perguntas de design:** sempre com **opções visuais** (cores, organização da tela, letras) e/ou **links de referência**, mais um campo para o cliente colar os links que ele gosta.
- **Não use em projeto confidencial.**

### Traduzir e verificar impacto
Quando o cliente responde: *"retomar"* (ou *"o cliente respondeu"*). O Claude lê os envios, mostra a resposta nas palavras dele, propõe a **decisão técnica** e você confirma. Em seguida faz a **verificação de impacto obrigatória**: confere cada resposta do cliente contra **todas** as decisões já tomadas na lista completa. A decisão afetada vira **a revisar** (laranja, com a decisão anterior) e **impede sair da entrevista** até você refazer ou confirmar. A decisão anterior fica no histórico da pergunta.

## 6. Spec, features, tasks, construção, deploy, mudanças

| Fase | O que acontece | Como pedir |
|---|---|---|
| **Spec** | Objetivo, escopo (dentro e fora) e "como está hoje" escritos a partir das decisões; você aprova | *"fecha a spec"* |
| **Features** | Escopo cortado em features que fazem sentido para o negócio, agrupadas em **entregas** (E1 MVP, E2...), com critérios de aceite; você aprova cada uma | *"quebra em features e entregas"* |
| **Tasks** | Cada feature aprovada vira tasks que um agente independente consegue executar (arquivos, dependências, aceite, teste). Pergunta uma vez se quer **tasks em paralelo** (padrão: não) | *"quebra em tasks"* |
| **Construção** | Sequencial (uma por vez) ou **paralelo** (subagentes em worktrees próprios, sem editar o SPEC). Os testes marcados "durante a construção" rodam aqui, sozinhos | *"constrói a próxima task"* / *"constrói em paralelo"* |
| **Testes** | O plano de testes (seção 7) nasce junto com as tasks. **Cada teste vai para o momento em que faz sentido**: durante a construção, antes do deploy ou só depois dele. O Claude roda sozinho tudo o que dá, guarda **evidência** em `docs/evidencias/` e só pede você para o que depende de uma pessoa (aceite). Falhou: não avança, corrige e roda de novo | *"roda os testes"* |
| **Deploy** | Checklist a partir das decisões (ambiente, segredos, domínio, banco, backup, monitoramento, rollback). Confirma antes de cada ação externa. **Logo depois de publicar, roda sozinho os testes pós-deploy** | *"vamos ao deploy"* |
| **Manutenção** | **Change request**: mini-entrevista só dos blocos afetados, features marcadas como alteradas, novas tasks **e testes (com regressão)**, tudo no histórico | *"quero uma mudança: ..."* |

Estados da feature: `proposta → aprovada → em-andamento → em-teste → entregue → alterada` (e `descartada`). Marcas da task: pendente, andamento, feita, bloqueada.

## 7. Painel e documento

- `docs/painel.html`, com **uma aba por etapa**: *Visão geral* (fase, KPIs, entrevista por bloco, entregas e **pendências**), *Entrevista* (cada decisão com origem, resposta do cliente, decisões anteriores e perguntas descartadas), *Features* (critérios de aceite), *Tasks*, *Testes* (plano por momento, modo, estado e evidência) e *Histórico* (links e registro completo). Funciona no celular e no escuro.
- `docs/spec.html`: o `SPEC.md` formatado para leitura.
- Pedir: *"painel"*. Para ver no celular, o Claude publica como página privada.

## 8. Retomada automática

O `CLAUDE.md` do projeto manda toda sessão nova invocar a skill. Ela mostra a fase, o que falta, e retoma: importa respostas do celular e do cliente, roda a verificação de impacto, segue de onde parou.

## 9. Comandos (referência)

| Comando | Para quê |
|---|---|
| `init "nome" --tipo T --prof p\|m\|c` | cria o projeto |
| `status [--json]` | fase, entrevista, features, tasks, pendências |
| `next [-n 4] [--bloco B] [--json]` | próximas perguntas |
| `answer ID --opt N \| --text ".." \| --bypass` | registra resposta |
| `dica ID ".."` / `rec ID N [--nota ..]` | personaliza pergunta da base |
| `add --bloco B --q ".." --opt ".." [--why ..] [--motivo ..] [--multi] [--design]` | pergunta do escopo |
| `plano` / `descartar ID --motivo ..` | plano de perguntas por bloco / pergunta da base que não se aplica |
| `lista-cliente` | direcionadas, 📌 sugeridas e demais com texto pronto |
| `sugerir-cliente --ids A,B [--remover]` / `cliente-lote --ids A,B \| --sugeridas` | marca a pré-seleção / direciona várias de uma vez |
| `bypass-all [--bloco B] [--motivo ..]` / `varredura` | pular em lote / registrar varredura |
| `export-web` / `import-answers arq.json` | página do celular / importar respostas |
| `cliente ID [--texto ..] [--opt ..] [--arquivo [--arquivo-desc ..]] [--design] [--visual paleta\|layout\|tipografia] [--visual-opt ..] [--ref ..] [--sugerir] [--remover]` | direciona ao dono do negócio |
| `export-cliente [--intro ..]` / `import-cliente arq.json` | página do cliente / importar envios |
| `impacto [--json]` / `impacto-ok` | verificação de impacto |
| `revisar ID --motivo .. --origem ID` / `revisao-ok ID` | marcar decisão para revisão / manter |
| `gate` / `fase DESTINO [--forcar]` / `check` | validar, mudar fase, validar SPEC |
| `ready [--json]` / `set-feature` / `set-task` | construção |
| `testes [--quando Q]` / `set-teste ID estado --evidencia ..` | plano de testes por momento / resultado com evidência |
| `cr-new` / `cr-set` / `hist` / `new-id` / `ficha` / `sync` / `render` | mudanças, histórico, utilitários |
| `netlify.py site-ensure [--aleatorio] [--ficha .]`, `deploy`, `forms`, `submissions`, `delete-site` | publicação do link do cliente |

## 10. Limites conhecidos

- **Link do cliente** é privado só por obscuridade (sem senha). O registro é somente leitura para o cliente, mas quem controla o Netlify pode editar o site; o código de verificação permite detectar isso.
- **Upload:** o formato em que o arquivo chega na leitura dos envios e o acesso ao download ainda precisam ser confirmados com o primeiro arquivo real.
- **Rede da nuvem:** o ambiente não alcança sites `*.netlify.app`; testes de envio ao formulário são feitos por você.
- **Netlify gratuito:** limites de envios por mês não verificados. Confira no painel do Netlify.
- **Entrevista no celular** guarda respostas no serviço da Anthropic; não use com cliente que exige sigilo.
- O token do Netlify fica no ambiente padrão e vale para todas as suas sessões.

## 11. Testes

`python3 tests/smoke.py` roda 140+ verificações (motor, gates, página do cliente, registro, impacto, importações) sem rede.
