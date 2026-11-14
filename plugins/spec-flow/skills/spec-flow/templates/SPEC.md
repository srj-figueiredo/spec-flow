# {{NOME}}

> Fonte de verdade do projeto, mantida pela skill spec-flow. Leia este arquivo inteiro antes de mexer no projeto e atualize-o junto com cada mudança. O bloco de decisões é gerado por `spec.py sync`; o resto é editado direto.

## 0. Ficha

- fase: entrada
- tipo: {{TIPO}}
- profundidade: {{PROF}}
- tasks_paralelas: não
- entrevista_web: —
- varredura_lacunas: não
- criado: {{DATA}}

## 1. Objetivo

(preencher)

## 2. Escopo e requisitos

### Dentro do escopo

(preencher)

### Fora do escopo

(preencher)

## 3. Decisões

<!-- decisoes:inicio -->
(a entrevista ainda não começou)
<!-- decisoes:fim -->

## 4. Como está hoje

Stack, arquitetura, como rodar localmente e como publicar. Esta seção descreve o sistema como ele é agora, não como foi planejado.

(preencher)

## 5. Entregas

Cada entrega agrupa features que fazem sentido juntas para o negócio. Formato: `- E1 · Nome · objetivo`.

(preencher)

## 6. Features

<!--
Formato de cada feature (os campos com "- " no início da linha são lidos pelo script):

### F-001 · Título da feature
- estado: proposta
- entrega: E1
- valor: o que isso muda para o negócio, em uma frase
- aceite:
  - critério verificável 1
  - critério verificável 2
- tasks:
  - [ ] T-001 · título da task
    - dono: agente-backend
    - toca: src/models/cliente.py, tests/test_cliente.py
    - depende: —
    - aceite: como saber que a task está pronta
    - teste: comando ou cenário que prova

Estados da feature: proposta, aprovada, em-andamento, em-teste, entregue, alterada, descartada.
Marcas da task: [ ] pendente, [~] em andamento, [x] feita, [!] bloqueada.
-->

## 7. Testes

O plano de testes nasce junto com as features e é executado no **momento que fizer sentido para cada caso**: durante a construção, antes do deploy ou só depois dele. Quanto mais autônomo, melhor: o que dá para rodar sozinho roda sozinho, e só vira roteiro manual o que depende de uma pessoa.

<!--
Formato de cada teste (os campos com "- " no início da linha são lidos pelo script):

### TS-001 · Cadastro de paciente cria e busca
- estado: pendente
- feature: F-001
- tipo: unidade | integracao | e2e | aceite | acessibilidade | carga | seguranca | smoke-pos-deploy
- quando: durante-build | antes-deploy | pos-deploy
- modo: autonomo | manual
- como: comando ou roteiro que prova (ex.: pytest tests/test_paciente.py)
- criterio: o que precisa ser verdade para passar
- motivo_momento: por que este momento (ex.: depende do domínio no ar)
- evidencia: caminho de log, captura de tela ou saída (preenchido ao executar)

Estados: pendente, em-execucao, passou, falhou, bloqueado, n-a (não se aplica, com motivo).
-->

## 8. Deploy

Onde o sistema está no ar, como publicar de novo, como reverter e o checklist da publicação. Preenchido na fase de Deploy a partir das decisões da entrevista (`deploy-init` monta o esqueleto).

<!--
Formato (linhas com "- " no início são lidas pelo script):

- url: https://...                (endereço de produção)
- ambiente: producao
- como_publicar: passo a passo curto
- como_reverter: passo a passo curto
- monitoramento: o que avisa quando cai
- dominio: onde o domínio e o DNS estão

### Checklist
- [ ] CK-001 · Segredos e variáveis configurados no provedor
  - nota: o que decidimos / onde
  - evidencia: docs/evidencias/arquivo

Marcas: [ ] pendente, [~] em andamento, [x] feito, [!] bloqueado.

### Publicações
- 2026-11-14 · producao · ok · url=https://... commit=abc1234 nota livre
-->

(nenhuma publicação ainda)

## 9. Change requests

Mudanças pedidas depois da primeira entrega. Formato: `### CR-001 · título`, com `estado`, `features`, `motivo`.

## 10. Histórico

- {{DATA}} · projeto criado com a spec-flow
