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
- **Use `rodar-teste`** para tudo que é comando: `SPEC rodar-teste TS-001` (ou `--cmd "..."`) roda, guarda a saída em `docs/evidencias/ts-001-<data>.log` e registra `passou` ou `falhou` **pelo código de saída**. Nunca encadeie `set-teste ... passou` depois de um comando sem ler o resultado: no ensaio isso registrou "passou" num teste que tinha falhado. `set-teste` fica para o que não é comando (roteiro manual, captura de tela).
- **Sempre deixe evidência** em `docs/evidencias/` (saída do comando, captura de tela, relatório) e cite o caminho em `--evidencia`. Teste sem evidência não conta como feito.
- **Falhou:** não avance de fase. Ache a causa, crie a task de correção, conserte, rode de novo. Depois de 3 tentativas sem sucesso, mostre ao usuário o que tentou e o que descobriu.
- **Teste que escreve dados em produção** (smoke pós-deploy): use dado identificável (nome `SMOKE-...`), apague no fim e registre na evidência que apagou. Antes de rodar, **confirme que a versão nova é a que responde** (processo antigo pode seguir ocupando a porta; no ensaio, o smoke bateu na versão velha).
- **Testes manuais:** roteiro curto, passo a passo, com o resultado esperado em cada passo. O usuário executa e responde "passou" ou "falhou, porque...". Na evidência, escreva **quem aceitou, como e quando** (ex.: "aceite da Lu por áudio, 14/11"); aceite simulado nunca entra como real.

## O que o motor garante

- `tasks → construcao`: toda feature precisa de ao menos um teste planejado (ou `n-a` justificado).
- `construcao → testes`: testes `durante-build` passados, tasks feitas, features em teste.
- `testes → deploy`: testes `durante-build` e `antes-deploy` passados (ou `n-a`). Falhou ou bloqueado barra.
- `deploy → manutencao`: features entregues e testes `pos-deploy` passados.
- `cr-set CR-00X entregue`: tasks e testes das features da CR concluídos (qualquer momento); ao entregar, as features `alterada` voltam a `entregue`. `--forcar` pula, e você diz ao usuário o que foi pulado.
- O painel tem uma aba **Testes** com momento, modo, estado e evidência de cada um.

## Mudanças (change requests)

Cada change request ganha seus testes, incluindo **regressão** do que a mudança pode quebrar, escolhidos pelo mesmo critério de momento.
