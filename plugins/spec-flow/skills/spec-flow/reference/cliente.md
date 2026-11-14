# Perguntas para o dono do negócio (link do cliente)

Muitas perguntas da entrevista são do **negócio**, não técnicas. O usuário (consultor) pode direcionar qualquer pergunta ao dono do negócio, que responde em linguagem de negócio num link próprio, sem conta e sem custo. Você traduz a resposta para a decisão técnica, e o usuário confirma.

## Dois links por projeto

| Link | Quem usa | Conteúdo |
|---|---|---|
| **Entrevista completa** (artifact, `reference/celular.md`) | o usuário | todas as perguntas, mais a opção "Direcionar ao dono do negócio" |
| **Página do cliente** (Netlify, este documento) | o dono do negócio | só as perguntas direcionadas a ele, reescritas em linguagem de negócio |

## Lista inicial do cliente (você sugere, o usuário decide com uma caixa)

Cada pergunta tem **uma caixa "📤 Enviar ao dono do negócio"** na página do usuário. **Marcada = vai para a página do cliente; desmarcada = não vai.**

1. **Suas sugestões já vêm marcadas** (selo 📌 "sugerida por mim"): `SPEC sugerir-cliente --ids A,B,C` (texto pronto do banco) ou `SPEC cliente <ID> --sugerir --texto "..."` (a sua versão). Regra de ouro: o dono do negócio responde sobre o **negócio dele** (rotina, clientes, regras, preferências), nunca sobre tecnologia.
2. **Ligar e desligar são simétricos e independentes.** O usuário marca e desmarca quantas vezes quiser, sem afetar as outras. Cada decisão tem carimbo de tempo e **a mais recente vence**, mesmo chegando fora de ordem. Desmarcar uma sugestão sua a torna **dispensada** (você não remarca).
3. **Qualquer pergunta pode ser marcada pelo usuário**, mesmo as que você não sugeriu: todas têm a pergunta de negócio pronta. Marcada, ele vê a pergunta e **✎ Editar a pergunta do cliente** (texto, opções, arquivo).
4. Antes de publicar, mostre a lista final (a que ele deixou marcada) e confirme. `SPEC lista-cliente` mostra: as que vão, as dispensadas e as demais com texto pronto.
5. `SPEC export-cliente` **já inclui as marcadas** (sem passo extra) e você publica. `cliente-lote` é opcional (só torna as escolhas explícitas).

## Responder e direcionar são independentes (e dá para reabrir)

- Uma pergunta **marcada para o cliente sempre vai para a página dele**, mesmo que o usuário a tenha respondido ou pulado. Quem responde primeiro não "cancela" o envio.
- A resposta do usuário vira **provisória**: o painel e o SPEC mostram "Sua resposta provisória: ... + aguardando cliente". Quando o cliente responde, vale a verificação de impacto e a decisão pode mudar.
- A entrevista **não fecha** com pergunta respondida que ainda aguarda o cliente (a não ser por bypass).
- O usuário pode **reabrir** qualquer pergunta (botão ↺ **Reabrir pergunta**, ou `SPEC reabrir ID`): a resposta sai, a anterior vai para o histórico da pergunta e o direcionamento ao cliente **continua**. Também pode direcionar depois de responder, sem perder a resposta, ou parar de direcionar enquanto o cliente não respondeu ("Não direcionar mais").
- Se o cliente já respondeu, a pergunta não é mais direcionável: faça uma pergunta de aprofundamento (`SPEC add` + `SPEC cliente`).

## Toda pergunta já tem a versão para o dono do negócio

Ao clicar em **Direcionar ao dono do negócio**, o painel **sempre abre com uma pergunta pronta**, em linguagem de negócio, com as opções de resposta, para o usuário só conferir, editar e enviar, mesmo nas técnicas que você não marcou. As técnicas viram uma pergunta sobre o negócio que permite decidir o ponto técnico (banco de dados → "quanta informação você espera guardar nos próximos anos?"; hospedagem → "quanto aceita gastar por mês?"). Garantias:

- as 66 perguntas da base trazem esse texto (`atualizar-textos` o aplica a projetos mais antigos);
- `SPEC add` **exige** `--neg` (e `--neg-opt`), então nenhuma pergunta do escopo nasce sem a versão de negócio;
- a tradução da resposta para a decisão técnica continua sendo sua (e a verificação de impacto também).

## Direcionar uma pergunta

Na página do usuário, cada pergunta (não respondida) tem o botão **Direcionar ao dono do negócio**. Ele abre a pergunta reescrita em linguagem de negócio, editável, e opções de resposta opcionais. Perguntas claramente de negócio já trazem a sugestão pronta (campo `neg` do banco). Nas técnicas, o campo vem vazio: o usuário pode escrever, ou você sugere com `SPEC cliente ID --sugerir --texto "..." [--opt ...]`.

Pelo chat: `SPEC cliente ID [--texto "..."] [--opt "..."]` direciona; `--remover` desfaz. Sem `--texto`, usa a sugestão do banco.

Estado: a pergunta vira **aguardando cliente** (roxo no painel e na página). Ela continua contando como pendente para sair da entrevista.

## Publicar a página do cliente

Pré-requisito: token do Netlify (nuvem: credencial salva para `api.netlify.com`; máquina local: `NETLIFY_AUTH_TOKEN`). Um site por projeto, nome `spec-flow-<slug-do-projeto>` mais um sufixo aleatório.

1. `SPEC export-cliente [--intro "texto de abertura"]` gera `.spec/cliente/` (`index.html` com o formulário e `obrigado.html`).
2. `NETLIFY site-ensure spec-flow-<slug> --aleatorio --ficha .` cria o site com endereço impossível de adivinhar, devolve `id` e `url` e **grava `cliente_site_id` e `cliente_url` na Ficha** (é isso que faz a retomada automática buscar as respostas do cliente).
3. `NETLIFY deploy <id> .spec/cliente` publica.
4. **Primeira vez em cada site:** ligue a detecção de formulários (ferramenta do Netlify: `netlify-project-services-updater`, operação `update-forms`, `forms: "enabled"`) e **publique de novo** (passo 3). Confirme com `NETLIFY forms <id>`: deve listar o formulário `entrevista`.
5. Entregue o link ao usuário para enviar ao cliente.

**Privacidade do link:** é privado por obscuridade, sem senha: quem tiver o endereço acessa; ninguém acha por acaso (endereço aleatório, `robots.txt` e `X-Robots-Tag: noindex`). Peça ao usuário para não divulgar o link. A página mostra respostas do cliente, então **não use este canal em projeto confidencial**.

`NETLIFY` = `python3 ${CLAUDE_SKILL_DIR}/scripts/netlify.py`.

Limitação da nuvem: a rede do ambiente não alcança `*.netlify.app`, então você não consegue enviar um teste ao formulário por conta própria. Peça ao usuário para testar pelo celular.

## Arquivos e design

**Upload de arquivo.** Se o cliente precisar enviar algo (planilha, logotipo, contrato), direcione a pergunta com `--arquivo` (e `--arquivo-desc "o que enviar"`): a página ganha o campo de envio.

- Limites do Netlify Forms: **8 MB por envio** (a requisição inteira, somando todos os campos), **um arquivo por campo** (um campo por pergunta) e **30 segundos** de limite de envio.
- A página avisa o limite ao cliente e **barra arquivos acima de 7,5 MB**, marcando sozinha a opção **"Meu arquivo é maior que 8 MB"**: nesse caso o desenvolvedor entra em contato para pegar o arquivo. Na importação isso vira "Arquivo grande: o desenvolvedor entrará em contato para pegar" e é pendência sua.
- A página pede para não enviar senhas nem documentos pessoais sensíveis (arquivo com dado pessoal exige cuidado extra no Netlify).
- Ainda **não verificado**: o formato em que o arquivo aparece na leitura dos envios e se o link para baixar exige login no Netlify. A importação aceita objeto (`url`, `filename`, `size`) ou texto. Confira o primeiro arquivo real de cada projeto.

**Perguntas de design.** Nenhuma pergunta de design vai ao cliente só com texto. Marque com `--design` (a base já marca U-06) e ofereça **opções visuais** e/ou **links de referência**, pelo menos um:

- `--visual paleta` (cores), `--visual layout` (desenhos da organização da tela), `--visual tipografia` (estilo de letra): cada tipo mostra opções padrão como cartões visuais para tocar.
- Opções próprias: `--visual-opt "paleta|Nome|#111111,#f59e0b,#fff7ed"`, `--visual-opt "layout|Nome|painel"` (hero, painel, grade ou lista), `--visual-opt "tipografia|Nome|Georgia, serif"`.
- Links para o cliente olhar: `--ref "Rótulo|https://..."` (repita). O cliente também ganha um campo para colar os links de sites que ele acha bonitos.
- Se uma pergunta de design chegar ao cliente sem nada disso, `export-cliente` aplica paleta e layout padrão e avisa.
- Use referências reais que você conferiu; não invente endereços.

## Verificação de impacto (obrigatória a cada resposta do cliente)

Há duas listas, a completa e a do negócio, e **a resposta do cliente pode mudar uma decisão já fechada na lista completa**. Exemplo: o cliente diz "os lucros são só meus", e a decisão de perfis (administrador e gerente com o mesmo acesso a relatórios) deixa de valer.

Depois de **todo** `import-cliente`:

1. `SPEC impacto` mostra as respostas novas e todas as decisões já tomadas, por bloco.
2. Para cada resposta nova, pergunte: ela contradiz, restringe ou muda alguma dessas decisões? Considere também decisões de outros blocos (permissões, dados, segurança, prazo, custo, stack).
3. Para cada decisão afetada: `SPEC revisar ID --motivo "<o que mudou>" --origem <ID da pergunta do cliente>`. Ela vira **a revisar** (laranja, com a decisão anterior), conta como pendente e impede sair da entrevista.
4. Mostre ao usuário a lista de afetadas e a proposta de nova decisão. Com o "ok": `SPEC answer ID ...` (a decisão anterior vai para o histórico da pergunta e a revisão se encerra) ou `SPEC revisao-ok ID --nota "mantida porque..."`.
5. Só então `SPEC impacto-ok`. Sem isso, `gate` e `fase spec` barram, e o painel mostra a pendência.

Se a resposta do cliente também gerar dúvida nova, crie a pergunta (`SPEC add`) e, se for do negócio, direcione (`SPEC cliente`): abre a próxima rodada.

## A página é um registro acumulativo (somente leitura)

A mesma página serve de **registro histórico** do cliente e de **formalização** das definições:

- **Respostas já dadas** aparecem no topo, em texto (não em campo), agrupadas por **rodada**, com data, nome de quem respondeu e um **código de verificação** do conteúdo. O cliente não consegue alterá-las.
- **Perguntas novas** aparecem embaixo, com campos para responder. A cada nova rodada, rode `SPEC export-cliente` e `NETLIFY deploy` no mesmo site: o registro cresce e nada some.
- Se o cliente reenviar a mesma pergunta (por exemplo, com a página antiga aberta), a nova resposta entra como **complemento**; a original continua intacta.
- O mesmo registro, com o mesmo código, é copiado para o `SPEC.md` (bloco de decisões, "Registro das respostas do cliente"), que continua a fonte de verdade.
- Sem perguntas novas, `export-cliente` gera a página só com o registro. **Ela é a formalização das definições**: não é preciso e-mail à parte.

Limite honesto: "somente leitura" vale para o cliente. Quem controla a conta do Netlify ainda poderia editar o site. O código de verificação (calculado sobre perguntas, respostas e datas) permite detectar qualquer alteração depois, comparando com o do `SPEC.md`, e os envios originais ficam guardados no Netlify.

## Receber e traduzir as respostas

1. `NETLIFY submissions <id> --form entrevista > envios.json` (todos os envios, do mais antigo ao mais novo).
2. `SPEC import-cliente envios.json`: cada resposta é **acrescentada** ao registro da pergunta (nunca sobrescreve) e a pergunta continua em "aguardando cliente" até você traduzir.
3. Para cada resposta: leia o que o cliente disse (palavras dele), proponha a **decisão técnica** e o motivo, e mostre ao usuário. Com o "ok": `SPEC answer <ID> --text "<decisão técnica>"` (ou `--opt N` se uma opção cobre). Dúvida do cliente que gera pergunta nova: `SPEC add` e, se for de negócio, `SPEC cliente`.
4. Se for preciso perguntar mais ao cliente (aprofundamento), crie a pergunta (`SPEC add` + `SPEC cliente`), rode `SPEC export-cliente` e `NETLIFY deploy` no mesmo site: abre-se a próxima rodada.

## Limpeza

Sites de piloto: `NETLIFY delete-site <id>`. Só apague um site de cliente com autorização do usuário.


## Aba Cliente do painel e página desatualizada

A aba *Cliente* mostra: endereço da página e se está **publicada**, **gerada mas não publicada** ou **desatualizada** (marcou ou desmarcou perguntas depois de gerar); as perguntas **aguardando** o dono do negócio (com sua resposta provisória e a origem: 📌 sugerida por você ou escolhida pelo usuário); as **respostas recebidas** por rodada, travadas, com código do registro, e se já foram **traduzidas** e tiveram o **impacto verificado**; e as sugestões que o usuário dispensou.

- `export-cliente` guarda o que foi gerado. Depois de gerar, **sempre publique**: `netlify.py deploy SITE_ID .spec/cliente --ficha .`. O `--ficha .` grava `cliente_publicada_em`, e é isso que o painel compara.
- Página gerada e não publicada = o cliente não vê nada. Isso aparece como pendência na Visão geral.
- Perguntas marcadas ou desmarcadas depois da geração = página desatualizada: rode `export-cliente` e publique de novo no mesmo site (o endereço não muda).
