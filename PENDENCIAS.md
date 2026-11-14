# Pendências do spec-flow

Arquivo de controle para retomar o trabalho em qualquer sessão. Atualize ao fechar cada item. Última atualização: 2026-11-14 (v0.7.1).

## Estado atual

- Versão publicada: **0.7.1** (correções do ensaio: gate da CR, `rodar-teste`, `n-a` no checklist) sobre a 0.7.0 (abas Deploy e Cliente).
- Testes: `python3 tests/smoke.py` (237 verificações, Python 3.11/3.12/3.13) e `claude plugin validate .`.
- Objetivo: deixar a skill pronta para o **primeiro projeto real com cliente**.

## Ensaio das fases 3 a 8 (feito em 2026-11-14)

Projeto fictício "Encomendas da Doceria da Lu" (app web pequeno, Python + SQLite), com features, tasks, plano de testes por momento, construção sequencial, testes autônomos (unidade e e2e com Playwright), deploy **simulado localmente** (produção = processo local, sem serviço externo), uma change request e um teste que falhou de verdade. O fluxo andou do início ao fim sem travar. Pasta de trabalho: scratchpad da sessão (não está no repositório).

### O que o ensaio revelou e o que foi feito (v0.7.1)

| # | Achado | Situação |
|---|---|---|
| 1 | `cr-set entregue` passava sem nenhuma verificação (task e teste pendentes) | **Corrigido**: exige tasks e testes das features da CR concluídos; `--forcar`; features `alterada` voltam a `entregue` |
| 2 | `ready` ignorava features `alterada`: tasks de uma CR nunca apareciam como prontas | **Corrigido** |
| 3 | `ready` dizia "podem rodar JUNTAS" mesmo no modo sequencial | **Corrigido**: mostra "Próxima task" |
| 4 | Registrei um teste como `passou` sem ler a saída (era falha) | **Corrigido**: novo `rodar-teste` registra pelo código de saída e guarda o log; regra no SKILL e em `reference/testes.md` |
| 5 | Smoke pós-deploy bateu num processo antigo que ainda ocupava a porta | **Documentado** (confirmar a versão no ar antes de testar) |
| 6 | Smoke pós-deploy deixou dado de teste em produção | **Documentado** (dado `SMOKE-...`, apagar e registrar) |
| 7 | Checklist de deploy não tinha "não se aplica" (ex.: app sem segredos) | **Corrigido**: estado `n-a` com justificativa obrigatória |
| 8 | Item `feito` sem evidência passava despercebido | **Corrigido**: a aba Deploy mostra "sem evidência registrada" |
| 9 | Aceite manual sem registro de quem aceitou e quando | **Documentado** (evidência diz quem, como e quando; aceite simulado nunca entra como real) |
| 10 | `next` mostrava "(por quê: )" vazio | **Corrigido** |
| 11 | O teste e2e pegou um defeito de verdade: validação nativa do navegador escondia a mensagem da API | Corrigido no app do ensaio (fluxo de falha → task de correção → reteste funcionou) |

Limites do ensaio: deploy simulado (sem provedor, domínio ou HTTPS reais), aceite da dona simulado, tasks em paralelo e subagentes **não** testados.

## Ajustes finos do piloto real (loja de cartas Pokémon, outro chat)

Anotados pelo usuário enquanto o primeiro projeto real roda no chat novo. Fazer **um ajuste final em conjunto** depois que o projeto estiver andando. Não mexer antes, salvo se o usuário pedir.

- [ ] **1. Onboarding de instalação.** Ao instalar a skill pela primeira vez, o Claude fez duas perguntas logo de cara. A skill deve guiar quem instala: dizer o que precisa ser preparado no ambiente (repositório, permissões, token do Netlify via formulário seguro, etc.) antes de começar. As duas perguntas feitas no chat novo foram: (a) **onde criar o projeto** (repositório separado ou subpasta) e (b) **se pode seguir com "app web, entrevista média"** (tipo e profundidade). O onboarding deve resolver as duas sem perguntar de forma solta: explicar a recomendação (um repositório por projeto, na raiz; tipo e profundidade inferidos do escopo, com confirmação em uma linha) e listar o que o usuário precisa preparar antes (criar o repositório no GitHub e anexá-lo à sessão, credencial do Netlify pelo formulário seguro). Pendente: ver se a mensagem completa do outro chat traz mais algum detalhe.

## Do Claude (código e documentação)

- [ ] **Ensaiar tasks em paralelo com subagentes** (`tasks_paralelas: sim`, worktrees): não foi testado
- [ ] **Ensaiar um deploy real** (provedor, domínio, HTTPS) num projeto pequeno e descartável, com autorização do usuário
- [ ] Tarefas delegadas a outra pessoa aparecerem como pendência no painel (item 7 do checklist do primeiro cliente)
- [ ] Verificação periódica das respostas do cliente (item 5): precisa de autorização do usuário para agendar
- [ ] Teste da instalação (`install.sh --projeto` e `--global`) numa sessão nova na nuvem
- [ ] Limpeza dos recursos de teste, só quando o usuário concordar: site Netlify `spec-flow-piloto` (id 2668d09f-eb99-42e1-a71d-fe516229c34c) e os artifacts antigos (entrevista piloto 3a3f6e69-26b4-4cc4-a155-642f3f8c7965, entrevista v2 ee0ed1d5-ae79-4ac5-a0b3-cdf451513389)
- [ ] Painel ao vivo: **inviável por enquanto**. A capacidade `files` dos artifacts lê arquivos de um projeto do Claude Code (id `chan_...`), e a sessão na nuvem não tem projeto. Hoje o painel é um instantâneo: depois do `render`, republicar o artifact. Reavaliar se o usuário passar a trabalhar dentro de um projeto.

## Do usuário (só ele pode fazer)

- [ ] Testar o link do cliente com **outra pessoa, em outro celular**
- [ ] Testar **upload de arquivo real** pela página do cliente (limite 8 MB) e conferir como o arquivo é baixado
- [ ] Conferir os **limites do plano gratuito do Netlify** (envios de formulário por mês, uploads)
- [ ] Decidir a **licença** do repositório público
- [ ] Decidir o que fazer com projetos confidenciais: a página do cliente não serve para eles (usar o chat)

## Riscos conhecidos, ainda não provados

- Fases 3 a 8 com código real, subagentes em paralelo e deploy de verdade (o ensaio cobre parte, em pequeno)
- Download autenticado dos arquivos enviados pelo cliente no Netlify
- Notificação quando o cliente responde (hoje só ao retomar a sessão)

## Histórico de versões (resumo)

- 2026-11-14: token do Netlify colado no chat foi revogado pelo usuário (pendência encerrada)
- 0.7.1: gate da CR, `rodar-teste`, `n-a` no checklist, `ready` com features alteradas, lições de smoke pós-deploy
- 0.7.0: abas Deploy e Cliente, seção 8 Deploy no SPEC.md (Change requests = 9, Histórico = 10), `migrar`, aviso de privacidade
- 0.6.x: controle total da lista do cliente (caixa única, reabrir, sugestões), painel por abas, testes por momento
