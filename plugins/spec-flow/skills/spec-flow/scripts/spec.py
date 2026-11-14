#!/usr/bin/env python3
"""spec.py: motor da skill spec-flow. Somente biblioteca padrão.

Uso: python3 spec.py <comando> [opções]      (veja `spec.py ajuda`)
O projeto é localizado subindo pastas até achar SPEC.md (ou use --raiz).
"""
import argparse
import datetime
import hashlib
import html as html_mod
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import specmd as S  # noqa: E402
import cliente_html as CH  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
RANK = {"p": 1, "m": 2, "c": 3}
SNIPPET_MARCA = "<!-- spec-flow -->"
SNIPPET = f"""{SNIPPET_MARCA}
## spec-flow (obrigatório no início de toda sessão)

Este projeto é conduzido pela skill `spec-flow`. No começo de TODA sessão, antes de qualquer outra coisa,
invoque a skill `spec-flow`: ela mostra em que fase o projeto está, o que falta e retoma a entrevista de onde parou.
`SPEC.md` é a fonte de verdade: leia antes de mexer no projeto e atualize junto com cada mudança.
"""


# ---------- localização e estado ----------
def achar_raiz(inicio):
    d = os.path.abspath(inicio)
    while True:
        if os.path.isfile(os.path.join(d, "SPEC.md")):
            return d
        pai = os.path.dirname(d)
        if pai == d:
            return None
        d = pai


def caminhos(raiz):
    return {
        "spec": os.path.join(raiz, "SPEC.md"),
        "entrev": os.path.join(raiz, ".spec", "interview.json"),
        "docs": os.path.join(raiz, "docs"),
    }


def carregar(raiz):
    c = caminhos(raiz)
    md = S.ler(c["spec"])
    entrev = json.load(open(c["entrev"], encoding="utf-8")) if os.path.isfile(c["entrev"]) else None
    return md, entrev


def salvar_entrev(raiz, e):
    c = caminhos(raiz)
    os.makedirs(os.path.dirname(c["entrev"]), exist_ok=True)
    with open(c["entrev"], "w", encoding="utf-8", newline="\n") as f:
        json.dump(e, f, ensure_ascii=False, indent=1)
        f.write("\n")


def die(msg, code=1):
    print(f"erro: {msg}", file=sys.stderr)
    sys.exit(code)


# ---------- entrevista ----------
def texto_resposta(p):
    r = p.get("resposta")
    if not r:
        return ""
    if r["tipo"] == "opcao":
        base = "; ".join(r.get("rotulos", []))
        return (base + (" — " + r["texto"] if r.get("texto") else "")).strip()
    if r["tipo"] == "livre":
        return r.get("texto", "")
    return ""


def visivel(p, e):
    se = p.get("se")
    if not se:
        return True
    ref = next((x for x in e["perguntas"] if x["id"] == se[0]), None)
    if not ref or not ref.get("resposta") or ref["resposta"]["tipo"] == "bypass":
        return False
    return se[1].lower() in texto_resposta(ref).lower()


def visiveis(e):
    return [p for p in e["perguntas"] if visivel(p, e) and not p.get("descartada")]


def cliente_efetivo(p):
    """UMA regra para 'esta pergunta vai ao cliente?': devolve o que vai, ou None.
    - decisão explícita (p['cliente']) manda: ligada = vai; desligada = não vai;
    - sem decisão explícita, a SUGESTÃO do Claude (selecao 'sugerida', com texto de negócio) já vale: vem marcada, o usuário desmarca quando quiser."""
    c = p.get("cliente")
    if c is not None:
        return c if c.get("ativa") else None
    neg = p.get("neg") or {}
    if p.get("selecao_cliente") == "sugerida" and neg.get("q"):
        return {"ativa": True, "texto": neg["q"], "opcoes": list(neg.get("o", [])), "arquivo": False, "arquivo_desc": "",
                "visuais": [], "refs": [], "origem": "sugerida"}
    return None


def vai_ao_cliente(p):
    return cliente_efetivo(p) is not None


def estado_p(p):
    """Responder e direcionar ao cliente são INDEPENDENTES: uma pergunta direcionada continua aguardando o cliente
    mesmo que o usuário já tenha dado a sua resposta (provisória) ou pulado."""
    r = p.get("resposta")
    if r and (p.get("revisao") or {}).get("aberta"):
        return "revisar"
    if vai_ao_cliente(p) and (not r or not p.get("respostas_cliente")):
        return "aguardando"
    if not r:
        return "pendente"
    return "bypass" if r["tipo"] == "bypass" else "respondida"


def nome_bloco(e, bid):
    for b in e.get("blocos", []):
        if b["id"] == bid:
            return b["nome"]
    return bid.capitalize()


def contagem(e):
    vs = visiveis(e)
    c = {"total": len(vs), "respondidas": 0, "bypass": 0, "pendentes": 0, "aguardando": 0, "revisar": 0,
         "base": sum(1 for p in vs if p.get("origem", "base") == "base"),
         "escopo": sum(1 for p in vs if p.get("origem") == "escopo")}
    for p in vs:
        k = estado_p(p)
        c[{"respondida": "respondidas", "bypass": "bypass", "aguardando": "aguardando", "revisar": "revisar"}.get(k, "pendentes")] += 1
    return c


def _uma_linha(t):
    return re.sub(r"\s+", " ", str(t)).strip()


def sync_decisoes(raiz):
    md, e = carregar(raiz)
    if not e:
        return
    vs = visiveis(e)
    c = contagem(e)
    linhas = [f"Respondidas: {c['respondidas']} de {c['total']} · puladas (bypass): {c['bypass']} · pendentes: {c['pendentes']}", ""]
    blocos = []
    for p in vs:
        if p["bloco"] not in blocos:
            blocos.append(p["bloco"])
    for b in blocos:
        linhas += [f"### {nome_bloco(e, b)}", "", "| ID | Pergunta | Decisão | Origem |", "|---|---|---|---|"]
        for p in vs:
            if p["bloco"] != b:
                continue
            k = estado_p(p)
            r = p.get("resposta") or {}
            if k == "respondida":
                dec = texto_resposta(p)
                origem = {"recomendada": "recomendada", "alternativa": "alternativa", "livre": "resposta livre"}.get(
                    r.get("origem", ""), r.get("origem", ""))
            elif k == "bypass":
                dec = "PENDENTE (bypass)" + (f": {r['texto']}" if r.get("texto") else "")
                origem = "bypass"
            elif k == "revisar":
                rv = p["revisao"]
                dec = f"{texto_resposta(p)} — REVISAR: {rv.get('motivo', '')} (origem {rv.get('origem', '?')})"
                origem = "revisar"
            elif k == "aguardando":
                rc = p.get("resposta_cliente")
                if rc:
                    dec = "RESPOSTA DO CLIENTE (a traduzir): " + " · ".join(CH.resumo(rc))
                else:
                    dec = "AGUARDANDO CLIENTE: " + (cliente_efetivo(p).get("texto") or p["q"])
                if p.get("resposta") and p["resposta"]["tipo"] != "bypass":
                    dec = f"Sua resposta provisória: {texto_resposta(p)} — " + dec
                origem = "cliente" + (" · 📌 sugerida por mim" if p.get("cliente") is None else "")
            else:
                dec = "—"
                origem = "pendente"
            cel = lambda t: re.sub(r"\s+", " ", str(t)).replace("|", "/")  # noqa: E731
            linhas.append(f"| {p['id']} | {cel(p['q'])} | {cel(dec)} | {origem} |")
        linhas.append("")
    desc = [p for p in e["perguntas"] if p.get("descartada")]
    if desc:
        linhas += ["### Perguntas da base que não se aplicam", "", "| ID | Pergunta | Motivo |", "|---|---|---|"]
        for p in desc:
            linhas.append(f"| {p['id']} | {_uma_linha(p['q']).replace('|', '/')} | {_uma_linha(p['descartada']['motivo']).replace('|', '/')} |")
        linhas.append("")
    reg = _registro(e)
    if reg:
        linhas += ["### Registro das respostas do cliente", "",
                   "Respostas do dono do negócio, nas palavras dele. Somente acréscimo: nada aqui é alterado depois de registrado. "
                   f"Código do registro: `{_codigo_registro(reg)}`.", ""]
        rod = None
        for it in reg:
            if it["rodada"] != rod:
                rod = it["rodada"]
                linhas += [f"**Rodada {rod}**", ""]
            linhas.append("- " + it["id"] + " · " + _uma_linha(it["pergunta"]))
            for k, r in enumerate(it["respostas"]):
                quem = f" · {r['respondente']}" if r.get("respondente") else ""
                txt = _uma_linha(" · ".join(CH.resumo(r)))
                linhas.append(f"  - {'resposta' if k == 0 else 'complemento'} ({_fmt(r['em'])}{quem}): {txt}")
        linhas.append("")
    novo = "\n".join(linhas).rstrip() + "\n"
    i, f = md.find(S.DEC_INI), md.find(S.DEC_FIM)
    if i < 0 or f < 0:
        die("marcadores de decisões não encontrados no SPEC.md")
    md = md[:i + len(S.DEC_INI)] + "\n" + novo + md[f:]
    S.gravar(caminhos(raiz)["spec"], md)


def montar_pergunta_json(e, p, pos, total):
    return {"id": p["id"], "bloco": nome_bloco(e, p["bloco"]), "pos": pos, "total": total, "q": p["q"],
            "why": p.get("why", ""), "multi": bool(p.get("multi")), "origem": p.get("origem", "base"),
            "motivo": p.get("motivo", ""), "dica": p.get("dica", ""), "revisao": p.get("revisao"), "neg": p.get("neg"), "cliente": p.get("cliente"), "selecao_cliente": p.get("selecao_cliente"),
            "opcoes": [{"n": i + 1, "rotulo": o[0], "nota": (o[1] if len(o) > 1 else ""), "recomendada": i == 0}
                       for i, o in enumerate(p["o"])]}


# ---------- comandos ----------
def cmd_init(a):
    raiz = os.path.abspath(a.raiz or os.getcwd())
    if os.path.isfile(os.path.join(raiz, "SPEC.md")) and not a.forcar:
        die("já existe SPEC.md aqui. Use `status` para retomar (ou --forcar para recriar).")
    banco = json.load(open(os.path.join(SKILL, "data", "question-bank.json"), encoding="utf-8"))
    if a.tipo not in banco["tipos"]:
        die(f"tipo inválido: {a.tipo}. Use: {', '.join(banco['tipos'])}")
    r = RANK[a.prof]
    perguntas = []
    for p in banco["perguntas"]:
        if RANK[p["min"]] > r:
            continue
        if p.get("tipos") and a.tipo not in p["tipos"]:
            continue
        q = {k: v for k, v in p.items() if k != "min"}
        q["origem"] = "base"
        perguntas.append(q)
    blocos = [b for b in banco["blocos"] if any(p["bloco"] == b["id"] for p in perguntas)]
    e = {"versao": 1, "projeto": a.nome, "tipo": a.tipo, "profundidade": a.prof, "blocos": blocos,
         "perguntas": perguntas}
    tpl = S.ler(os.path.join(SKILL, "templates", "SPEC.md"))
    md = tpl.replace("{{NOME}}", a.nome).replace("{{TIPO}}", a.tipo).replace("{{PROF}}", S.PROF_NOME[a.prof]).replace(
        "{{DATA}}", S.hoje())
    os.makedirs(os.path.join(raiz, ".spec"), exist_ok=True)
    S.gravar(os.path.join(raiz, "SPEC.md"), md)
    salvar_entrev(raiz, e)
    cl = os.path.join(raiz, "CLAUDE.md")
    atual = S.ler(cl) if os.path.isfile(cl) else ""
    if SNIPPET_MARCA not in atual:
        S.gravar(cl, (atual.rstrip("\n") + "\n\n" if atual else "") + SNIPPET)
    sync_decisoes(raiz)
    import render
    render.render_all(raiz)
    c = contagem(e)
    print(f"Projeto criado em {raiz}")
    print(f"Perguntas: {c['total']} (profundidade {S.PROF_NOME[a.prof]}, tipo {a.tipo})")
    print("Arquivos: SPEC.md, .spec/interview.json, docs/spec.html, docs/painel.html, CLAUDE.md")


def cmd_status(a, raiz):
    md, e = carregar(raiz)
    f = S.ficha(md)
    fase = f.get("fase", "entrada")
    idx = S.FASES.index(fase) + 1 if fase in S.FASES else 0
    feats = S.features(md)
    tasks = S.todas_tasks(md)
    crs = [c for c in S.change_requests(md) if c["estado"] in ("aberta", "aprovada")]
    tst = S.testes(md)
    d = {"testes": {k: sum(1 for t in tst if t["estado"] == k) for k in S.TESTE_ESTADOS if any(t["estado"] == k for t in tst)},
         "projeto": S.titulo_projeto(md), "fase": fase, "fase_num": idx, "fases_total": len(S.FASES),
         "tipo": f.get("tipo"), "profundidade": f.get("profundidade"), "tasks_paralelas": f.get("tasks_paralelas"),
         "entrevista_web": f.get("entrevista_web", "—"),
         "features": {k: sum(1 for x in feats if x["estado"] == k) for k in S.ESTADOS_FEATURE if any(
             x["estado"] == k for x in feats)},
         "tasks": {k: sum(1 for t in tasks if t["estado"] == k) for k in S.MARCA_DE},
         "crs_abertas": [c["id"] for c in crs]}
    if e:
        c = contagem(e)
        d["entrevista"] = c
        vs = visiveis(e)
        d["proximas"] = [p["id"] for p in vs if estado_p(p) == "pendente"][:6]
        d["bypass"] = [p["id"] for p in vs if estado_p(p) == "bypass"]
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return
    print(f"Projeto: {d['projeto']} · fase: {S.FASES_NOME.get(fase, fase)} ({idx} de {len(S.FASES)})")
    if e:
        c = d["entrevista"]
        print(f"Entrevista: {c['respondidas']} de {c['total']} respondidas até agora · {c['bypass']} puladas · {c['pendentes']} pendentes "
              f"({c['base']} da base + {c['escopo']} do escopo)")
        if c["aguardando"]:
            print(f"Aguardando o cliente: {c['aguardando']} perguntas "
                  f"({sum(1 for p in visiveis(e) if p.get('resposta_cliente') and estado_p(p) == 'aguardando')} já com resposta para traduzir)")
        if c["revisar"]:
            print(f"DECISÕES A REVISAR (afetadas por resposta do cliente): {c['revisar']} → "
                  + ", ".join(p["id"] for p in visiveis(e) if estado_p(p) == "revisar"))
        nv = _nao_verificadas(e)
        if nv:
            print(f"Respostas do cliente SEM verificação de impacto: {len(nv)} (rode `impacto`)")
        print(f"Varredura de lacunas: {S.ficha(md).get('varredura_lacunas', 'não')}")
        if d["proximas"]:
            print("Próximas perguntas: " + ", ".join(d["proximas"]))
        if d["bypass"]:
            print("Puladas (bypass): " + ", ".join(d["bypass"]))
    print(f"Features: {d['features'] or 'nenhuma'}")
    print(f"Tasks: {d['tasks']}")
    print(f"Testes: {d['testes'] or 'nenhum no plano'}")
    dp = S.deploy(md)
    if dp["checklist"] or dp["publicacoes"]:
        print(f"Deploy: checklist {sum(1 for i in dp['checklist'] if i['estado'] in ('feito', 'n-a'))}/{len(dp['checklist'])} · publicações: {len(dp['publicacoes'])}"
              f" · URL: {dp['info'].get('url') or '—'}")
    if e:
        pc = estado_pagina_cliente(md, e)
        if pc["gerada_em"] or pc["deve"]:
            if not pc["gerada_em"]:
                estado = "ainda NÃO criada (export-cliente)"
            else:
                estado = "publicada" if pc["publicada"] else "gerada, NÃO publicada (netlify.py deploy ... --ficha .)"
                if pc["desatualizada"]:
                    estado += f" · DESATUALIZADA (faltam {', '.join(pc['faltam']) or '—'}; sobram {', '.join(pc['sobram']) or '—'})"
            print(f"Página do cliente: {estado}")
    if crs:
        print("Change requests em aberto: " + ", ".join(d["crs_abertas"]))
    print(f"Entrevista pelo celular: {d['entrevista_web']}")
    print(f"Tasks em paralelo: {d['tasks_paralelas']}")


def cmd_next(a, raiz):
    _, e = carregar(raiz)
    vs = visiveis(e)
    pend = [(i + 1, p) for i, p in enumerate(vs) if estado_p(p) in ("pendente", "revisar")]
    if a.bloco:
        pend = [(i, p) for i, p in pend if p["bloco"] == a.bloco]
    pend = pend[:a.n]
    saida = [montar_pergunta_json(e, p, i, len(vs)) for i, p in pend]
    if a.json:
        print(json.dumps(saida, ensure_ascii=False, indent=1))
        return
    if not saida:
        print("Nenhuma pergunta pendente.")
    for q in saida:
        print(f"[{q['id']}] Pergunta {q['pos']} de {q['total']} · {q['bloco']}")
        print(f"  {q['q']}")
        if q.get("why"):
            print(f"  (por quê: {q['why']})")
        if q.get("dica"):
            print(f"  (no briefing: {q['dica']})")
        if (q.get("revisao") or {}).get("aberta"):
            print(f"  (REVISAR: {q['revisao']['motivo']} · origem {q['revisao'].get('origem', '?')} · decisão anterior: {q['revisao'].get('decisao_anterior', '')})")
        for o in q["opcoes"]:
            print(f"   {o['n']}. {o['rotulo']}{' (recomendada)' if o['recomendada'] else ''}")
        print("   L. Resposta livre   P. Pular (bypass)")


def _arquivar(p, motivo=""):
    """Guarda a decisão anterior no histórico da pergunta e encerra a revisão aberta (a decisão foi refeita)."""
    antiga = p.get("resposta")
    if antiga:
        p.setdefault("historico", []).append({"resposta": antiga, "texto": texto_resposta(p), "substituida_em": S.agora(), "motivo": motivo})
    rv = p.get("revisao")
    if rv and rv.get("aberta"):
        rv["aberta"] = False
        rv["resolvida_em"] = S.agora()
        rv["resultado"] = "decisão refeita"


def _nao_verificadas(e):
    return [(p["id"], r) for p in e["perguntas"] for r in (p.get("respostas_cliente") or []) if not r.get("verificada")]


def cmd_answer(a, raiz):
    md, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    if not p:
        die(f"pergunta {a.id} não existe")
    if a.bypass:
        r = {"tipo": "bypass", "texto": a.text or "", "em": S.agora()}
    elif a.opt:
        idx = [int(x) for x in a.opt.split(",")]
        if any(i < 1 or i > len(p["o"]) for i in idx):
            die(f"opção fora do intervalo 1..{len(p['o'])}")
        if len(idx) > 1 and not p.get("multi"):
            die("esta pergunta aceita uma opção só")
        origem = "recomendada" if idx == [1] else "alternativa"
        r = {"tipo": "opcao", "indices": idx, "rotulos": [p["o"][i - 1][0] for i in idx], "texto": a.text or "",
             "origem": origem, "em": S.agora()}
    elif a.text:
        r = {"tipo": "livre", "texto": a.text, "origem": "livre", "em": S.agora()}
    else:
        die("informe --opt N, --text \"...\" ou --bypass")
    _arquivar(p, (p.get("revisao") or {}).get("motivo", "") if (p.get("revisao") or {}).get("aberta") else "nova resposta")
    p["resposta"] = r
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    c = contagem(carregar(raiz)[1])
    print(f"{a.id} registrada ({r['tipo']}). Restam {c['pendentes']} pendentes.")


def cmd_dica(a, raiz):
    _, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    if not p:
        die(f"pergunta {a.id} não existe")
    p["dica"] = a.texto
    salvar_entrev(raiz, e)
    print(f"{a.id}: dica registrada (aparece para você confirmar, a pergunta continua pendente).")


def cmd_rec(a, raiz):
    _, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    if not p:
        die(f"pergunta {a.id} não existe")
    if p.get("resposta"):
        die("pergunta já respondida: não reordene as opções")
    if a.n < 1 or a.n > len(p["o"]):
        die(f"opção fora do intervalo 1..{len(p['o'])}")
    p["o"].insert(0, p["o"].pop(a.n - 1))
    if a.nota:
        p["o"][0] = [p["o"][0][0], a.nota]
    salvar_entrev(raiz, e)
    print(f"{a.id}: recomendada agora é '{p['o'][0][0]}'.")


def _visuais_de_args(a):
    """Monta os grupos visuais a partir de --visual TIPO e --visual-opt TIPO|Rótulo|dado."""
    grupos = {}
    for t in a.visual or []:
        if t not in CH.TITULOS:
            die(f"tipo visual inválido: {t} (use paleta, layout ou tipografia)")
        grupos.setdefault(t, [])
    for vo in a.visual_opt or []:
        partes = vo.split("|", 2)
        if len(partes) != 3 or partes[0] not in CH.TITULOS:
            die("--visual-opt deve ser 'tipo|Rótulo|dado' (paleta: cores #hex separadas por vírgula; layout: hero, painel, grade ou lista; tipografia: família de fonte)")
        grupos.setdefault(partes[0], []).append({"rotulo": partes[1], "dado": partes[2]})
    return [{"tipo": t, "titulo": CH.TITULOS[t], "opcoes": ops or CH.opcoes_padrao(t)} for t, ops in grupos.items()]


def _refs_de_args(a):
    refs = []
    for r in a.ref or []:
        rot, _, url = r.rpartition("|") if "|" in r else ("", "", r)
        if not CH._url_ok(url):
            die(f"link de referência inválido (use http:// ou https://): {url}")
        refs.append({"rotulo": rot.strip(), "url": url.strip()})
    return refs


def cmd_cliente(a, raiz):
    _, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    if not p:
        die(f"pergunta {a.id} não existe")
    if a.remover:
        p.pop("cliente", None)
        if p.get("selecao_cliente") == "sugerida":
            p["selecao_cliente"] = "dispensada"
        salvar_entrev(raiz, e)
        print(f"{a.id}: não está mais direcionada ao cliente.")
        return
    neg = p.get("neg") or {}
    texto = a.texto or neg.get("q")
    if not texto:
        die("informe --texto com a pergunta em linguagem de negócio (esta pergunta não tem sugestão pronta)")
    opcoes = a.opt if a.opt else neg.get("o", [])
    if a.sugerir:
        p["neg"] = {"q": texto, "o": opcoes, "sugerida": True}
        if p.get("selecao_cliente") == "dispensada":
            salvar_entrev(raiz, e)
            print(f"{a.id}: o usuário DISPENSOU a sugestão de enviar esta pergunta ao cliente; mantive o texto, sem marcar de novo.")
            return
        p["selecao_cliente"] = "sugerida"
        salvar_entrev(raiz, e)
        print(f"{a.id}: marcada como SUGERIDA para o cliente (você decide se direciona).")
        return
    if a.design:
        p["design"] = True
    visuais, refs = _visuais_de_args(a), _refs_de_args(a)
    if p.get("design") and not visuais and not refs and not (p.get("cliente") or {}).get("visuais") and not (p.get("cliente") or {}).get("refs"):
        die("pergunta de DESIGN: sempre ofereça opções visuais (--visual paleta|layout|tipografia) e/ou links de referência (--ref URL). "
            "Dica: --visual paleta --visual layout --ref \"Exemplo|https://...\"")
    ant = p.get("cliente") or {}
    p["cliente"] = {"ativa": True, "texto": texto, "opcoes": opcoes, "em": S.agora(),
                    "arquivo": bool(a.arquivo or ant.get("arquivo")), "arquivo_desc": a.arquivo_desc or ant.get("arquivo_desc", ""),
                    "visuais": visuais or ant.get("visuais", []), "refs": refs or ant.get("refs", [])}
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    extras = [x for x, ok in (("upload de arquivo", p["cliente"]["arquivo"]), ("opções visuais", bool(p["cliente"]["visuais"])),
                              ("links de referência", bool(p["cliente"]["refs"]))) if ok]
    print(f"{a.id}: direcionada ao dono do negócio → \"{texto}\"" + (f" (+ {', '.join(extras)})" if extras else ""))


def _cliente_ativas(e):
    """Perguntas direcionadas ao cliente que ainda não receberam resposta dele (vão para o formulário)."""
    return [p for p in visiveis(e) if vai_ao_cliente(p) and not p.get("respostas_cliente")]


def _fmt(iso):
    d = datetime.datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    return d.astimezone(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")


def _rodada_de(e, pid):
    for r in e.get("rodadas", []):
        if pid in r["perguntas"]:
            return r["n"]
    return None


def _registro(e):
    """Registro histórico das respostas do cliente (somente acréscimo), agrupável por rodada."""
    itens = []
    for p in e["perguntas"]:
        rs = p.get("respostas_cliente") or []
        if rs:
            itens.append({"id": p["id"], "rodada": p.get("rodada_cliente") or 1, "pergunta": rs[0].get("pergunta") or p["q"],
                          "respostas": sorted(rs, key=lambda x: x["em"])})
    itens.sort(key=lambda x: (x["rodada"], x["respostas"][0]["em"], x["id"]))
    return itens


def _codigo_registro(itens):
    canon = json.dumps([[i["id"], i["pergunta"], [[r["em"], CH.resumo(r)] for r in i["respostas"]]]
                        for i in itens], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]


def cmd_export_cliente(a, raiz):
    """Gera .spec/cliente/: página do dono do negócio = registro das respostas anteriores (travado) + novas perguntas."""
    md, e = carregar(raiz)
    novas = _cliente_ativas(e)
    reg = _registro(e)
    if not novas and not reg:
        die("nenhuma pergunta direcionada ao cliente (use `cliente ID --texto ...`).")
    rodadas = e.setdefault("rodadas", [])
    if novas:
        atual = rodadas[-1] if rodadas else None
        if not atual or any(next((x for x in e["perguntas"] if x["id"] == pid), {}).get("respostas_cliente") for pid in atual["perguntas"]):
            atual = {"n": len(rodadas) + 1, "publicada_em": S.agora(), "perguntas": []}
            rodadas.append(atual)
        for p in novas:
            if not any(p["id"] in r["perguntas"] for r in rodadas):
                atual["perguntas"].append(p["id"])
        atual["publicada_em"] = S.agora()
        salvar_entrev(raiz, e)
    esc = html_mod.escape
    cards = []
    avisos = []
    for i, p in enumerate(novas, 1):
        c = cliente_efetivo(p)
        if p.get("design") and not c.get("visuais") and not c.get("refs"):
            c["visuais"] = [{"tipo": t, "titulo": CH.TITULOS[t], "opcoes": CH.opcoes_padrao(t)} for t in ("paleta", "layout")]
            avisos.append(p["id"])
        ops = "".join(f'<label class="opt"><input type="radio" name="q_{esc(p["id"])}" value="{esc(o)}"><span>{esc(o)}</span></label>'
                      for o in c.get("opcoes", []))
        extra = CH.render_refs(c.get("refs", [])) + CH.render_visuais(p["id"], c.get("visuais", []))
        if p.get("design"):
            extra += CH.render_links_campo(p["id"])
        arq = CH.render_arquivo(p["id"], c.get("arquivo_desc", "")) if c.get("arquivo") else ""
        rotulo = "Se preferir, explique com suas palavras" if (ops or c.get("visuais")) else "Sua resposta"
        cards.append(f'<section class="card"><div class="n">Pergunta {i} de {len(novas)}</div><p class="q">{esc(c["texto"])}</p>{ops}{extra}'
                     f'<label class="t" for="t_{esc(p["id"])}">{rotulo}</label>'
                     f'<textarea id="t_{esc(p["id"])}" name="t_{esc(p["id"])}"></textarea>{arq}</section>')
    if avisos:
        salvar_entrev(raiz, e)
        print(f"aviso: pergunta(s) de design sem opções visuais ({', '.join(avisos)}): usei paleta e layout padrão. Ajuste com `cliente ID --visual ...`.")
    perguntas_html = ('<h2 class="sec">Novas perguntas</h2>' + "\n".join(cards)) if cards else ""
    registro_html = ""
    if reg:
        registro_html = ('<section class="reg"><h2 class="sec">Respostas já registradas</h2>'
                         '<p class="nota2">🔒 Estas respostas já foram enviadas e não podem ser alteradas. Ficam aqui como registro das definições.</p>')
        rod_atual = None
        for it in reg:
            if it["rodada"] != rod_atual:
                rod_atual = it["rodada"]
                registro_html += f'<h3 class="rod">Rodada {rod_atual} · {esc(_fmt(it["respostas"][0]["em"])[:10])}</h3>'
            registro_html += f'<div class="rc"><p class="q">{esc(it["pergunta"])}</p>'
            for k, r in enumerate(it["respostas"]):
                quem = f' · {esc(r["respondente"])}' if r.get("respondente") else ""
                rot = "Resposta" if k == 0 else "Complemento"
                texto = "<br>".join(esc(x) for x in CH.resumo(r))
                registro_html += (f'<p class="a"><span class="meta">🔒 {rot} · {esc(_fmt(r["em"]))}{quem}</span><br>{texto}</p>')
            registro_html += "</div>"
        registro_html += f'<p class="cod">Código do registro: <code>{_codigo_registro(reg)}</code></p></section>'
    nome = S.titulo_projeto(md)
    if a.intro:
        intro = a.intro
    elif reg and novas:
        intro = "Obrigado pelas respostas anteriores, que ficam registradas abaixo. Preciso de mais algumas informações para continuar."
    elif reg:
        intro = "Estas são as definições registradas até agora, com as suas respostas. Não há perguntas novas no momento."
    else:
        intro = "Preciso de algumas informações sobre o seu negócio para montar o projeto do jeito certo. Responda o que souber agora."
    tpl = S.ler(os.path.join(SKILL, "templates", "cliente.html"))
    pagina = (tpl.replace("__TITULO__", esc(nome)).replace("__INTRO__", esc(intro)).replace("__PROJETO__", esc(nome))
              .replace("__REGISTRO__", registro_html).replace("__PERGUNTAS__", perguntas_html)
              .replace("__FORM_HIDDEN__", "" if novas else " hidden")
              .replace("__MAXBYTES__", str(int(CH.MARGEM_MB * 1024 * 1024))).replace("__LIMITE__", str(CH.LIMITE_MB)))
    pasta = os.path.join(raiz, ".spec", "cliente")
    os.makedirs(pasta, exist_ok=True)
    S.gravar(os.path.join(pasta, "index.html"), pagina)
    S.gravar(os.path.join(pasta, "obrigado.html"), S.ler(os.path.join(SKILL, "templates", "obrigado.html")))
    S.gravar(os.path.join(pasta, "robots.txt"), "User-agent: *\nDisallow: /\n")
    S.gravar(os.path.join(pasta, "_headers"), "/*\n  X-Robots-Tag: noindex, nofollow\n  Referrer-Policy: no-referrer\n")
    e["pagina_cliente"] = {"gerada_em": S.agora(), "ids": sorted(p["id"] for p in novas), "rodada": (e.get("rodadas") or [{}])[-1].get("n")}
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(pasta)
    print(f"{len(novas)} perguntas novas · {len(reg)} respostas registradas (travadas) na página do cliente.")
    print("Lembrete: publique no mesmo site (`netlify.py deploy <id> .spec/cliente --ficha .`) para o painel marcar como publicada.")


def _arquivo_de(v):
    """Normaliza o valor de um campo de arquivo do Netlify (objeto com url/nome/tamanho, ou só texto)."""
    if isinstance(v, list):
        v = v[0] if v else None
    if isinstance(v, dict):
        url = v.get("url") or ""
        nome = v.get("filename") or v.get("name") or v.get("nome") or (url.rsplit("/", 1)[-1] if url else "")
        if not (url or nome):
            return None
        return {"nome": nome, "url": url, "tamanho": v.get("size") or v.get("tamanho") or 0, "tipo": v.get("type") or v.get("tipo") or ""}
    if isinstance(v, str) and v.strip():
        return {"nome": v.strip().rsplit("/", 1)[-1], "url": v.strip() if v.startswith("http") else "", "tamanho": 0, "tipo": ""}
    return None


def cmd_import_cliente(a, raiz):
    """Importa envios do formulário (JSON de `netlify.py submissions`). Só acrescenta: nunca altera o que já foi registrado."""
    md, e = carregar(raiz)
    envios = json.load(open(a.arquivo, encoding="utf-8"))
    n = 0
    for env in sorted(envios, key=lambda x: x["em"]):
        dados = env.get("data", {})
        for p in e["perguntas"]:
            pid = p["id"]
            opcao = (dados.get("q_" + pid) or "").strip() if isinstance(dados.get("q_" + pid), str) else ""
            texto = (dados.get("t_" + pid) or "").strip() if isinstance(dados.get("t_" + pid), str) else ""
            links = (dados.get("l_" + pid) or "").strip() if isinstance(dados.get("l_" + pid), str) else ""
            arquivo = _arquivo_de(dados.get("f_" + pid))
            grande = str(dados.get("g_" + pid) or "").strip().lower() in ("sim", "on", "true", "1")
            visuais = []
            for g in (p.get("cliente") or {}).get("visuais", []):
                v = dados.get(f"v_{pid}_{g['tipo']}")
                if isinstance(v, str) and v.strip():
                    visuais.append(f"{CH.NOMES.get(g['tipo'], g['tipo'])}: {v.strip()}")
            if not (opcao or texto or links or arquivo or grande or visuais):
                continue
            lista = p.setdefault("respostas_cliente", [])
            if any(x.get("submissao") == env.get("id") for x in lista):
                continue
            c = p.get("cliente") or {}
            item = {"pergunta": c.get("texto") or p["q"], "opcoes": c.get("opcoes", []), "opcao": opcao, "texto": texto,
                    "visuais": visuais, "links": links, "arquivo": arquivo, "grande": grande,
                    "em": env["em"], "submissao": env.get("id", ""), "respondente": (dados.get("respondente") or "").strip()}
            lista.append(item)
            lista.sort(key=lambda x: x["em"])
            p["resposta_cliente"] = lista[-1]
            p.setdefault("rodada_cliente", _rodada_de(e, pid) or 1)
            n += 1
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    pend = [p["id"] for p in e["perguntas"] if p.get("respostas_cliente") and not p.get("resposta")]
    print(f"{n} respostas do cliente registradas. A traduzir para decisão técnica: {', '.join(pend) or 'nenhuma'}")
    if _nao_verificadas(e):
        print("⚠ OBRIGATÓRIO: verifique o impacto dessas respostas nas decisões já tomadas na lista completa (`impacto`).")


def cmd_revisar(a, raiz):
    _, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    if not p:
        die(f"pergunta {a.id} não existe")
    if not p.get("resposta"):
        die("só se revisa uma decisão já tomada (esta pergunta ainda não foi respondida)")
    p["revisao"] = {"aberta": True, "motivo": a.motivo, "origem": a.origem or "", "em": S.agora(), "decisao_anterior": texto_resposta(p)}
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{a.id}: marcada para REVISAR. Motivo: {a.motivo}. Refaça com `answer {a.id} ...` ou confirme com `revisao-ok {a.id}`.")


def cmd_revisao_ok(a, raiz):
    _, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    rv = (p or {}).get("revisao")
    if not rv or not rv.get("aberta"):
        die(f"{a.id} não tem revisão aberta")
    rv.update({"aberta": False, "resolvida_em": S.agora(), "resultado": "decisão mantida", "nota": a.nota or ""})
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{a.id}: decisão mantida após revisão.")


def cmd_impacto(a, raiz):
    """Lista o que revisar: respostas do cliente ainda não verificadas × decisões já tomadas na lista completa."""
    md, e = carregar(raiz)
    nv = _nao_verificadas(e)
    resolvidas = [p for p in visiveis(e) if estado_p(p) in ("respondida", "revisar")]
    if a.json:
        print(json.dumps({"respostas_do_cliente": [{"id": i, "pergunta": r["pergunta"], "resumo": CH.resumo(r), "em": r["em"]} for i, r in nv],
                          "decisoes_tomadas": [{"id": p["id"], "bloco": nome_bloco(e, p["bloco"]), "pergunta": p["q"], "decisao": texto_resposta(p),
                                                "em_revisao": estado_p(p) == "revisar"} for p in resolvidas]}, ensure_ascii=False, indent=1))
        return
    if not nv:
        print("Nenhuma resposta do cliente pendente de verificação de impacto.")
        return
    print("VERIFICAÇÃO DE IMPACTO. Respostas novas do cliente:")
    for i, r in nv:
        print(f"  [{i}] {r['pergunta']}\n       → {' · '.join(CH.resumo(r))}")
    print(f"\nDecisões já tomadas na lista completa ({len(resolvidas)}). Para CADA resposta acima, pergunte: ela contradiz, restringe ou muda alguma destas?")
    bl = None
    for p in resolvidas:
        if p["bloco"] != bl:
            bl = p["bloco"]
            print(f"  == {nome_bloco(e, bl)}")
        print(f"   {p['id']} · {p['q']} → {texto_resposta(p)}{'  [EM REVISÃO]' if estado_p(p) == 'revisar' else ''}")
    print("\nSe afeta: `revisar ID --motivo \"...\" --origem <ID da pergunta do cliente>`. Ao terminar: `impacto-ok`.")


def cmd_impacto_ok(a, raiz):
    md, e = carregar(raiz)
    nv = _nao_verificadas(e)
    for _, r in nv:
        r["verificada"] = True
        r["verificada_em"] = S.agora()
    salvar_entrev(raiz, e)
    abertas = [p["id"] for p in e["perguntas"] if (p.get("revisao") or {}).get("aberta")]
    S.gravar(caminhos(raiz)["spec"], S.add_historico(md, f"impacto verificado: {len(nv)} resposta(s) do cliente; revisões abertas: {', '.join(abertas) or 'nenhuma'}"))
    print(f"{len(nv)} resposta(s) do cliente marcadas como verificadas. Revisões abertas: {', '.join(abertas) or 'nenhuma'}.")


def cmd_bypass_all(a, raiz):
    _, e = carregar(raiz)
    n = 0
    for p in visiveis(e):
        if estado_p(p) in ("pendente", "aguardando") and (not a.bloco or p["bloco"] == a.bloco):
            p["resposta"] = {"tipo": "bypass", "texto": a.motivo or "bypass em lote", "em": S.agora()}
            n += 1
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{n} perguntas marcadas como bypass.")


def cmd_add(a, raiz):
    _, e = carregar(raiz)
    qid = a.id or S.proximo_id(json.dumps(e, ensure_ascii=False), "X", 2)
    if any(p["id"] == qid for p in e["perguntas"]):
        die(f"{qid} já existe")
    if not a.bloco_nome and not any(b["id"] == a.bloco for b in e["blocos"]):
        a.bloco_nome = a.bloco.capitalize()
    if a.bloco_nome and not any(b["id"] == a.bloco for b in e["blocos"]):
        e["blocos"].append({"id": a.bloco, "nome": a.bloco_nome})
    if not (a.neg or "").strip():
        die("informe --neg com a pergunta em linguagem de NEGÓCIO (obrigatório): é o texto que o botão 'Direcionar ao dono do negócio' "
            "já abre pronto para enviar ao cliente. Ex.: --neg \"Hoje, como você controla os pedidos?\" [--neg-opt \"Caderno\" --neg-opt \"Planilha\"]")
    p = {"id": qid, "bloco": a.bloco, "q": a.q, "why": a.why or "", "o": [[x] for x in a.opt or []],
         "origem": "escopo", "neg": {"q": a.neg.strip(), "o": a.neg_opt or [], "sugerida": True}}
    if a.motivo:
        p["motivo"] = a.motivo
    if getattr(a, "design", False):
        p["design"] = True
    if a.multi:
        p["multi"] = True
    if not p["o"]:
        die("informe ao menos uma --opt (a primeira é a recomendada)")
    # perguntas do escopo vêm antes das da base no mesmo bloco (a entrevista é guiada pelo escopo)
    pos = next((i for i, x in enumerate(e["perguntas"]) if x["bloco"] == a.bloco and x.get("origem", "base") == "base"), None)
    if pos is None:
        e["perguntas"].append(p)
    else:
        e["perguntas"].insert(pos, p)
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{qid} adicionada ao bloco {a.bloco}.")


def _completar_textos(e):
    """Projetos criados antes do banco ter o texto de negócio de todas as perguntas recebem os textos novos."""
    banco = json.load(open(os.path.join(SKILL, "data", "question-bank.json"), encoding="utf-8"))
    por_id = {q["id"]: q for q in banco["perguntas"]}
    n = 0
    for p in e["perguntas"]:
        b = por_id.get(p["id"])
        if b and p.get("origem", "base") == "base":
            if not (p.get("neg") or {}).get("q") and b.get("neg"):
                p["neg"] = dict(b["neg"])
                n += 1
            if b.get("design") and not p.get("design"):
                p["design"] = True
    return n


def cmd_atualizar_textos(a, raiz):
    _, e = carregar(raiz)
    n = _completar_textos(e)
    salvar_entrev(raiz, e)
    print(f"{n} pergunta(s) da base receberam o texto em linguagem de negócio.")


def cmd_export_web(a, raiz):
    """Gera .spec/entrevista.html: a página da entrevista (para publicar como artifact e responder no celular)."""
    md, e = carregar(raiz)
    if _completar_textos(e):
        salvar_entrev(raiz, e)
    blocos = [b for b in e["blocos"] if any(p["bloco"] == b["id"] for p in e["perguntas"])]
    dados = {"projeto": S.titulo_projeto(md), "blocos": blocos, "perguntas": e["perguntas"],
             "respostas": {p["id"]: p["resposta"] for p in e["perguntas"] if p.get("resposta")}}
    js = json.dumps(dados, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    tpl = S.ler(os.path.join(SKILL, "templates", "entrevista.html"))
    if "/*__DADOS__*/null" not in tpl:
        die("template entrevista.html sem o marcador de dados")
    html = tpl.replace("/*__DADOS__*/null", js).replace(
        "<title>Entrevista de requisitos</title>", "<title>Entrevista · " + html_mod.escape(S.titulo_projeto(md)) + "</title>")
    saida = os.path.join(raiz, ".spec", "entrevista.html")
    S.gravar(saida, html)
    print(saida)


def _itens_import(bruto):
    """Normaliza o que veio do celular: (id, doc, coleção). Coleções: answers (respostas) e clientes (direcionamentos)."""
    itens = []

    def add(conteudo, colecao):
        pares = conteudo.items() if isinstance(conteudo, dict) else [(x.get("id"), x.get("data", x)) for x in conteudo]
        for k, d in pares:
            itens.append((k, d, colecao))
    if isinstance(bruto, dict):
        if "answers" in bruto or "clientes" in bruto:
            add(bruto.get("answers", {}), "answers")
            add(bruto.get("clientes", {}), "clientes")
        else:
            add(bruto, "answers")
    else:
        for x in bruto:
            itens.append((x.get("id"), x.get("data", x), x.get("colecao", "answers")))
    return itens


def _aplicar_cliente(p, d):
    """Direcionamento ao cliente, independente da resposta do usuário. Devolve True se mudou algo."""
    antigo = p.get("cliente") or {}
    if antigo.get("em", "") >= d.get("em", ""):
        return False
    if d.get("ativa") is False:
        p.pop("cliente", None)
        # desligar uma pergunta que eu tinha sugerido é uma DISPENSA (simétrica a ligar de novo); o Claude não remarca
        if d.get("dispensada") or p.get("selecao_cliente") in ("sugerida", "dispensada"):
            p["selecao_cliente"] = "dispensada"
        return True
    p["cliente"] = {"ativa": True, "texto": d.get("texto", ""), "opcoes": [x for x in d.get("opcoes", []) if x],
                    "em": d.get("em", S.agora()), "arquivo": bool(d.get("arquivo")),
                    "arquivo_desc": antigo.get("arquivo_desc") or "", "visuais": antigo.get("visuais", []), "refs": antigo.get("refs", [])}
    return True


def cmd_import(a, raiz):
    md, e = carregar(raiz)
    bruto = json.load(open(a.arquivo, encoding="utf-8"))
    novas = antigas = 0
    lista_antes = sorted(x["id"] for x in _cliente_ativas(e))
    for qid, d, colecao in _itens_import(bruto):
        p = next((x for x in e["perguntas"] if x["id"] == qid), None)
        if not p or not isinstance(d, dict):
            continue
        atual = p.get("resposta")
        tipo = "cliente" if colecao == "clientes" else d.get("tipo")
        if tipo == "cliente":  # direcionamento ao cliente (também aceita o formato antigo, dentro de answers)
            if _aplicar_cliente(p, d):
                novas += 1
            else:
                antigas += 1
            continue
        if tipo == "reaberta":  # o usuário reabriu a pergunta: a resposta dele sai, a anterior vai para o histórico
            if atual and atual.get("em", "") < d.get("em", ""):
                _arquivar(p, "reaberta pelo usuário")
                p.pop("resposta", None)
                novas += 1
            else:
                antigas += 1
            continue
        if atual and atual.get("em", "") >= d.get("em", ""):
            antigas += 1
            continue
        if tipo == "opcao":
            idx = [int(i) for i in d.get("indices", [])]
            idx = [i for i in idx if 1 <= i <= len(p["o"])]
            if not idx:
                continue
            r = {"tipo": "opcao", "indices": idx, "rotulos": [p["o"][i - 1][0] for i in idx], "texto": d.get("texto", ""),
                 "origem": "recomendada" if idx == [1] else "alternativa", "em": d.get("em", S.agora())}
        elif tipo == "livre" and d.get("texto"):
            r = {"tipo": "livre", "texto": d["texto"], "origem": "livre", "em": d.get("em", S.agora())}
        elif tipo == "bypass":
            r = {"tipo": "bypass", "texto": d.get("texto", ""), "em": d.get("em", S.agora())}
        else:
            continue
        _arquivar(p, "nova resposta (importada)")
        p["resposta"] = r
        novas += 1
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    c = contagem(carregar(raiz)[1])
    print(f"{novas} respostas importadas ({antigas} já estavam atualizadas). Restam {c['pendentes']} pendentes.")
    e2 = carregar(raiz)[1]
    if sorted(x["id"] for x in _cliente_ativas(e2)) != lista_antes:
        print("⚠ A LISTA DO CLIENTE MUDOU (o usuário direcionou ou revogou perguntas). Rode `export-cliente` e republique a página "
              "do cliente (mesmo site) para ela refletir as escolhas dele.")


def cmd_reabrir(a, raiz):
    """Reabre uma pergunta já respondida: a resposta sai (a anterior vai para o histórico) e ela volta a pendente."""
    _, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    if not p:
        die(f"pergunta {a.id} não existe")
    if not p.get("resposta"):
        die(f"{a.id} não tem resposta para reabrir")
    _arquivar(p, a.motivo or "reaberta pelo usuário")
    p.pop("resposta", None)
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{a.id}: reaberta. A resposta anterior ficou no histórico da pergunta"
          + (" e ela continua direcionada ao cliente." if vai_ao_cliente(p) else "."))


def cmd_varredura(a, raiz):
    md, e = carregar(raiz)
    md = S.set_ficha(md, "varredura_lacunas", "feita")
    md = S.add_historico(md, "varredura de lacunas da entrevista concluída")
    S.gravar(caminhos(raiz)["spec"], md)
    c = contagem(e)
    print(f"Varredura registrada. Perguntas: {c['base']} da base + {c['escopo']} do escopo.")


def cmd_ficha(a, raiz):
    md, _ = carregar(raiz)
    if not a.chave:
        for k, v in S.ficha(md).items():
            print(f"{k}: {v}")
        return
    if a.valor is None:
        print(S.ficha(md).get(a.chave, ""))
        return
    S.gravar(caminhos(raiz)["spec"], S.set_ficha(md, a.chave, a.valor))
    print(f"{a.chave}: {a.valor}")


def cmd_sync(a, raiz):
    sync_decisoes(raiz)
    print("Decisões do SPEC.md atualizadas a partir da entrevista.")


# ---------- validações ----------
def ciclo_ou_conflitos(md):
    """Problemas estruturais das tasks: ids, dependências, ciclos e (se paralelo) sobreposição de arquivos."""
    erros = []
    tasks = S.todas_tasks(md)
    ids = [t["id"] for t in tasks]
    for i in set(ids):
        if ids.count(i) > 1:
            erros.append(f"task {i} duplicada")
    fids = [f["id"] for f in S.features(md)]
    for i in set(fids):
        if fids.count(i) > 1:
            erros.append(f"feature {i} duplicada")
    mapa = {t["id"]: t for t in tasks}
    for t in tasks:
        for d in t["depende"]:
            if d not in mapa:
                erros.append(f"{t['id']} depende de {d}, que não existe")

    visit = {}

    def dfs(x, pilha):
        if visit.get(x) == 2:
            return
        if visit.get(x) == 1:
            erros.append("ciclo de dependências: " + " → ".join(pilha + [x]))
            return
        visit[x] = 1
        for d in mapa.get(x, {}).get("depende", []):
            if d in mapa:
                dfs(d, pilha + [x])
        visit[x] = 2
    for i in ids:
        dfs(i, [])
    if S.ficha(md).get("tasks_paralelas", "não").lower().startswith("s"):
        def ancestrais(x, acc=None):
            acc = acc if acc is not None else set()
            for d in mapa.get(x, {}).get("depende", []):
                if d in mapa and d not in acc:
                    acc.add(d)
                    ancestrais(d, acc)
            return acc
        anc = {i: ancestrais(i) for i in ids}
        for i, a in enumerate(tasks):
            for b in tasks[i + 1:]:
                if a["id"] in anc[b["id"]] or b["id"] in anc[a["id"]]:
                    continue
                comum = set(a["toca"]) & set(b["toca"])
                if comum:
                    erros.append(f"{a['id']} e {b['id']} podem rodar juntas mas tocam os mesmos arquivos ({', '.join(sorted(comum))}): "
                                 "declare dependência ou separe os arquivos")
    return erros


def _erros_plano_testes(md, feats):
    """Todo feature precisa de pelo menos um teste planejado (ou um 'n-a' com motivo); campos válidos."""
    erros = []
    ts = S.testes(md)
    ids = [t["id"] for t in ts]
    for i in set(ids):
        if ids.count(i) > 1:
            erros.append(f"teste {i} duplicado")
    fids = {f["id"] for f in feats}
    for f in feats:
        if not any(t["feature"] == f["id"] for t in ts):
            erros.append(f"{f['id']}: sem teste no plano (seção 7). Defina ao menos um, ou registre `n-a` com o motivo.")
    for t in ts:
        if t["estado"] not in S.TESTE_ESTADOS:
            erros.append(f"{t['id']}: estado inválido '{t['estado']}'")
        if t["quando"] not in S.TESTE_QUANDO:
            erros.append(f"{t['id']}: 'quando' inválido '{t['quando']}' (use {', '.join(S.TESTE_QUANDO)})")
        if t["modo"] not in ("autonomo", "manual"):
            erros.append(f"{t['id']}: 'modo' inválido '{t['modo']}' (autonomo ou manual)")
        if t["feature"] and t["feature"] not in {x["id"] for x in S.features(md)}:
            erros.append(f"{t['id']}: feature '{t['feature']}' não existe")
        if t["estado"] == "n-a" and not t["motivo_momento"]:
            erros.append(f"{t['id']}: 'n-a' precisa de `motivo_momento` explicando por que não se aplica")
        if t["estado"] != "n-a" and not (t["como"] and t["criterio"]):
            erros.append(f"{t['id']}: falta `como` e/ou `criterio`")
    return erros


def _erros_execucao_testes(md, momentos):
    erros = []
    for t in S.testes(md):
        if t["quando"] not in momentos:
            continue
        if t["estado"] in ("passou", "n-a"):
            continue
        rot = {"falhou": "FALHOU (corrija e rode de novo)", "bloqueado": "bloqueado", "em-execucao": "ainda em execução"}.get(t["estado"], "ainda não executado")
        erros.append(f"{t['id']} ({S.QUANDO_NOME.get(t['quando'], t['quando'])}, {t['modo']}): {rot}.")
    return erros


def erros_de_gate(raiz, atual, destino):
    md, e = carregar(raiz)
    erros = []
    feats = [f for f in S.features(md) if f["estado"] != "descartada"]
    if atual == "entrada" and destino == "entrevista":
        if S.vazio(S.corpo(md, 1)):
            erros.append("Seção 1 (Objetivo) ainda está vazia: registre o briefing ou a ideia antes de entrevistar.")
    elif atual == "entrevista" and destino == "spec":
        c = contagem(e) if e else {"pendentes": 0, "aguardando": 0}
        c = dict(c, pendentes=c["pendentes"] + c.get("aguardando", 0) + c.get("revisar", 0))
        if e and _nao_verificadas(e):
            erros.append(f"{len(_nao_verificadas(e))} resposta(s) do cliente sem verificação de impacto na lista completa: rode `impacto`, "
                         "revise o que for afetado e registre com `impacto-ok`.")
        if S.ficha(md).get("varredura_lacunas", "não") != "feita":
            erros.append("Falta a varredura de lacunas: releia briefing e respostas, adicione as perguntas que o escopo "
                         "pede (`add`) e registre com `varredura`.")
        if c["pendentes"]:
            ids = [p["id"] for p in visiveis(e) if estado_p(p) in ("pendente", "aguardando", "revisar")]
            erros.append(f"{c['pendentes']} perguntas pendentes ({', '.join(ids[:8])}{'...' if len(ids) > 8 else ''}). "
                         "Responda ou use bypass (pergunta a pergunta ou em lote).")
    elif atual == "spec" and destino == "features":
        for n, nome in ((1, "Objetivo"), (2, "Escopo e requisitos")):
            if S.vazio(S.corpo(md, n)):
                erros.append(f"Seção {n} ({nome}) ainda está vazia.")
    elif atual == "features" and destino == "tasks":
        ents = {x["id"] for x in S.entregas(md)}
        if not ents:
            erros.append("Seção 5 (Entregas) sem nenhuma entrega no formato `- E1 · Nome · objetivo`.")
        if not feats:
            erros.append("Nenhuma feature na seção 6.")
        for f in feats:
            if f["entrega"] not in ents:
                erros.append(f"{f['id']}: entrega '{f['entrega']}' não existe na seção 5.")
            if not f["aceite"]:
                erros.append(f"{f['id']}: falta critério de aceite.")
            if f["estado"] == "proposta":
                erros.append(f"{f['id']}: ainda está como proposta (precisa da sua aprovação → aprovada).")
    elif atual == "tasks" and destino == "construcao":
        for f in feats:
            if not f["tasks"]:
                erros.append(f"{f['id']}: sem tasks.")
            for t in f["tasks"]:
                for campo in ("toca", "aceite", "teste"):
                    if not t[campo]:
                        erros.append(f"{t['id']}: campo '{campo}' vazio.")
        erros += ciclo_ou_conflitos(md)
        erros += _erros_plano_testes(md, feats)
    elif atual == "construcao" and destino == "testes":
        for f in feats:
            if f["estado"] not in ("em-teste", "entregue"):
                erros.append(f"{f['id']}: está '{f['estado']}' (precisa estar em-teste ou entregue).")
            for t in f["tasks"]:
                if t["estado"] != "feita":
                    erros.append(f"{t['id']}: task {t['estado']}.")
        erros += _erros_execucao_testes(md, ("durante-build",))
    elif atual == "testes" and destino == "deploy":
        erros += _erros_execucao_testes(md, ("durante-build", "antes-deploy"))
    elif atual == "deploy" and destino == "manutencao":
        dp = S.deploy(md)
        if not dp["checklist"]:
            erros.append("Checklist de deploy vazio: rode `deploy-init` e conclua os itens.")
        for it in dp["checklist"]:
            if it["estado"] not in ("feito", "n-a"):
                erros.append(f"{it['id']} ({it['titulo'][:50]}): {it['estado']}.")
        if not any(x["ambiente"] == "producao" and x["resultado"] == "ok" for x in dp["publicacoes"]):
            erros.append("Nenhuma publicação OK em produção registrada: use `deploy-registrar --ambiente producao --resultado ok --url ...`.")
        if not dp["info"].get("url"):
            erros.append("Falta a URL de produção na seção 8 (`deploy-info url https://...`).")
        for f in feats:
            if f["estado"] != "entregue":
                erros.append(f"{f['id']}: está '{f['estado']}' (precisa estar entregue).")
        erros += _erros_execucao_testes(md, ("pos-deploy",))
    return erros


def cmd_gate(a, raiz):
    md, _ = carregar(raiz)
    atual = S.ficha(md).get("fase", "entrada")
    i = S.FASES.index(atual)
    if i + 1 >= len(S.FASES):
        print("Já estamos na última fase (manutenção).")
        return
    destino = S.FASES[i + 1]
    erros = erros_de_gate(raiz, atual, destino)
    if erros:
        print(f"Não dá para ir de {S.FASES_NOME[atual]} para {S.FASES_NOME[destino]}:")
        for x in erros:
            print(f"  - {x}")
        sys.exit(1)
    print(f"Liberado: {S.FASES_NOME[atual]} → {S.FASES_NOME[destino]}.")


def cmd_fase(a, raiz):
    md, _ = carregar(raiz)
    atual = S.ficha(md).get("fase", "entrada")
    if a.destino not in S.FASES:
        die(f"fase inválida. Use: {', '.join(S.FASES)}")
    i, j = S.FASES.index(atual), S.FASES.index(a.destino)
    if j > i and not a.forcar:
        if j != i + 1:
            die(f"só é possível avançar uma fase por vez (agora: {atual}). Use --forcar para pular.")
        erros = erros_de_gate(raiz, atual, a.destino)
        if erros:
            print("Pendências que impedem o avanço:")
            for x in erros:
                print(f"  - {x}")
            sys.exit(1)
    md = S.set_ficha(md, "fase", a.destino)
    nota = " (forçado)" if a.forcar and j > i else ""
    md = S.add_historico(md, f"fase: {S.FASES_NOME[atual]} → {S.FASES_NOME[a.destino]}{nota}")
    S.gravar(caminhos(raiz)["spec"], md)
    import render
    render.render_all(raiz)
    print(f"Fase agora: {S.FASES_NOME[a.destino]}")


def cmd_check(a, raiz):
    md, _ = carregar(raiz)
    erros = ciclo_ou_conflitos(md)
    ents = {x["id"] for x in S.entregas(md)}
    if S.testes(md):
        erros += _erros_plano_testes(md, [f for f in S.features(md) if f["estado"] != "descartada"])
    for f in S.features(md):
        if f["estado"] not in S.ESTADOS_FEATURE:
            erros.append(f"{f['id']}: estado inválido '{f['estado']}'")
        if f["entrega"] and ents and f["entrega"] not in ents:
            erros.append(f"{f['id']}: entrega '{f['entrega']}' inexistente")
    if erros:
        print("Problemas no SPEC.md:")
        for x in erros:
            print(f"  - {x}")
        sys.exit(1)
    print("SPEC.md consistente.")


def cmd_ready(a, raiz):
    md, _ = carregar(raiz)
    mapa = {t["id"]: t for t in S.todas_tasks(md)}
    estado_f = {f["id"]: f["estado"] for f in S.features(md)}
    prontas = [t for t in mapa.values() if t["estado"] == "pendente"
               and estado_f.get(t["feature"]) in ("aprovada", "em-andamento", "alterada")
               and all(mapa.get(d, {}).get("estado") == "feita" for d in t["depende"])]
    lote, usados = [], set()
    for t in prontas:
        if not (set(t["toca"]) & usados):
            lote.append(t)
            usados |= set(t["toca"])
    fora = [t for t in prontas if t not in lote]
    if a.json:
        print(json.dumps({"lote_paralelo": lote, "esperam_arquivos": fora}, ensure_ascii=False, indent=1))
        return
    if not prontas:
        print("Nenhuma task pronta para iniciar.")
        return
    paralelo = S.ficha(md).get("tasks_paralelas", "não") == "sim"
    if not paralelo:
        t0 = prontas[0]
        print("Próxima task (modo sequencial; uma por vez):")
        print(f"  {t0['id']} · {t0['titulo']} · dono: {t0['dono'] or '—'} · toca: {', '.join(t0['toca']) or '—'}")
        if len(prontas) > 1:
            print(f"Depois dela já estão liberadas: {', '.join(x['id'] for x in prontas[1:])}.")
        return
    print("Podem rodar JUNTAS agora (arquivos disjuntos):")
    for t in lote:
        print(f"  {t['id']} · {t['titulo']} · dono: {t['dono'] or '—'} · toca: {', '.join(t['toca']) or '—'}")
    if fora:
        print("Prontas, mas disputam arquivos com as de cima (rodar depois):")
        for t in fora:
            print(f"  {t['id']} · {t['titulo']}")


def cmd_set_feature(a, raiz):
    md, _ = carregar(raiz)
    md = S.set_estado_feature(md, a.id, a.estado)
    md = S.add_historico(md, f"{a.id} → {a.estado}")
    S.gravar(caminhos(raiz)["spec"], md)
    print(f"{a.id}: {a.estado}")


def cmd_set_task(a, raiz):
    md, _ = carregar(raiz)
    md = S.set_marca_task(md, a.id, a.estado)
    t = next(x for x in S.todas_tasks(md) if x["id"] == a.id)
    feat = next(f for f in S.features(md) if f["id"] == t["feature"])
    dica = ""
    if a.estado == "andamento" and feat["estado"] == "aprovada":
        md = S.set_estado_feature(md, feat["id"], "em-andamento")
        md = S.add_historico(md, f"{feat['id']} → em-andamento (primeira task iniciada: {a.id})")
    if a.estado == "feita":
        feat = next(f for f in S.features(md) if f["id"] == t["feature"])
        if all(x["estado"] == "feita" for x in feat["tasks"]) and feat["estado"] in ("aprovada", "em-andamento"):
            dica = f" Todas as tasks de {feat['id']} estão feitas: mova a feature para em-teste (`set-feature {feat['id']} em-teste`)."
    S.gravar(caminhos(raiz)["spec"], md)
    print(f"{a.id}: {a.estado}.{dica}")


DEPLOY_PADRAO = [
    ("Ambiente de produção criado no provedor", ("S-02", "A-03")),
    ("Variáveis de ambiente e segredos configurados no provedor (nunca no repositório)", ("SG-03",)),
    ("Domínio e DNS apontados, com HTTPS ativo", ("DP-02",)),
    ("Banco de dados e migrações aplicados em produção", ("D-03",)),
    ("Backup configurado e restauração testada", ("D-05",)),
    ("Monitoramento e alertas ativos", ("A-05", "DP-05")),
    ("Plano de reversão conferido (como voltar à versão anterior)", ("DP-04",)),
    ("Contas dos serviços no nome combinado", ("DP-03",)),
    ("Forma de publicação conforme decidido (automática ou manual)", ("DP-01",)),
]


def cmd_deploy_init(a, raiz):
    md, e = carregar(raiz)
    d = S.deploy(md)
    if d["checklist"] and not a.forcar:
        die("o checklist de deploy já existe. Use --forcar para recriar (perde o andamento).")
    por_id = {p["id"]: p for p in e["perguntas"]} if e else {}

    def decisao(i):
        p = por_id.get(i)
        return f"{i}: {texto_resposta(p)}" if p and p.get("resposta") and p["resposta"]["tipo"] != "bypass" else ""
    linhas = ["Onde o sistema está no ar, como publicar de novo, como reverter e o checklist da publicação.", "",
              "- ambiente: producao", f"- como_publicar: {decisao('DP-01').split(': ', 1)[-1] or 'a definir'}",
              f"- como_reverter: {decisao('DP-04').split(': ', 1)[-1] or 'a definir'}",
              f"- monitoramento: {(decisao('A-05') or decisao('DP-05')).split(': ', 1)[-1] or 'a definir'}",
              f"- dominio: {decisao('DP-02').split(': ', 1)[-1] or 'a definir'}", "", "### Checklist", ""]
    for n, (titulo, ids) in enumerate(DEPLOY_PADRAO, 1):
        linhas.append(f"- [ ] CK-{n:03d} · {titulo}")
        nota = "; ".join(x for x in (decisao(i) for i in ids) if x)
        linhas.append(f"  - nota: {nota or 'decisão não registrada na entrevista: definir agora'}")
    linhas += ["", "### Publicações", "", "(nenhuma publicação ainda)"]
    novo = S.trocar_corpo(md, 8, "\n".join(linhas))
    S.gravar(caminhos(raiz)["spec"], S.add_historico(novo, "checklist de deploy criado a partir das decisões da entrevista"))
    print(f"Checklist de deploy criado com {len(DEPLOY_PADRAO)} itens a partir das decisões. Ajuste a seção 8 do SPEC.md se o projeto pedir mais.")


def cmd_set_deploy(a, raiz):
    md, _ = carregar(raiz)
    if a.estado not in S.CK_MARCA_DE:
        die(f"estado inválido: {a.estado}. Use: {', '.join(S.CK_MARCA_DE)}")
    if a.estado == "n-a" and not a.evidencia:
        die("n-a exige a justificativa: use --evidencia \"por que não se aplica\".")
    md = S.set_marca_checklist(md, a.id, a.estado, a.evidencia)
    md = S.add_historico(md, f"{a.id} → {a.estado}" + (f" (evidência: {a.evidencia})" if a.evidencia else ""))
    S.gravar(caminhos(raiz)["spec"], md)
    print(f"{a.id}: {a.estado}")


def cmd_deploy_info(a, raiz):
    md, _ = carregar(raiz)
    S.gravar(caminhos(raiz)["spec"], S.set_info_deploy(md, a.chave, a.valor))
    print(f"{a.chave}: {a.valor}")


def cmd_deploy_registrar(a, raiz):
    md, _ = carregar(raiz)
    extras = " ".join(x for x in ((f"url={a.url}" if a.url else ""), (f"commit={a.commit}" if a.commit else ""), (a.nota or "")) if x)
    md = S.add_publicacao(md, f"- {S.hoje()} · {a.ambiente} · {a.resultado}" + (f" · {extras}" if extras else ""))
    if a.resultado == "ok" and a.ambiente == "producao" and a.url:
        md = S.set_info_deploy(md, "url", a.url)
    md = S.add_historico(md, f"publicação em {a.ambiente}: {a.resultado}" + (f" ({a.url})" if a.url else ""))
    S.gravar(caminhos(raiz)["spec"], md)
    print(f"Publicação registrada: {a.ambiente} · {a.resultado}")


def cmd_migrar(a, raiz):
    """Atualiza um SPEC.md criado antes da seção de Deploy (renumera e insere a seção 8)."""
    md, _ = carregar(raiz)
    if re.search(r"^## 8\. Deploy", md, re.M):
        print("SPEC.md já está na versão atual.")
        return
    if not re.search(r"^## 8\. Change requests", md, re.M):
        die("não reconheci a estrutura do SPEC.md (esperava '## 8. Change requests').")
    md = re.sub(r"^## 9\. Histórico", "## 10. Histórico", md, flags=re.M)
    secao = ("## 8. Deploy\n\nOnde o sistema está no ar, como publicar de novo, como reverter e o checklist da publicação. "
             "Preenchido na fase de Deploy (`deploy-init` monta o esqueleto).\n\n(nenhuma publicação ainda)\n\n## 9. Change requests")
    md = re.sub(r"^## 8\. Change requests", secao, md, count=1, flags=re.M)
    S.gravar(caminhos(raiz)["spec"], S.add_historico(md, "SPEC.md migrado: seção 8 (Deploy) criada; Change requests = 9; Histórico = 10"))
    print("Migrado: seção 8 (Deploy) criada; Change requests agora é a 9 e Histórico a 10.")


def cmd_testes(a, raiz):
    md, _ = carregar(raiz)
    ts = [t for t in S.testes(md) if not a.quando or t["quando"] == a.quando]
    if a.json:
        print(json.dumps(ts, ensure_ascii=False, indent=1))
        return
    if not ts:
        print("Nenhum teste no plano (seção 7).")
        return
    for q in S.TESTE_QUANDO:
        grupo = [t for t in ts if t["quando"] == q]
        if not grupo:
            continue
        print(f"== {S.QUANDO_NOME[q]}")
        for t in grupo:
            print(f"  {t['id']} [{S.TESTE_NOME.get(t['estado'], t['estado'])}] {t['titulo']} · {t['feature'] or '—'} · {t['tipo'] or '—'} · {t['modo']}")
            if t["estado"] in ("pendente", "em-execucao", "falhou"):
                print(f"      como: {t['como'] or '—'}")


def cmd_set_teste(a, raiz):
    md, _ = carregar(raiz)
    if a.estado not in S.TESTE_ESTADOS:
        die(f"estado inválido: {a.estado}. Use: {', '.join(S.TESTE_ESTADOS)}")
    md = S.set_campo_teste(md, a.id, "estado", a.estado)
    if a.evidencia:
        md = S.set_campo_teste(md, a.id, "evidencia", a.evidencia)
    md = S.add_historico(md, f"{a.id} → {a.estado}" + (f" (evidência: {a.evidencia})" if a.evidencia else ""))
    S.gravar(caminhos(raiz)["spec"], md)
    dica = " Crie uma task de correção e rode o teste de novo." if a.estado == "falhou" else ""
    print(f"{a.id}: {a.estado}.{dica}")


def cmd_rodar_teste(a, raiz):
    """Roda o comando do teste, guarda a saída como evidência e registra passou/falhou pelo código de saída (nunca no escuro)."""
    import subprocess
    md, _ = carregar(raiz)
    t = next((x for x in S.testes(md) if x["id"] == a.id), None)
    if not t:
        die(f"teste {a.id} não existe")
    if t["modo"] == "manual" and not a.cmd:
        die(f"{a.id} é manual: entregue o roteiro ao usuário e registre com `set-teste {a.id} passou|falhou --evidencia \"quem aceitou e quando\"`.")
    cmd = a.cmd or t["como"]
    if not cmd.strip():
        die(f"{a.id} não tem comando em `como`: passe --cmd.")
    pasta = os.path.join(raiz, "docs", "evidencias")
    os.makedirs(pasta, exist_ok=True)
    quando = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    rel = f"docs/evidencias/{a.id.lower()}-{quando}.log"
    print(f"$ {cmd}")
    try:
        r = subprocess.run(cmd, shell=True, cwd=raiz, capture_output=True, text=True, timeout=a.timeout)
        rc, saida = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as ex:
        rc, saida = 124, ((ex.stdout or b"").decode() if isinstance(ex.stdout, bytes) else (ex.stdout or "")) + f"\n(interrompido após {a.timeout}s)"
    if rc == 127:
        die(f"comando não encontrado (código 127). Se `como` for um roteiro e não um comando, rode você mesmo e use `set-teste` com a evidência.\n{saida.strip()[-300:]}")
    with open(os.path.join(raiz, rel), "w", encoding="utf-8") as fh:
        fh.write(f"$ {cmd}\n# {quando} UTC\n\n{saida}\n# código de saída: {rc}\n")
    estado = "passou" if rc == 0 else "falhou"
    md = S.set_campo_teste(md, a.id, "estado", estado)
    md = S.set_campo_teste(md, a.id, "evidencia", rel)
    md = S.add_historico(md, f"{a.id} → {estado} (evidência: {rel})")
    S.gravar(caminhos(raiz)["spec"], md)
    cauda = "\n".join(saida.strip().splitlines()[-12:])
    print(cauda + f"\n\n{a.id}: {estado} (código de saída {rc}). Evidência: {rel}"
          + (" Crie uma task de correção e rode o teste de novo." if rc else ""))
    if rc:
        sys.exit(1)


def cmd_descartar(a, raiz):
    _, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    if not p:
        die(f"pergunta {a.id} não existe")
    if a.desfazer:
        p.pop("descartada", None)
        salvar_entrev(raiz, e)
        sync_decisoes(raiz)
        print(f"{a.id}: de volta à entrevista.")
        return
    if p.get("resposta") or p.get("respostas_cliente"):
        die("pergunta já respondida: não dá para descartar")
    if not a.motivo:
        die("informe --motivo (por que não se aplica a este projeto)")
    p["descartada"] = {"motivo": a.motivo, "em": S.agora()}
    p.pop("cliente", None)
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{a.id}: não se aplica ({a.motivo}). Fica registrada no SPEC.md.")


def cmd_plano(a, raiz):
    """Plano de perguntas: como a entrevista está montada (escopo × base × descartadas), por bloco."""
    _, e = carregar(raiz)
    vs = visiveis(e)
    blocos = []
    for b in e["blocos"]:
        ps = [p for p in vs if p["bloco"] == b["id"]]
        desc = [p for p in e["perguntas"] if p["bloco"] == b["id"] and p.get("descartada")]
        if ps or desc:
            blocos.append({"bloco": b["nome"], "escopo": sum(1 for p in ps if p.get("origem") == "escopo"),
                           "base": sum(1 for p in ps if p.get("origem", "base") == "base"), "descartadas": len(desc),
                           "para_o_cliente": sum(1 for p in ps if vai_ao_cliente(p)),
                           "sugeridas_cliente": sum(1 for p in ps if p.get("selecao_cliente") == "sugerida" and vai_ao_cliente(p))})
    if a.json:
        print(json.dumps(blocos, ensure_ascii=False, indent=1))
        return
    print(f"{'Bloco':26s} escopo  base  descartadas  p/ cliente  sugeridas")
    for b in blocos:
        print(f"{b['bloco']:26s} {b['escopo']:6d} {b['base']:5d} {b['descartadas']:12d} {b['para_o_cliente']:11d} {b['sugeridas_cliente']:10d}")
    print(f"Total visível: {len(vs)} perguntas.")


def _livres(p):
    """Fora da lista do cliente (e o cliente não respondeu): pode ser ligada."""
    return not vai_ao_cliente(p) and not p.get("respostas_cliente")


def _sugeridas(e):
    """Marcadas por mim e ainda sem decisão explícita do usuário: vão ao cliente se ele não desmarcar."""
    return [p for p in visiveis(e) if p.get("selecao_cliente") == "sugerida" and p.get("cliente") is None and vai_ao_cliente(p)
            and not p.get("respostas_cliente")]


def _com_texto_pronto(e):
    """Fora da lista, com texto de negócio disponível (o usuário pode ligar), sem as que ele dispensou."""
    return [p for p in visiveis(e) if p.get("selecao_cliente") != "dispensada" and (p.get("neg") or {}).get("q") and _livres(p)]


def cmd_lista_cliente(a, raiz):
    """A lista inicial do cliente: direcionadas, sugeridas por mim (marcadas na lista completa) e demais com texto pronto."""
    _, e = carregar(raiz)
    dirs = [p for p in visiveis(e) if (p.get("cliente") or {}).get("ativa") and not p.get("respostas_cliente")]
    sug, outras = _sugeridas(e), _com_texto_pronto(e)
    dispensadas = [p for p in visiveis(e) if p.get("selecao_cliente") == "dispensada" and not vai_ao_cliente(p)]

    def item(p):
        return {"id": p["id"], "bloco": nome_bloco(e, p["bloco"]), "tecnica": p["q"], "texto": p["neg"]["q"], "opcoes": p["neg"].get("o", []),
                "design": bool(p.get("design"))}
    if a.json:
        print(json.dumps({"direcionadas": [{"id": p["id"], "texto": p["cliente"]["texto"], "opcoes": p["cliente"].get("opcoes", [])} for p in dirs],
                          "sugeridas": [item(p) for p in sug], "com_texto_pronto": [item(p) for p in outras],
                          "dispensadas": [item(p) for p in dispensadas]}, ensure_ascii=False, indent=1))
        return
    print(f"Direcionadas ao cliente ({len(dirs)}):")
    for p in dirs:
        print(f"  [{p['id']}] {p['cliente']['texto']}")
    print(f"\n📌 Marcadas por mim (VÃO ao cliente se o usuário não desmarcar) ({len(sug)}):")
    for p in sug:
        print(f"  [{p['id']}] {p['neg']['q']}{'  (design: leva opções visuais)' if p.get('design') else ''}")
    print(f"\nOutras com texto pronto, que você pode escolher ({len(outras)}):")
    for p in (outras if a.todas else outras[:8]):
        print(f"  [{p['id']}] {p['neg']['q']}")
    if not a.todas and len(outras) > 8:
        print(f"  ... e mais {len(outras) - 8} (use --todas para listar)")
    disp = [p["id"] for p in dispensadas]
    if disp:
        print(f"\nSugestões que o usuário DISPENSOU ({len(disp)}): {', '.join(disp)}")
    print("\nAprovando: `cliente-lote --sugeridas` ou `cliente-lote --ids A,B`; depois `export-cliente`. "
          "Para mudar a seleção: `sugerir-cliente --ids A,B` / `--remover`.")


def cmd_sugerir_cliente(a, raiz):
    """Marca (ou desmarca) na lista completa as perguntas que eu sugiro para o cliente, usando o texto pronto."""
    _, e = carregar(raiz)
    ids = [x.strip() for x in a.ids.split(",") if x.strip()]
    n = 0
    for pid in ids:
        p = next((x for x in e["perguntas"] if x["id"] == pid), None)
        if not p:
            die(f"pergunta {pid} não existe")
        if a.remover:
            p.pop("selecao_cliente", None)
            n += 1
            continue
        if not (p.get("neg") or {}).get("q"):
            die(f"{pid} não tem texto em linguagem de negócio: use `cliente {pid} --sugerir --texto \"...\"`")
        if p.get("selecao_cliente") == "dispensada" and not a.forcar:
            print(f"  {pid}: o usuário DISPENSOU esta sugestão; não vou marcar de novo (use --forcar se ele pediu).")
            continue
        p["selecao_cliente"] = "sugerida"
        n += 1
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{n} pergunta(s) {'desmarcada(s)' if a.remover else 'marcada(s) como sugerida(s) para o cliente'}.")


def cmd_cliente_lote(a, raiz):
    _, e = carregar(raiz)
    alvo = _sugeridas(e) if a.sugeridas else [p for p in e["perguntas"] if p["id"] in set(x.strip() for x in (a.ids or "").split(",") if x.strip())]
    if not alvo:
        die("nada para direcionar: informe --ids A,B ou --sugeridas")
    n = 0
    for p in alvo:
        neg = p.get("neg") or {}
        if not neg.get("q") or p.get("descartada") or p.get("respostas_cliente"):
            print(f"  {p['id']}: pulada (sem texto de negócio, descartada ou o cliente já respondeu)")
            continue
        cl = {"ativa": True, "texto": neg["q"], "opcoes": neg.get("o", []), "em": S.agora(), "arquivo": False, "arquivo_desc": "", "visuais": [], "refs": []}
        if p.get("design"):
            cl["visuais"] = [{"tipo": t, "titulo": CH.TITULOS[t], "opcoes": CH.opcoes_padrao(t)} for t in ("paleta", "layout")]
        p["cliente"] = cl
        n += 1
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{n} perguntas direcionadas ao cliente. Rode `export-cliente` para gerar a página.")


def estado_pagina_cliente(md, e):
    """Compara o que DEVERIA estar na página do cliente com o que foi gerado/publicado."""
    f = S.ficha(md)
    deve = sorted(p["id"] for p in _cliente_ativas(e)) if e else []
    pg = (e or {}).get("pagina_cliente") or {}
    gerada = pg.get("ids", [])
    ainda_ativas_na_gerada = [i for i in gerada if i in deve]
    faltam = [i for i in deve if i not in gerada]
    sobram = [i for i in gerada if i not in deve and not any(x["id"] == i and x.get("respostas_cliente") for x in (e or {}).get("perguntas", []))]
    pub = f.get("cliente_publicada_em", "")
    return {"url": f.get("cliente_url", ""), "site_id": f.get("cliente_site_id", ""), "gerada_em": pg.get("gerada_em", ""), "publicada_em": pub,
            "deve": deve, "gerada": gerada, "faltam": faltam, "sobram": sobram,
            "publicada": bool(pub) and bool(pg.get("gerada_em")) and pub >= pg.get("gerada_em", ""),
            "desatualizada": bool(faltam or sobram),
            "a_publicar": bool(pg.get("gerada_em")) and not (bool(pub) and pub >= pg["gerada_em"])}


def cmd_hist(a, raiz):
    md, _ = carregar(raiz)
    S.gravar(caminhos(raiz)["spec"], S.add_historico(md, a.texto))
    print("Registrado no histórico.")


def cmd_new_id(a, raiz):
    md, e = carregar(raiz)
    print(S.proximo_id(md, a.prefixo))


def cmd_cr_new(a, raiz):
    md, _ = carregar(raiz)
    cid = S.proximo_id(md, "CR")
    bloco = f"### {cid} · {a.titulo}\n- estado: aberta\n- data: {S.hoje()}\n- features: {a.features or '—'}\n- motivo: {a.motivo or '—'}\n"
    for s in S.secoes(md):
        if s["num"] == 9:
            corpo7 = md[s["ini"]:s["fim"]].rstrip("\n")
            md = md[:s["ini"]] + corpo7 + "\n\n" + bloco + "\n" + md[s["fim"]:]
            break
    md = S.add_historico(md, f"{cid} aberta: {a.titulo}")
    S.gravar(caminhos(raiz)["spec"], md)
    print(cid)


def cmd_cr_set(a, raiz):
    md, _ = carregar(raiz)
    cr = next((c for c in S.change_requests(md) if c["id"] == a.id), None)
    if not cr:
        die(f"{a.id} não encontrada")
    if a.estado == "entregue" and not a.forcar:
        erros = []
        alvo = set(cr["features"])
        for tk in S.todas_tasks(md):
            if tk["feature"] in alvo and tk["estado"] != "feita":
                erros.append(f"{tk['id']} ({tk['feature']}): task {tk['estado']}.")
        for ts in S.testes(md):
            if ts["feature"] in alvo and ts["estado"] not in ("passou", "n-a"):
                erros.append(f"{ts['id']} ({S.QUANDO_NOME.get(ts['quando'], ts['quando'])}, {ts['modo']}): {ts['estado']}.")
        if not alvo:
            erros.append("A CR não lista features afetadas: preencha `features:` para o motor poder conferir tasks e testes.")
        if erros:
            die(f"{a.id} ainda não pode ser entregue:\n  - " + "\n  - ".join(erros)
                + "\nTermine as tasks, rode os testes (inclusive os pós-deploy, depois de publicar) ou use --forcar sabendo o que está pulando.")
    m = re.search(rf"^### {re.escape(a.id)} · .*$", S.mascara(md), re.M)
    resto = S.mascara(md)[m.end():]
    prox = re.search(r"^## |^### ", resto, re.M)
    fim = m.end() + (prox.start() if prox else len(resto))
    bloco = md[m.start():fim]
    bloco = re.sub(r"^- estado:.*$", f"- estado: {a.estado}", bloco, count=1, flags=re.M)
    md = md[:m.start()] + bloco + md[fim:]
    if a.estado == "aprovada":
        for fid in cr["features"]:
            try:
                md = S.set_estado_feature(md, fid, "alterada")
            except KeyError:
                pass
    if a.estado == "entregue":
        for fid in cr["features"]:
            f_ = next((x for x in S.features(md) if x["id"] == fid), None)
            if f_ and f_["estado"] == "alterada":
                md = S.set_estado_feature(md, fid, "entregue")
    md = S.add_historico(md, f"{a.id} → {a.estado}")
    S.gravar(caminhos(raiz)["spec"], md)
    print(f"{a.id}: {a.estado}" + (" (features alteradas voltaram a entregue)" if a.estado == "entregue" else ""))


def cmd_render(a, raiz):
    import render
    for x in render.render_all(raiz):
        print(x)


def main():
    ap = argparse.ArgumentParser(prog="spec.py", description="Motor da skill spec-flow")
    ap.add_argument("--raiz", help="pasta do projeto (padrão: sobe a partir da pasta atual até achar SPEC.md)")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("init", help="cria SPEC.md e a entrevista")
    p.add_argument("nome")
    p.add_argument("--tipo", required=True)
    p.add_argument("--prof", choices=["p", "m", "c"], default="m")
    p.add_argument("--forcar", action="store_true")
    p.set_defaults(f=cmd_init, sem_raiz=True)

    p = sp.add_parser("status")
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_status)

    p = sp.add_parser("next", help="próximas perguntas pendentes")
    p.add_argument("-n", type=int, default=4)
    p.add_argument("--bloco")
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_next)

    p = sp.add_parser("answer")
    p.add_argument("id")
    p.add_argument("--opt", help="número(s) da opção, ex.: 1 ou 2,3")
    p.add_argument("--text")
    p.add_argument("--bypass", action="store_true")
    p.set_defaults(f=cmd_answer)

    p = sp.add_parser("dica", help="anota o que o briefing já diz sobre a pergunta (você confirma; nada é respondido)")
    p.add_argument("id")
    p.add_argument("texto")
    p.set_defaults(f=cmd_dica)
    p = sp.add_parser("rec", help="troca a opção recomendada de uma pergunta pendente (a escolhida vai para o topo)")
    p.add_argument("id")
    p.add_argument("n", type=int)
    p.add_argument("--nota", help="por que esta é a recomendada neste projeto")
    p.set_defaults(f=cmd_rec)
    p = sp.add_parser("cliente", help="direciona a pergunta ao dono do negócio (ou só sugere / remove)")
    p.add_argument("id")
    p.add_argument("--texto", help="a pergunta em linguagem de negócio (padrão: a sugestão do banco)")
    p.add_argument("--opt", action="append", help="opção em linguagem de negócio (repita; opcional)")
    p.add_argument("--sugerir", action="store_true", help="só registra a sugestão, sem direcionar")
    p.add_argument("--arquivo", action="store_true", help="o cliente poderá enviar um arquivo (limite de 8 MB; maior = o desenvolvedor pega)")
    p.add_argument("--arquivo-desc", help="o que o cliente deve enviar (ex.: 'a planilha de clientes')")
    p.add_argument("--design", action="store_true", help="pergunta de design: exige opções visuais e/ou links de referência")
    p.add_argument("--visual", action="append", help="grupo de opções visuais padrão: paleta, layout ou tipografia (repita)")
    p.add_argument("--visual-opt", action="append", help="opção visual própria: 'tipo|Rótulo|dado' (paleta: #hex,#hex; layout: hero|painel|grade|lista)")
    p.add_argument("--ref", action="append", help="link de referência para o cliente olhar: URL ou 'Rótulo|URL' (repita)")
    p.add_argument("--remover", action="store_true")
    p.set_defaults(f=cmd_cliente)
    p = sp.add_parser("export-cliente", help="gera .spec/cliente/ (página do dono do negócio, para o Netlify)")
    p.add_argument("--intro", help="texto de abertura da página")
    p.set_defaults(f=cmd_export_cliente)
    p = sp.add_parser("import-cliente", help="importa os envios do formulário do cliente")
    p.add_argument("arquivo")
    p.set_defaults(f=cmd_import_cliente)
    p = sp.add_parser("reabrir", help="reabre uma pergunta já respondida (a resposta anterior vai para o histórico)")
    p.add_argument("id")
    p.add_argument("--motivo")
    p.set_defaults(f=cmd_reabrir)
    p = sp.add_parser("revisar", help="marca uma decisão já tomada para revisão (afetada por resposta do cliente)")
    p.add_argument("id")
    p.add_argument("--motivo", required=True)
    p.add_argument("--origem", help="ID da pergunta do cliente que motivou")
    p.set_defaults(f=cmd_revisar)
    p = sp.add_parser("revisao-ok", help="encerra a revisão mantendo a decisão")
    p.add_argument("id")
    p.add_argument("--nota")
    p.set_defaults(f=cmd_revisao_ok)
    p = sp.add_parser("impacto", help="checklist: respostas novas do cliente × decisões já tomadas")
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_impacto)
    p = sp.add_parser("impacto-ok", help="registra que o impacto das respostas do cliente foi verificado")
    p.set_defaults(f=cmd_impacto_ok)
    p = sp.add_parser("bypass-all", help="pula todas as pendentes (ou de um bloco)")
    p.add_argument("--bloco")
    p.add_argument("--motivo")
    p.set_defaults(f=cmd_bypass_all)

    p = sp.add_parser("add", help="adiciona pergunta sob medida (a 1ª --opt é a recomendada)")
    p.add_argument("--id")
    p.add_argument("--bloco", required=True)
    p.add_argument("--bloco-nome")
    p.add_argument("--q", required=True)
    p.add_argument("--why")
    p.add_argument("--opt", action="append")
    p.add_argument("--multi", action="store_true")
    p.add_argument("--neg", help="OBRIGATÓRIO: a mesma pergunta em linguagem de negócio, pronta para o dono do negócio (o botão Direcionar já abre com ela)")
    p.add_argument("--neg-opt", action="append", help="opção de resposta em linguagem de negócio (repita; opcional)")
    p.add_argument("--design", action="store_true", help="marca como pergunta de design (ao direcionar ao cliente exige opções visuais ou referências)")
    p.add_argument("--motivo", help="o que no briefing ou numa resposta anterior gerou esta pergunta (ex.: 'briefing: marketplace')")
    p.set_defaults(f=cmd_add)

    p = sp.add_parser("varredura", help="registra que a varredura de lacunas foi feita")
    p.set_defaults(f=cmd_varredura)
    p = sp.add_parser("atualizar-textos", help="dá às perguntas da base o texto em linguagem de negócio que ainda não tinham")
    p.set_defaults(f=cmd_atualizar_textos)
    p = sp.add_parser("export-web", help="gera .spec/entrevista.html (página do celular) com as perguntas e respostas atuais")
    p.set_defaults(f=cmd_export_web)
    p = sp.add_parser("import-answers", help="importa respostas vindas da página do celular")
    p.add_argument("arquivo")
    p.set_defaults(f=cmd_import)
    p = sp.add_parser("ficha", help="lê ou grava campos da Ficha (ex.: ficha entrevista_web URL)")
    p.add_argument("chave", nargs="?")
    p.add_argument("valor", nargs="?")
    p.set_defaults(f=cmd_ficha)
    p = sp.add_parser("sync", help="regrava o bloco de decisões do SPEC.md")
    p.set_defaults(f=cmd_sync)

    p = sp.add_parser("gate", help="diz se já pode avançar de fase")
    p.set_defaults(f=cmd_gate)
    p = sp.add_parser("fase", help="avança (com validação) ou volta de fase")
    p.add_argument("destino")
    p.add_argument("--forcar", action="store_true")
    p.set_defaults(f=cmd_fase)
    p = sp.add_parser("check", help="valida a estrutura do SPEC.md")
    p.set_defaults(f=cmd_check)
    p = sp.add_parser("ready", help="tasks prontas e quais podem rodar em paralelo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_ready)

    p = sp.add_parser("set-feature")
    p.add_argument("id")
    p.add_argument("estado", choices=S.ESTADOS_FEATURE)
    p.set_defaults(f=cmd_set_feature)
    p = sp.add_parser("set-task")
    p.add_argument("id")
    p.add_argument("estado", choices=list(S.MARCA_DE))
    p.set_defaults(f=cmd_set_task)
    p = sp.add_parser("testes", help="plano de testes por momento (durante a construção, antes ou depois do deploy)")
    p.add_argument("--quando", choices=S.TESTE_QUANDO)
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_testes)
    p = sp.add_parser("set-teste", help="registra o resultado de um teste (com evidência)")
    p.add_argument("id")
    p.add_argument("estado", choices=S.TESTE_ESTADOS)
    p.add_argument("--evidencia", help="caminho de log, captura de tela ou saída que prova")
    p.set_defaults(f=cmd_set_teste)
    p = sp.add_parser("rodar-teste", help="roda o comando do teste (campo `como` ou --cmd), guarda a saída em docs/evidencias e registra passou/falhou pelo código de saída")
    p.add_argument("id")
    p.add_argument("--cmd", help="comando a rodar no lugar do campo `como`")
    p.add_argument("--timeout", type=int, default=600)
    p.set_defaults(f=cmd_rodar_teste)
    p = sp.add_parser("descartar", help="pergunta da base que não se aplica a este projeto (fica registrada com o motivo)")
    p.add_argument("id")
    p.add_argument("--motivo")
    p.add_argument("--desfazer", action="store_true")
    p.set_defaults(f=cmd_descartar)
    p = sp.add_parser("plano", help="como a entrevista está montada: escopo × base × descartadas, por bloco")
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_plano)
    p = sp.add_parser("lista-cliente", help="lista inicial do cliente: direcionadas + sugeridas")
    p.add_argument("--json", action="store_true")
    p.add_argument("--todas", action="store_true", help="lista todas as perguntas com texto pronto")
    p.set_defaults(f=cmd_lista_cliente)
    p = sp.add_parser("sugerir-cliente", help="marca na lista completa as perguntas que eu sugiro para o cliente (texto pronto)")
    p.add_argument("--ids", required=True)
    p.add_argument("--forcar", action="store_true", help="marca mesmo as que o usuário dispensou (só se ele pedir)")
    p.add_argument("--remover", action="store_true")
    p.set_defaults(f=cmd_sugerir_cliente)
    p = sp.add_parser("cliente-lote", help="direciona várias perguntas ao cliente de uma vez, com as sugestões em linguagem de negócio")
    p.add_argument("--ids", help="IDs separados por vírgula")
    p.add_argument("--sugeridas", action="store_true", help="todas as sugeridas")
    p.set_defaults(f=cmd_cliente_lote)
    p = sp.add_parser("deploy-init", help="monta o checklist de deploy (seção 8) a partir das decisões da entrevista")
    p.add_argument("--forcar", action="store_true")
    p.set_defaults(f=cmd_deploy_init)
    p = sp.add_parser("set-deploy", help="muda o estado de um item do checklist de deploy (CK-xxx)")
    p.add_argument("id")
    p.add_argument("estado", choices=list(S.CK_MARCA_DE))
    p.add_argument("--evidencia")
    p.set_defaults(f=cmd_set_deploy)
    p = sp.add_parser("deploy-info", help="grava um campo da ficha de deploy (url, como_publicar, como_reverter, monitoramento, dominio)")
    p.add_argument("chave")
    p.add_argument("valor")
    p.set_defaults(f=cmd_deploy_info)
    p = sp.add_parser("deploy-registrar", help="registra uma publicação (e atualiza a URL de produção quando ok)")
    p.add_argument("--ambiente", default="producao")
    p.add_argument("--resultado", required=True, choices=["ok", "falhou", "revertido"])
    p.add_argument("--url")
    p.add_argument("--commit")
    p.add_argument("--nota")
    p.set_defaults(f=cmd_deploy_registrar)
    p = sp.add_parser("migrar", help="atualiza um SPEC.md antigo para a estrutura atual (seção 8 Deploy)")
    p.set_defaults(f=cmd_migrar)
    p = sp.add_parser("hist", help="registra uma linha no histórico")
    p.add_argument("texto")
    p.set_defaults(f=cmd_hist)
    p = sp.add_parser("new-id", help="próximo id livre (F, T ou CR)")
    p.add_argument("prefixo", choices=["F", "T", "CR", "E", "TS"])
    p.set_defaults(f=cmd_new_id)
    p = sp.add_parser("cr-new", help="abre um change request")
    p.add_argument("titulo")
    p.add_argument("--features")
    p.add_argument("--motivo")
    p.set_defaults(f=cmd_cr_new)
    p = sp.add_parser("cr-set", help="muda o estado de um change request")
    p.add_argument("id")
    p.add_argument("estado", choices=["aberta", "aprovada", "entregue", "descartada"])
    p.add_argument("--forcar", action="store_true", help="entrega mesmo com task ou teste pendente (diga ao usuário o que está sendo pulado)")
    p.set_defaults(f=cmd_cr_set)
    p = sp.add_parser("render", help="gera docs/spec.html e docs/painel.html")
    p.set_defaults(f=cmd_render)

    a = ap.parse_args()
    if getattr(a, "sem_raiz", False):
        a.raiz = a.raiz
        return a.f(a)
    raiz = achar_raiz(a.raiz or os.getcwd())
    if not raiz:
        die("SPEC.md não encontrado. Este projeto ainda não usa a spec-flow: rode `init`.")
    a.f(a, raiz)


if __name__ == "__main__":
    main()
