# Testes: decidir o momento e ser autônomo

Não existe uma regra única de "testar no fim". **Cada teste é analisado e colocado no momento em que faz sentido**, e o que puder rodar sozinho roda sozinho. O plano vive na seção 7 do `SPEC.md`, nasce junto com as tasks (Fase 4) e é reavaliado a cada fase.

## Formato (seção 7)

```
### TS-001 · Cadastro de paciente cria e busca
- estado: pendente
- feature: F-001
- tipo: unidade | integracao | e2e | aceite | acessibilidade | carga | seguranca | smoke-pos-deploy
- quando: durante-build | antes-deploy | pos-deploy
- modo: autonomo | manual
- como: comando ou roteiro que prova
- criterio: o que precisa ser verdade para passar
- motivo_momento: por que neste momento
- evidencia: (preenchido ao executar)
```

Estados: `pendente`, `em-execucao`, `passou`, `falhou`, `bloqueado`, `n-a` (exige `motivo_momento`). Ids novos: `SPEC new-id TS`. Resultado: `SPEC set-teste TS-001 passou --evidencia docs/evidencias/ts-001.log`.

## Como escolher o momento

Pergunte, nesta ordem, o que o teste precisa para rodar:

| Depende só de... | Momento | Exemplos |
|---|---|---|
| código isolado | `durante-build` | unidade, regras de cálculo, validações, componentes |
| o app inteiro rodando (banco, serviços, ambiente de teste) | `antes-deploy` | integração, e2e do fluxo principal, acessibilidade, segurança (dependências, checklist OWASP), desempenho básico |
| algo que só existe em produção | `pos-deploy` | site responde, HTTPS e domínio, e-mail e DNS, pagamento em modo de teste, fluxo principal em produção, monitoramento e alertas |
| a opinião de uma pessoa | `antes-deploy` se houver ambiente de homologação; senão `pos-deploy` | aceite do dono do negócio, "ficou como imaginei?" |

Na dúvida, o mais cedo possível que ainda seja realista. Se descobrir que um teste só faz sentido depois do deploy, **mude `quando` e explique em `motivo_momento`**; não force.

## Autonomia

- **Rode sem pedir licença** tudo que é local ou de ambiente de teste: unidade, integração, e2e (Playwright, quando o projeto tiver ou for razoável incluir), análise de dependências, linters, verificação de acessibilidade, scripts de fumaça.
- Faltou ferramenta? Instale como dependência de desenvolvimento do próprio projeto quando for seguro e registre no histórico; se não der, vire teste `manual` com o motivo.
- **Peça confirmação antes** do que tem efeito no mundo real: pagamento real, e-mail ou mensagem para pessoas reais, carga contra produção, qualquer operação que apague ou altere dados reais.
- **Sempre deixe evidência** em `docs/evidencias/` (saída do comando, captura de tela, relatório) e cite o caminho em `--evidencia`. Teste sem evidência não conta como feito.
- **Falhou:** não avance de fase. Ache a causa, crie a task de correção, conserte, rode de novo. Depois de 3 tentativas sem sucesso, mostre ao usuário o que tentou e o que descobriu.
- **Testes manuais:** roteiro curto, passo a passo, com o resultado esperado em cada passo. O usuário executa e responde "passou" ou "falhou, porque...".

## O que o motor garante

- `tasks → construcao`: toda feature precisa de ao menos um teste planejado (ou `n-a` justificado).
- `construcao → testes`: testes `durante-build` passados, tasks feitas, features em teste.
- `testes → deploy`: testes `durante-build` e `antes-deploy` passados (ou `n-a`). Falhou ou bloqueado barra.
- `deploy → manutencao`: features entregues e testes `pos-deploy` passados.
- O painel tem uma aba **Testes** com momento, modo, estado e evidência de cada um.

## Mudanças (change requests)

Cada change request ganha seus testes, incluindo **regressão** do que a mudança pode quebrar, escolhidos pelo mesmo critério de momento.
