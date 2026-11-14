# Deploy: checklist, publicações e aba do painel

Tudo vive na **seção 8 do SPEC.md**. O painel (aba *Deploy*) só lê dali.

## Formato (não edite à mão se puder usar os comandos)

```
- ambiente: producao
- url: https://...            (gravada por deploy-registrar quando produção fica ok)
- como_publicar: ...
- como_reverter: ...
- monitoramento: ...
- dominio: ...

### Checklist
- [ ] CK-001 · Ambiente de produção criado no provedor
  - nota: decisões da entrevista (S-02: ...)
  - evidencia: docs/evidencias/ambiente.txt

### Publicações
- 2026-11-14 · producao · ok · url=https://... commit=abc1234 nota livre
```

Marcas do checklist: `[ ]` pendente, `[~]` andamento, `[x]` feito, `[!]` bloqueado, `[-]` n-a (não se aplica: `set-deploy CK-002 n-a --evidencia "por quê"`, a justificativa é obrigatória; conta como concluído). Item `feito` sem evidência aparece na aba como "sem evidência registrada".
Resultado de publicação: `ok`, `falhou` ou `revertido`.

## Fluxo

1. `deploy-init` cria 9 itens a partir das decisões da entrevista (DP-01..05, S-02, A-03, A-05, SG-03, D-03, D-05). Decisão não registrada vira "definir agora" na nota: resolva com o usuário antes de executar o item.
2. Para cada item: execute (confirmando antes de qualquer ação externa), guarde a prova em `docs/evidencias/` e rode `set-deploy CK-00X feito --evidencia docs/evidencias/arquivo`. Evidência dentro de `docs/` vira link na aba.
3. `deploy-info` para url, domínio, como publicar de novo, como reverter, monitoramento.
4. `deploy-registrar` a cada publicação, inclusive as que falharam e as revertidas: o histórico de publicações é parte do que o cliente paga.
5. **Confirme que a versão nova é a que está no ar** antes de qualquer teste (processo antigo, cache ou deploy que não trocou nada respondem como se estivesse tudo certo). testes `pos-deploy` rodam logo depois (ver `testes.md`). Falhou em produção: reverter conforme `como_reverter`, registrar `revertido`.
6. Porta de saída (`fase manutencao`): checklist todo `feito`, ao menos uma publicação `producao ok`, `url` preenchida, features `entregue`, testes `pos-deploy` passados. `--forcar` existe, mas diga ao usuário o que está sendo pulado.

## Projetos criados antes da seção 8

`migrar` insere a seção Deploy e renumera (Change requests = 9, Histórico = 10). É idempotente.

## O que a aba mostra

Endereço de produção e última publicação, dados de operação, checklist com barra de progresso e evidências, tabela de publicações, testes pós-deploy e as decisões da entrevista que guiam o deploy. Itens bloqueados e checklist aberto aparecem como pendências na Visão geral.
