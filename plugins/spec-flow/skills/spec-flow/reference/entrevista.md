# Entrevista de requisitos: como conduzir

Você faz o papel de analista de requisitos. A meta é **não deixar lacuna** e **não inferir nada** que o usuário deveria decidir.

## 1. O escopo comanda; a base é checklist

O usuário descreve o escopo livremente e **você gera a entrevista a partir dele**. O banco traz perguntas que todo projeto precisa decidir (hospedagem, login, testes, deploy...), mas serve só como **checklist para não esquecer o básico**: para cada uma, ou o escopo já responde (`dica`), ou não se aplica (`descartar` com motivo, que fica registrado), ou fica. O total de perguntas cresce durante a entrevista, e o contador diz "até agora". Perguntas do escopo ficam **antes** da base dentro do bloco.

## 2. Do briefing às perguntas

Leia o briefing três vezes, com três perguntas:

1. **O que já foi dito?** Cada fato explícito vira `dica` na pergunta da base correspondente. Exemplo: o briefing diz "hoje usamos uma planilha de clientes" → `SPEC dica D-01 "planilha de clientes existente"` e `SPEC rec D-01 2 --nota "o briefing cita planilha"`. A pergunta continua pendente: o usuário confirma.
2. **O que foi dito pela metade?** Palavra vaga ("rápido", "simples", "integrar com o sistema deles", "relatórios") é pergunta do escopo.
3. **O que um sistema assim sempre precisa e o briefing calou?** Compare com o tipo de negócio (veja os eixos abaixo).

## 3. Como escrever uma pergunta do escopo

- Uma decisão por pergunta, em linguagem do negócio.
- **Opção 1 = o que você faria**, com motivo no `--why`. Depois 2 ou 3 alternativas realmente adequadas (não opções de enfeite). A resposta livre e o "pular" o motor já oferece.
- `--motivo "briefing: <trecho>"` ou `--motivo "resposta N-02"` para o usuário ver de onde veio.
- Pergunta de múltipla escolha só quando as opções não se excluem (`--multi`).
- Bloco: use um dos existentes (`negocio`, `escopo`, `regras`, `dados`, `integracoes`, `stack`, `arquitetura`, `seguranca`, `testes`, `deploy`, `entrega`, `manutencao`) ou crie um com `--bloco-nome`.

## 4. Eixos para procurar lacunas (varredura)

Antes de `SPEC varredura`, passe por todos e adicione o que faltar:

- **Atores e permissões**: quem usa, quem administra, quem só consulta; o que cada um pode ver e alterar.
- **Entidades e ciclo de vida**: o que é guardado, como nasce, muda de estado, é cancelado, arquivado ou apagado.
- **Regras de negócio e exceções**: cálculos, prazos, limites, o que acontece quando algo dá errado ou foge do normal.
- **Dinheiro e obrigações legais**: cobrança, impostos e nota fiscal, contratos, LGPD, termos de uso, retenção de dados.
- **Integrações e falhas**: cada sistema externo; o que fazer quando ele estiver fora do ar.
- **Entrada e saída de dados**: importação, exportação, relatórios, migração do que existe hoje.
- **Comunicação**: e-mails, avisos, WhatsApp; texto e momento de cada um.
- **Telas e estados** (quando há interface): vazio, carregando, erro, sucesso; celular e desktop; acessibilidade; identidade visual.
- **Operação**: quem administra no dia a dia, suporte, monitoramento, backup, custos recorrentes.
- **Requisitos não funcionais**: desempenho, disponibilidade, segurança, privacidade.
- **Dependências do cliente**: conteúdo, contas, domínios, acessos, aprovações que travam o projeto se não chegarem.
- **Aceite e riscos**: como o usuário vai testar e aprovar; o que mais preocupa o cliente.

Registre ao final: "Varredura: N perguntas adicionadas" e rode `SPEC varredura`.

## 5. Bypass

- Pular é um direito do usuário e é registrado. Não insista, mas **avise o risco em uma frase** quando a pergunta for estrutural (banco, multi-tenant, autenticação, LGPD).
- Pergunta pulada vira pendência no painel e linha `PENDENTE (bypass)` no bloco de decisões do `SPEC.md`.
- Bypass em lote só se o usuário pedir.

## 6. Perguntas que dependem de outras

Algumas perguntas só aparecem conforme uma resposta anterior (ex.: meio de pagamento só se houver pagamento). O motor cuida disso; se criar pergunta do escopo condicional, simplesmente adicione depois de ter a resposta que a justifica.
