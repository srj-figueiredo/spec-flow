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
    return [p for p in e["perguntas"] if visivel(p, e)]


def estado_p(p):
    r = p.get("resposta")
    if not r:
        return "aguardando" if (p.get("cliente") or {}).get("ativa") else "pendente"
    return "bypass" if r["tipo"] == "bypass" else "respondida"


def nome_bloco(e, bid):
    for b in e.get("blocos", []):
        if b["id"] == bid:
            return b["nome"]
    return bid.capitalize()


def contagem(e):
    vs = visiveis(e)
    c = {"total": len(vs), "respondidas": 0, "bypass": 0, "pendentes": 0, "aguardando": 0,
         "base": sum(1 for p in vs if p.get("origem", "base") == "base"),
         "escopo": sum(1 for p in vs if p.get("origem") == "escopo")}
    for p in vs:
        k = estado_p(p)
        c[{"respondida": "respondidas", "bypass": "bypass", "aguardando": "aguardando"}.get(k, "pendentes")] += 1
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
            elif k == "aguardando":
                rc = p.get("resposta_cliente")
                if rc:
                    dec = "RESPOSTA DO CLIENTE (a traduzir): " + " ".join(x for x in [rc.get("opcao", ""), rc.get("texto", "")] if x)
                else:
                    dec = "AGUARDANDO CLIENTE: " + (p["cliente"].get("texto") or p["q"])
                origem = "cliente"
            else:
                dec, origem = "—", "pendente"
            cel = lambda t: re.sub(r"\s+", " ", str(t)).replace("|", "/")  # noqa: E731
            linhas.append(f"| {p['id']} | {cel(p['q'])} | {cel(dec)} | {origem} |")
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
                txt = _uma_linha(" ".join(x for x in [r.get("opcao", ""), r.get("texto", "")] if x))
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
            "motivo": p.get("motivo", ""), "dica": p.get("dica", ""), "neg": p.get("neg"), "cliente": p.get("cliente"),
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
    d = {"projeto": S.titulo_projeto(md), "fase": fase, "fase_num": idx, "fases_total": len(S.FASES),
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
        print(f"Varredura de lacunas: {S.ficha(md).get('varredura_lacunas', 'não')}")
        if d["proximas"]:
            print("Próximas perguntas: " + ", ".join(d["proximas"]))
        if d["bypass"]:
            print("Puladas (bypass): " + ", ".join(d["bypass"]))
    print(f"Features: {d['features'] or 'nenhuma'}")
    print(f"Tasks: {d['tasks']}")
    if crs:
        print("Change requests em aberto: " + ", ".join(d["crs_abertas"]))
    print(f"Entrevista pelo celular: {d['entrevista_web']}")
    print(f"Tasks em paralelo: {d['tasks_paralelas']}")


def cmd_next(a, raiz):
    _, e = carregar(raiz)
    vs = visiveis(e)
    pend = [(i + 1, p) for i, p in enumerate(vs) if estado_p(p) == "pendente"]
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
        print(f"  (por quê: {q['why']})")
        if q.get("dica"):
            print(f"  (no briefing: {q['dica']})")
        for o in q["opcoes"]:
            print(f"   {o['n']}. {o['rotulo']}{' (recomendada)' if o['recomendada'] else ''}")
        print("   L. Resposta livre   P. Pular (bypass)")


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


def cmd_cliente(a, raiz):
    _, e = carregar(raiz)
    p = next((x for x in e["perguntas"] if x["id"] == a.id), None)
    if not p:
        die(f"pergunta {a.id} não existe")
    if a.remover:
        p.pop("cliente", None)
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
        salvar_entrev(raiz, e)
        print(f"{a.id}: sugestão para o cliente registrada (você decide se direciona).")
        return
    if p.get("resposta"):
        die("pergunta já respondida: não dá para direcionar")
    p["cliente"] = {"ativa": True, "texto": texto, "opcoes": opcoes, "em": S.agora()}
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{a.id}: direcionada ao dono do negócio → \"{texto}\"")


def _cliente_ativas(e):
    """Perguntas direcionadas ao cliente que ainda não receberam resposta dele (vão para o formulário)."""
    return [p for p in visiveis(e) if (p.get("cliente") or {}).get("ativa") and not p.get("resposta")
            and not p.get("respostas_cliente")]


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
    canon = json.dumps([[i["id"], i["pergunta"], [[r["em"], r.get("opcao", ""), r.get("texto", "")] for r in i["respostas"]]]
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
    for i, p in enumerate(novas, 1):
        c = p["cliente"]
        ops = "".join(f'<label class="opt"><input type="radio" name="q_{esc(p["id"])}" value="{esc(o)}"><span>{esc(o)}</span></label>'
                      for o in c.get("opcoes", []))
        rotulo = "Se preferir, explique com suas palavras" if ops else "Sua resposta"
        cards.append(f'<section class="card"><div class="n">Pergunta {i} de {len(novas)}</div><p class="q">{esc(c["texto"])}</p>{ops}'
                     f'<label class="t" for="t_{esc(p["id"])}">{rotulo}</label>'
                     f'<textarea id="t_{esc(p["id"])}" name="t_{esc(p["id"])}"></textarea></section>')
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
                texto = " ".join(x for x in [r.get("opcao", ""), r.get("texto", "")] if x)
                registro_html += (f'<p class="a"><span class="meta">🔒 {rot} · {esc(_fmt(r["em"]))}{quem}</span><br>{esc(texto)}</p>')
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
              .replace("__FORM_HIDDEN__", "" if novas else " hidden"))
    pasta = os.path.join(raiz, ".spec", "cliente")
    os.makedirs(pasta, exist_ok=True)
    S.gravar(os.path.join(pasta, "index.html"), pagina)
    S.gravar(os.path.join(pasta, "obrigado.html"), S.ler(os.path.join(SKILL, "templates", "obrigado.html")))
    sync_decisoes(raiz)
    print(pasta)
    print(f"{len(novas)} perguntas novas · {len(reg)} respostas registradas (travadas) na página do cliente.")


def cmd_import_cliente(a, raiz):
    """Importa envios do formulário (JSON de `netlify.py submissions`). Só acrescenta: nunca altera o que já foi registrado."""
    md, e = carregar(raiz)
    envios = json.load(open(a.arquivo, encoding="utf-8"))
    n = 0
    for env in sorted(envios, key=lambda x: x["em"]):
        dados = env.get("data", {})
        for p in e["perguntas"]:
            opcao = (dados.get("q_" + p["id"]) or "").strip()
            texto = (dados.get("t_" + p["id"]) or "").strip()
            if not (opcao or texto):
                continue
            lista = p.setdefault("respostas_cliente", [])
            if any(x.get("submissao") == env.get("id") for x in lista):
                continue
            c = p.get("cliente") or {}
            lista.append({"pergunta": c.get("texto") or p["q"], "opcoes": c.get("opcoes", []), "opcao": opcao, "texto": texto,
                          "em": env["em"], "submissao": env.get("id", ""),
                          "respondente": (dados.get("respondente") or "").strip()})
            lista.sort(key=lambda x: x["em"])
            p["resposta_cliente"] = lista[-1]
            p.setdefault("rodada_cliente", _rodada_de(e, p["id"]) or 1)
            n += 1
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    pend = [p["id"] for p in e["perguntas"] if p.get("respostas_cliente") and not p.get("resposta")]
    print(f"{n} respostas do cliente registradas. A traduzir para decisão técnica: {', '.join(pend) or 'nenhuma'}")


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
    p = {"id": qid, "bloco": a.bloco, "q": a.q, "why": a.why or "", "o": [[x] for x in a.opt or []],
         "origem": "escopo"}
    if a.motivo:
        p["motivo"] = a.motivo
    if a.multi:
        p["multi"] = True
    if not p["o"]:
        die("informe ao menos uma --opt (a primeira é a recomendada)")
    e["perguntas"].append(p)
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    print(f"{qid} adicionada ao bloco {a.bloco}.")


def cmd_export_web(a, raiz):
    """Gera .spec/entrevista.html: a página da entrevista (para publicar como artifact e responder no celular)."""
    md, e = carregar(raiz)
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


def cmd_import(a, raiz):
    md, e = carregar(raiz)
    bruto = json.load(open(a.arquivo, encoding="utf-8"))
    if isinstance(bruto, dict) and "answers" in bruto:
        bruto = bruto["answers"]
    itens = bruto.items() if isinstance(bruto, dict) else [(x.get("id"), x.get("data", x)) for x in bruto]
    novas = antigas = 0
    for qid, d in itens:
        p = next((x for x in e["perguntas"] if x["id"] == qid), None)
        if not p or not isinstance(d, dict):
            continue
        atual = p.get("resposta")
        tipo = d.get("tipo")
        if tipo == "cliente":
            antigo = p.get("cliente") or {}
            if atual or antigo.get("em", "") >= d.get("em", ""):
                antigas += 1
                continue
            if d.get("ativa") is False:
                p.pop("cliente", None)
                novas += 1
                continue
            p["cliente"] = {"ativa": True, "texto": d.get("texto", ""), "opcoes": [x for x in d.get("opcoes", []) if x],
                            "em": d.get("em", S.agora())}
            novas += 1
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
        p["resposta"] = r
        novas += 1
    salvar_entrev(raiz, e)
    sync_decisoes(raiz)
    c = contagem(carregar(raiz)[1])
    print(f"{novas} respostas importadas ({antigas} já estavam atualizadas). Restam {c['pendentes']} pendentes.")


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


def erros_de_gate(raiz, atual, destino):
    md, e = carregar(raiz)
    erros = []
    feats = [f for f in S.features(md) if f["estado"] != "descartada"]
    if atual == "entrada" and destino == "entrevista":
        if S.vazio(S.corpo(md, 1)):
            erros.append("Seção 1 (Objetivo) ainda está vazia: registre o briefing ou a ideia antes de entrevistar.")
    elif atual == "entrevista" and destino == "spec":
        c = contagem(e) if e else {"pendentes": 0, "aguardando": 0}
        c = dict(c, pendentes=c["pendentes"] + c.get("aguardando", 0))
        if S.ficha(md).get("varredura_lacunas", "não") != "feita":
            erros.append("Falta a varredura de lacunas: releia briefing e respostas, adicione as perguntas que o escopo "
                         "pede (`add`) e registre com `varredura`.")
        if c["pendentes"]:
            ids = [p["id"] for p in visiveis(e) if estado_p(p) in ("pendente", "aguardando")]
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
    elif atual == "construcao" and destino == "deploy":
        for f in feats:
            if f["estado"] not in ("em-teste", "entregue"):
                erros.append(f"{f['id']}: está '{f['estado']}' (precisa estar em-teste ou entregue).")
            for t in f["tasks"]:
                if t["estado"] != "feita":
                    erros.append(f"{t['id']}: task {t['estado']}.")
    elif atual == "deploy" and destino == "manutencao":
        for f in feats:
            if f["estado"] != "entregue":
                erros.append(f"{f['id']}: está '{f['estado']}' (precisa estar entregue).")
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
               and estado_f.get(t["feature"]) in ("aprovada", "em-andamento")
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
        if s["num"] == 7:
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
    md = S.add_historico(md, f"{a.id} → {a.estado}")
    S.gravar(caminhos(raiz)["spec"], md)
    print(f"{a.id}: {a.estado}")


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
    p.add_argument("--remover", action="store_true")
    p.set_defaults(f=cmd_cliente)
    p = sp.add_parser("export-cliente", help="gera .spec/cliente/ (página do dono do negócio, para o Netlify)")
    p.add_argument("--intro", help="texto de abertura da página")
    p.set_defaults(f=cmd_export_cliente)
    p = sp.add_parser("import-cliente", help="importa os envios do formulário do cliente")
    p.add_argument("arquivo")
    p.set_defaults(f=cmd_import_cliente)
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
    p.add_argument("--motivo", help="o que no briefing ou numa resposta anterior gerou esta pergunta (ex.: 'briefing: marketplace')")
    p.set_defaults(f=cmd_add)

    p = sp.add_parser("varredura", help="registra que a varredura de lacunas foi feita")
    p.set_defaults(f=cmd_varredura)
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
    p = sp.add_parser("hist", help="registra uma linha no histórico")
    p.add_argument("texto")
    p.set_defaults(f=cmd_hist)
    p = sp.add_parser("new-id", help="próximo id livre (F, T ou CR)")
    p.add_argument("prefixo", choices=["F", "T", "CR", "E"])
    p.set_defaults(f=cmd_new_id)
    p = sp.add_parser("cr-new", help="abre um change request")
    p.add_argument("titulo")
    p.add_argument("--features")
    p.add_argument("--motivo")
    p.set_defaults(f=cmd_cr_new)
    p = sp.add_parser("cr-set", help="muda o estado de um change request")
    p.add_argument("id")
    p.add_argument("estado", choices=["aberta", "aprovada", "entregue", "descartada"])
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
