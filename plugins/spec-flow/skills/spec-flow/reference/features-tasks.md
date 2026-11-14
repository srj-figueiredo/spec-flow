# Features, entregas e tasks

## Cortando o escopo em features

Uma **feature** é uma fatia que o cliente reconhece como valor ("o paciente marca consulta online"), atravessando as camadas necessárias (tela, regra, dados). Não é "criar tabela de pacientes" nem "montar a API".

Teste rápido: a feature poderia ser demonstrada ao cliente sozinha? Se não, ou ela é pequena demais (junte) ou é só uma task (mova para dentro de outra feature).

Tamanho bom: entregável em alguns dias de trabalho. Maior que isso, divida por fluxo ou por perfil de usuário.

### Entregas (fases)

Agrupe features em **entregas** na seção 5: `- E1 · MVP · objetivo em uma frase`. Regras:

- **E1 é o menor conjunto que já gera valor** e pode ir ao ar. Pergunta-guia: "se só isto existisse, o cliente já pagaria?"
- Cada entrega seguinte acrescenta valor claro (novo perfil, nova automação, relatório).
- O que não entra agora fica registrado como feature `proposta` em entrega posterior, não some.
- Se o usuário preferir entrega única, use só `E1`.

### Critérios de aceite

Verificáveis por quem testa, sem interpretação:

- Bom: "Recepcionista busca paciente por nome ou CPF e vê o resultado em até 2 segundos."
- Ruim: "A busca é rápida e fácil."

Três a cinco por feature. Cada um deve virar um teste (automático ou roteiro manual).

## Formato no SPEC.md (seção 6)

```
### F-001 · Cadastro de pacientes
- estado: proposta
- entrega: E1
- valor: a recepção deixa de usar planilha
- aceite:
  - criar, editar e buscar paciente
  - CPF inválido é recusado com mensagem clara
- tasks:
  - [ ] T-001 · Modelo e migração de Paciente
    - dono: agente-backend
    - toca: src/models/paciente.py, migrations/
    - depende: —
    - aceite: tabela criada com os campos do SPEC
    - teste: pytest tests/test_paciente.py
```

Ids novos: `SPEC new-id F`, `SPEC new-id T`. Estados da feature: `proposta, aprovada, em-andamento, em-teste, entregue, alterada, descartada`. Marcas da task: `[ ]` pendente, `[~]` andamento, `[x]` feita, `[!]` bloqueada.

## Tasks que um agente independente consegue executar

Uma task é boa quando alguém (ou um subagente) que só leu **a task e o SPEC.md** consegue fazê-la e provar que ficou pronta.

- **Uma intenção por task**, tamanho de poucas horas.
- `toca`: lista exata de arquivos ou pastas que a task cria ou altera. É o que evita conflito entre agentes.
- `depende`: ids das tasks que precisam estar `feitas` antes (use `—` se não há).
- `aceite`: o resultado observável. `teste`: o comando ou cenário que prova (de preferência um teste automático escrito junto).
- `dono`: rótulo do tipo de agente (`agente-backend`, `agente-frontend`, `agente-testes`); só é usado no painel.
- Ordem natural: dados e regras antes de telas; testes de aceite junto da task, não no fim.

### Paralelo

Só com `tasks_paralelas: sim`. O `check` barra duas tasks que podem rodar juntas e disputam arquivos. Resolva declarando dependência entre elas ou separando os arquivos (por exemplo, `shared/` vira uma task própria que as outras aguardam). `SPEC ready` mostra o lote que pode ir junto.

## Estado da feature ao longo da construção

`aprovada` → (primeira task iniciada) `em-andamento` → (todas as tasks feitas) `em-teste` → (usuário aprova) `entregue`. Se o aceite falhar, volte para `em-andamento` e crie a task de correção.

## Testes das features

Cada feature precisa de ao menos um teste no plano (seção 7), escolhido para o momento certo e, sempre que possível, autônomo. Os critérios de aceite da feature viram a base dos testes de aceite. Veja `testes.md`.
