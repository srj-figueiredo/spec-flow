# Perguntas para o dono do negócio (link do cliente)

Muitas perguntas da entrevista são do **negócio**, não técnicas. O usuário (consultor) pode direcionar qualquer pergunta ao dono do negócio, que responde em linguagem de negócio num link próprio, sem conta e sem custo. Você traduz a resposta para a decisão técnica, e o usuário confirma.

## Dois links por projeto

| Link | Quem usa | Conteúdo |
|---|---|---|
| **Entrevista completa** (artifact, `reference/celular.md`) | o usuário | todas as perguntas, mais a opção "Direcionar ao dono do negócio" |
| **Página do cliente** (Netlify, este documento) | o dono do negócio | só as perguntas direcionadas a ele, reescritas em linguagem de negócio |

## Direcionar uma pergunta

Na página do usuário, cada pergunta (não respondida) tem o botão **Direcionar ao dono do negócio**. Ele abre a pergunta reescrita em linguagem de negócio, editável, e opções de resposta opcionais. Perguntas claramente de negócio já trazem a sugestão pronta (campo `neg` do banco). Nas técnicas, o campo vem vazio: o usuário pode escrever, ou você sugere com `SPEC cliente ID --sugerir --texto "..." [--opt ...]`.

Pelo chat: `SPEC cliente ID [--texto "..."] [--opt "..."]` direciona; `--remover` desfaz. Sem `--texto`, usa a sugestão do banco.

Estado: a pergunta vira **aguardando cliente** (roxo no painel e na página). Ela continua contando como pendente para sair da entrevista.

## Publicar a página do cliente

Pré-requisito: token do Netlify (nuvem: credencial salva para `api.netlify.com`; máquina local: `NETLIFY_AUTH_TOKEN`). Um site por projeto, nome `spec-flow-<slug-do-projeto>`.

1. `SPEC export-cliente [--intro "texto de abertura"]` gera `.spec/cliente/` (`index.html` com o formulário e `obrigado.html`).
2. `NETLIFY site-ensure spec-flow-<slug>` cria (ou acha) o site e devolve `id` e `url`. Guarde: `SPEC ficha cliente_site_id <id>` e `SPEC ficha cliente_url <url>`.
3. `NETLIFY deploy <id> .spec/cliente` publica.
4. **Primeira vez em cada site:** ligue a detecção de formulários (ferramenta do Netlify: `netlify-project-services-updater`, operação `update-forms`, `forms: "enabled"`) e **publique de novo** (passo 3). Confirme com `NETLIFY forms <id>`: deve listar o formulário `entrevista`.
5. Entregue o link ao usuário para enviar ao cliente. A página é pública (URL difícil de adivinhar); senha entra depois. **Não use para projeto confidencial.**

`NETLIFY` = `python3 ${CLAUDE_SKILL_DIR}/scripts/netlify.py`.

Limitação da nuvem: a rede do ambiente não alcança `*.netlify.app`, então você não consegue enviar um teste ao formulário por conta própria. Peça ao usuário para testar pelo celular.

## A página é um registro acumulativo (somente leitura)

A mesma página serve de **registro histórico** do cliente e de **formalização** das definições:

- **Respostas já dadas** aparecem no topo, em texto (não em campo), agrupadas por **rodada**, com data, nome de quem respondeu e um **código de verificação** do conteúdo. O cliente não consegue alterá-las.
- **Perguntas novas** aparecem embaixo, com campos para responder. A cada nova rodada, rode `SPEC export-cliente` e `NETLIFY deploy` no mesmo site: o registro cresce e nada some.
- Se o cliente reenviar a mesma pergunta (por exemplo, com a página antiga aberta), a nova resposta entra como **complemento**; a original continua intacta.
- O mesmo registro, com o mesmo código, é copiado para o `SPEC.md` (bloco de decisões, "Registro das respostas do cliente"), que continua a fonte de verdade.
- Sem perguntas novas, `export-cliente` gera a página só com o registro (a formalização final).

Limite honesto: "somente leitura" vale para o cliente. Quem controla a conta do Netlify ainda poderia editar o site. O código de verificação (calculado sobre perguntas, respostas e datas) permite detectar qualquer alteração depois, comparando com o do `SPEC.md`, e os envios originais ficam guardados no Netlify.

## Receber e traduzir as respostas

1. `NETLIFY submissions <id> --form entrevista > envios.json` (todos os envios, do mais antigo ao mais novo).
2. `SPEC import-cliente envios.json`: cada resposta é **acrescentada** ao registro da pergunta (nunca sobrescreve) e a pergunta continua em "aguardando cliente" até você traduzir.
3. Para cada resposta: leia o que o cliente disse (palavras dele), proponha a **decisão técnica** e o motivo, e mostre ao usuário. Com o "ok": `SPEC answer <ID> --text "<decisão técnica>"` (ou `--opt N` se uma opção cobre). Dúvida do cliente que gera pergunta nova: `SPEC add` e, se for de negócio, `SPEC cliente`.
4. Se for preciso perguntar mais ao cliente (aprofundamento), crie a pergunta (`SPEC add` + `SPEC cliente`), rode `SPEC export-cliente` e `NETLIFY deploy` no mesmo site: abre-se a próxima rodada.

## Formalização por e-mail

Ao fim das respostas, quando as definições estiverem confirmadas, monte um e-mail de **formalização das definições** ao cliente, em linguagem de negócio: o que foi decidido, o que ficou como pendência, próximos passos. Deixe como **rascunho no Gmail** (`create_draft`) para o usuário revisar e enviar. Nunca envie ao cliente sozinho.

## Limpeza

Sites de piloto: `NETLIFY delete-site <id>`. Só apague um site de cliente com autorização do usuário.
