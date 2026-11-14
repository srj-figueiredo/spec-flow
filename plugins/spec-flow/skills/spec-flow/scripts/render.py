"""render: gera docs/spec.html (documento legível) e docs/painel.html (controle visual). Somente biblioteca padrão."""
import html
import json
import os

import specmd as S

esc = html.escape

CSS = """
:root{color-scheme:light dark;--bg:#f6f5f2;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#7b7a75;--line:#e3e2dd;
--track:#e8e7e3;--blue:#2a78d6;--blue-soft:#cde2fb;--good:#0ca30c;--warn:#fab219;--serious:#ec835a;--crit:#d03b3b;--code:#f0efec}
@media (prefers-color-scheme:dark){:root{--bg:#121211;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#97968f;--line:#2e2e2b;
--track:#383835;--blue:#3987e5;--blue-soft:#184f95;--code:#262624}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--blue)}code{background:var(--code);padding:.1em .35em;border-radius:4px;font-size:.9em}
.wrap{max-width:1120px;margin:0 auto;padding:20px 16px 64px}
header.top{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:baseline;justify-content:space-between;margin-bottom:18px}
header.top h1{margin:0;font-size:1.6rem;letter-spacing:-.01em}
.meta{color:var(--ink2);font-size:.9rem}
.nav a{margin-right:14px;font-size:.92rem;text-decoration:none}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:16px}
.card h2{margin:0 0 12px;font-size:1.05rem}
.sub{color:var(--muted);font-size:.85rem}
.grid{display:grid;gap:14px}.g4{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.kpi .n{font-size:1.8rem;font-weight:700;letter-spacing:-.02em;line-height:1.1}.kpi .l{color:var(--ink2);font-size:.88rem}.kpi .s{color:var(--muted);font-size:.8rem;margin-top:2px}
.bar{display:flex;gap:2px;height:10px;background:var(--track);border-radius:999px;overflow:hidden;margin:8px 0 2px}
.bar .seg{display:block;height:100%}.seg.ok{background:var(--blue)}.seg.byp{background:var(--warn)}.seg.done{background:var(--good)}.seg.run{background:var(--blue)}
.row{display:grid;grid-template-columns:150px 1fr 130px;gap:10px;align-items:center;margin:8px 0;font-size:.9rem}
.row .v{text-align:right;color:var(--ink2);font-variant-numeric:tabular-nums}
@media(max-width:520px){.row{grid-template-columns:1fr 110px}.row .bar{grid-column:1/-1;order:3}}
ol.fases{list-style:none;display:flex;gap:6px;padding:0;margin:0;overflow-x:auto;scrollbar-width:thin}
ol.fases li{flex:1 0 96px;text-align:center;font-size:.82rem;color:var(--muted);padding:8px 4px;border-radius:10px;border:1px solid var(--line);background:var(--surface)}
ol.fases li b{display:block;font-size:1rem}
ol.fases li.feita{color:var(--ink2)}ol.fases li.feita b{color:var(--blue)}
ol.fases li.atual{border:2px solid var(--blue);color:var(--ink);font-weight:600}
.chip{display:inline-flex;align-items:center;gap:4px;padding:1px 9px;border-radius:999px;font-size:.78rem;border:1px solid var(--line);color:var(--ink2);white-space:nowrap}
.chip.e-aprovada{border-color:var(--blue);color:var(--blue)}.chip.e-em-andamento{background:var(--blue);border-color:var(--blue);color:#fff}
.chip.e-em-teste{border-color:var(--warn);color:var(--ink)}.chip.e-entregue{background:var(--good);border-color:var(--good);color:#fff}
.chip.e-alterada{border-color:var(--serious);color:var(--ink)}.chip.e-descartada{text-decoration:line-through;color:var(--muted)}
.kan{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}
.col h3{margin:0 0 8px;font-size:.85rem;color:var(--ink2);display:flex;gap:8px;align-items:center}
.fc{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-bottom:8px;font-size:.9rem}
.fc .id{color:var(--muted);font-size:.78rem}.fc .t{font-weight:600;margin:2px 0 6px}
table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--ink2);font-weight:600;font-size:.8rem}.tabela{overflow-x:auto}
details{border-top:1px solid var(--line);padding:8px 0}details summary{cursor:pointer;font-weight:600;font-size:.92rem}
.t-feita .g{color:var(--good)}.t-andamento .g{color:var(--blue)}.t-bloqueada .g{color:var(--crit)}.t-pendente .g{color:var(--muted)}
.pend{list-style:none;padding:0;margin:0}.pend li{padding:8px 0;border-bottom:1px solid var(--line);display:flex;gap:10px;font-size:.92rem}
.pend .ic{width:1.4em;text-align:center}.pend .w{color:var(--warn)}.pend .c{color:var(--crit)}
.vazio{color:var(--muted);font-size:.9rem}
.hist li{list-style:none;padding:5px 0;font-size:.88rem;color:var(--ink2)}.hist{padding:0;margin:0}.hist time{color:var(--muted);margin-right:8px;font-variant-numeric:tabular-nums}
footer{color:var(--muted);font-size:.8rem;margin-top:22px;text-align:center}
/* documento */
.doc{display:grid;grid-template-columns:230px 1fr;gap:28px}
@media(max-width:860px){.doc{grid-template-columns:1fr}.toc{position:static!important;max-height:none!important}}
.toc{position:sticky;top:16px;align-self:start;max-height:92vh;overflow:auto;font-size:.88rem}
.toc a{display:block;padding:3px 0;color:var(--ink2);text-decoration:none}.toc a.l3{padding-left:14px;color:var(--muted)}
.body h1{font-size:1.9rem;margin-top:0}.body h2{margin-top:2.2em;padding-bottom:.3em;border-bottom:1px solid var(--line)}
.body h3{margin-top:1.6em}.body ul{padding-left:1.2em}.body li{margin:.15em 0}
.body li .k{display:inline-block;min-width:4.5em;color:var(--muted);font-size:.82rem;text-transform:uppercase;letter-spacing:.03em}
.body li.task{list-style:none;margin-left:-1.1em}.body blockquote{border-left:3px solid var(--blue);margin:1em 0;padding:.2em 1em;color:var(--ink2);background:var(--surface);border-radius:0 8px 8px 0}
.body pre{background:var(--code);padding:12px;border-radius:8px;overflow:auto}
.body .tabela{background:var(--surface);border:1px solid var(--line);border-radius:10px;margin:1em 0}
@media print{body{background:#fff}.toc,.nav{display:none}.doc{display:block}}
"""

ICON_ESTADO = {"proposta": "○", "aprovada": "✓", "em-andamento": "▶", "em-teste": "⚑", "entregue": "●",
               "alterada": "↻", "descartada": "✕"}
ICON_TASK = {"pendente": "○", "andamento": "▶", "feita": "✓", "bloqueada": "■"}
NOME_TASK = {"pendente": "Pendente", "andamento": "Em andamento", "feita": "Feita", "bloqueada": "Bloqueada"}


def chip(estado):
    return f'<span class="chip e-{estado}">{ICON_ESTADO.get(estado, "")} {esc(S.ESTADO_NOME.get(estado, estado))}</span>'


def pct(a, b):
    return 0 if not b else round(100 * a / b)


def barra(segs):
    """segs: lista de (classe, valor) já em % da largura total."""
    h = '<div class="bar" role="img">'
    for cls, w in segs:
        if w > 0:
            h += f'<span class="seg {cls}" style="width:{w}%"></span>'
    return h + "</div>"


def pagina(titulo, corpo, extra_head=""):
    return (f'<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(titulo)}</title>'
            f"<style>{CSS}</style>{extra_head}</head><body><div class=\"wrap\">{corpo}</div></body></html>")


def carregar(raiz):
    md = S.ler(os.path.join(raiz, "SPEC.md"))
    caminho = os.path.join(raiz, ".spec", "interview.json")
    e = json.load(open(caminho, encoding="utf-8")) if os.path.isfile(caminho) else None
    return md, e


def _visiveis(e):
    import spec as C  # noqa: WPS433
    return C.visiveis(e), C


def render_spec(raiz, md):
    corpo, toc = S.md_para_html(md)
    nome = S.titulo_projeto(md)
    f = S.ficha(md)
    fase = S.FASES_NOME.get(f.get("fase", ""), f.get("fase", ""))
    nav = "".join(f'<a class="l{n}" href="#{sid}">{esc(t)}</a>' for n, t, sid in toc)
    cab = (f'<header class="top"><div><h1>{esc(nome)}</h1><div class="meta">Fase: {esc(fase)} · atualizado em {S.hoje()}</div></div>'
           f'<div class="nav"><a href="painel.html">Painel do projeto →</a></div></header>')
    return pagina(f"{nome} — Spec", cab + f'<div class="doc"><nav class="toc">{nav}</nav><main class="body">{corpo}</main></div>'
                  f'<footer>Gerado a partir do SPEC.md pela spec-flow. Não edite este arquivo: edite o SPEC.md.</footer>')


def render_painel(raiz, md, e):
    nome = S.titulo_projeto(md)
    f = S.ficha(md)
    fase = f.get("fase", "entrada")
    feats = S.features(md)
    tasks = [t for x in feats for t in x["tasks"]]
    ents = S.entregas(md)
    crs = S.change_requests(md)
    hist = S.historico(md)
    ativas = [x for x in feats if x["estado"] != "descartada"]
    entregues = sum(1 for x in ativas if x["estado"] == "entregue")
    feitas = sum(1 for t in tasks if t["estado"] == "feita")

    ent = None
    if e:
        vs, C = _visiveis(e)
        c = C.contagem(e)
        ent = (vs, C, c)

    # fases
    idx = S.FASES.index(fase) if fase in S.FASES else 0
    passos = ""
    for i, k in enumerate(S.FASES):
        cls = "feita" if i < idx else "atual" if i == idx else ""
        marca = "✓" if i < idx else str(i + 1)
        passos += f'<li class="{cls}"><b>{marca}</b>{esc(S.FASES_NOME[k])}</li>'
    h = (f'<header class="top"><div><h1>{esc(nome)}</h1><div class="meta">Painel · {esc(f.get("tipo", ""))} · '
         f'profundidade {esc(f.get("profundidade", ""))} · tasks em paralelo: {esc(f.get("tasks_paralelas", "não"))}</div></div>'
         f'<div class="nav"><a href="spec.html">Ler a spec completa →</a></div></header>')
    h += f'<div class="card"><h2>Fase do projeto</h2><ol class="fases">{passos}</ol></div>'

    # pendências (calculadas antes para o KPI)
    pend = []
    bypass_q = []
    if ent:
        bypass_q = [p for p in ent[0] if ent[1].estado_p(p) == "bypass"]
        if bypass_q:
            pend.append(("⚠", "w", f"{len(bypass_q)} pergunta(s) da entrevista puladas (bypass): decidir antes de construir"))
    for t in tasks:
        if t["estado"] == "bloqueada":
            pend.append(("■", "c", f"Task bloqueada · {t['id']} · {t['titulo']}"))
    for x in feats:
        if x["estado"] == "em-teste":
            pend.append(("⚑", "w", f"Aguardando seu aceite · {x['id']} · {x['titulo']}"))
        if x["estado"] == "proposta" and idx >= S.FASES.index("features"):
            pend.append(("○", "w", f"Aguardando sua aprovação · {x['id']} · {x['titulo']}"))
    for cr in crs:
        if cr["estado"] in ("aberta", "aprovada"):
            pend.append(("↻", "w", f"Change request {cr['estado']} · {cr['id']} · {cr['titulo']}"))

    # KPIs
    kp = ""
    if ent:
        c = ent[2]
        kp += (f'<div class="card kpi"><div class="l">Entrevista respondida</div><div class="n">{pct(c["respondidas"], c["total"])}%</div>'
               f'<div class="s">{c["respondidas"]} respondidas · {c["bypass"]} puladas · {c["pendentes"]} pendentes</div></div>')
    kp += (f'<div class="card kpi"><div class="l">Features entregues</div><div class="n">{entregues}/{len(ativas)}</div>'
           f'<div class="s">{pct(entregues, len(ativas))}% do escopo ativo</div></div>')
    kp += (f'<div class="card kpi"><div class="l">Tasks feitas</div><div class="n">{feitas}/{len(tasks)}</div>'
           f'<div class="s">{pct(feitas, len(tasks))}% concluído</div></div>')
    kp += (f'<div class="card kpi"><div class="l">Pendências</div><div class="n">{len(pend)}</div>'
           f'<div class="s">{"nada travando" if not pend else "veja a lista abaixo"}</div></div>')
    h += f'<div class="grid g4">{kp}</div>'

    # entrevista
    if ent:
        vs, C, c = ent
        h += '<div class="card"><h2>Entrevista de requisitos</h2>'
        h += (f'<div class="sub">{c["total"]} perguntas até agora ({c["base"]} da base + {c["escopo"]} do escopo) · '
              f'varredura de lacunas: {esc(f.get("varredura_lacunas", "não"))}. Novas perguntas podem surgir conforme o escopo se define.</div>')
        h += barra([("ok", pct(c["respondidas"], c["total"])), ("byp", pct(c["bypass"], c["total"]))])
        blocos = []
        for p in vs:
            if p["bloco"] not in blocos:
                blocos.append(p["bloco"])
        for b in blocos:
            ps = [p for p in vs if p["bloco"] == b]
            r = sum(1 for p in ps if C.estado_p(p) == "respondida")
            y = sum(1 for p in ps if C.estado_p(p) == "bypass")
            h += (f'<div class="row"><span>{esc(C.nome_bloco(e, b))}</span>'
                  f'{barra([("ok", pct(r, len(ps))), ("byp", pct(y, len(ps)))])}<span class="v">{r + y}/{len(ps)}</span></div>')
        h += '<div class="sub">Azul: respondida · amarelo: pulada (bypass, vira pendência)</div></div>'

    # entregas
    if ents:
        h += '<div class="card"><h2>Entregas</h2>'
        for en in ents:
            fs = [x for x in ativas if x["entrega"] == en["id"]]
            ts = [t for x in fs for t in x["tasks"]]
            ok = sum(1 for t in ts if t["estado"] == "feita")
            ent_ok = sum(1 for x in fs if x["estado"] == "entregue")
            h += (f'<div class="row"><span><b>{esc(en["id"])}</b> · {esc(en["nome"])}</span>'
                  f'{barra([("done", pct(ok, len(ts))) if ts else ("done", pct(ent_ok, len(fs)))])}'
                  f'<span class="v">{ent_ok}/{len(fs)} features · {pct(ok, len(ts))}% tasks</span></div>')
            if en["objetivo"]:
                h += f'<div class="sub">{esc(en["objetivo"])}</div>'
        h += "</div>"

    # features
    if feats:
        cols = [k for k in S.ESTADOS_FEATURE if any(x["estado"] == k for x in feats)]
        h += '<div class="card"><h2>Features</h2><div class="kan">'
        for k in cols:
            ds = [x for x in feats if x["estado"] == k]
            h += f'<div class="col"><h3>{chip(k)}<span>{len(ds)}</span></h3>'
            for x in ds:
                tt = len(x["tasks"])
                ok = sum(1 for t in x["tasks"] if t["estado"] == "feita")
                h += (f'<div class="fc"><div class="id">{esc(x["id"])} · {esc(x["entrega"] or "sem entrega")}'
                      f'{" · " + esc(x["origem"]) if x.get("origem") else ""}</div><div class="t">{esc(x["titulo"])}</div>'
                      f'{barra([("done", pct(ok, tt))]) if tt else ""}'
                      f'<div class="sub">{f"{ok}/{tt} tasks" if tt else "sem tasks ainda"}</div></div>')
            h += "</div>"
        h += "</div></div>"

    # tasks
    if tasks:
        cont = {k: sum(1 for t in tasks if t["estado"] == k) for k in ICON_TASK}
        resumo = " · ".join(f"{ICON_TASK[k]} {NOME_TASK[k]}: {v}" for k, v in cont.items())
        h += f'<div class="card"><h2>Tasks</h2><div class="sub">{resumo}</div>'
        for x in feats:
            if not x["tasks"]:
                continue
            aberto = " open" if x["estado"] in ("em-andamento", "aprovada") else ""
            h += f'<details{aberto}><summary>{esc(x["id"])} · {esc(x["titulo"])} {chip(x["estado"])}</summary><div class="tabela"><table>'
            h += "<tr><th>Estado</th><th>Task</th><th>Dono</th><th>Depende de</th><th>Arquivos</th></tr>"
            for t in x["tasks"]:
                h += (f'<tr class="t-{t["estado"]}"><td><span class="g">{ICON_TASK[t["estado"]]}</span> {NOME_TASK[t["estado"]]}</td>'
                      f'<td><b>{esc(t["id"])}</b> {esc(t["titulo"])}</td><td>{esc(t["dono"] or "—")}</td>'
                      f'<td>{esc(", ".join(t["depende"]) or "—")}</td><td><code>{esc(", ".join(t["toca"]) or "—")}</code></td></tr>')
            h += "</table></div></details>"
        h += "</div>"

    # pendências + CRs
    h += '<div class="grid g2"><div class="card"><h2>Pendências</h2>'
    if pend:
        h += '<ul class="pend">' + "".join(f'<li><span class="ic {c_}">{i}</span><span>{esc(t)}</span></li>' for i, c_, t in pend) + "</ul>"
        if bypass_q:
            h += ("<details><summary>Ver perguntas puladas</summary><ul class=\"pend\">" + "".join(
                f'<li><span class="ic w">⚠</span><span><b>{esc(p["id"])}</b> · {esc(p["q"])}'
                f'{" — " + esc(p["resposta"]["texto"]) if p["resposta"].get("texto") else ""}</span></li>' for p in bypass_q) + "</ul></details>")
    else:
        h += '<div class="vazio">✓ Nada pendente.</div>'
    h += '</div><div class="card"><h2>Change requests</h2>'
    if crs:
        h += '<ul class="pend">' + "".join(
            f'<li><span class="ic">↻</span><span><b>{esc(c_["id"])}</b> · {esc(c_["titulo"])} · {esc(c_["estado"])}'
            f'{" · " + esc(", ".join(c_["features"])) if c_["features"] else ""}</span></li>' for c_ in crs) + "</ul>"
    else:
        h += '<div class="vazio">Nenhuma mudança pedida ainda.</div>'
    h += "</div></div>"

    # histórico
    h += '<div class="card"><h2>Últimos registros</h2>'
    if hist:
        h += '<ul class="hist">' + "".join(f'<li><time>{esc(x["data"])}</time>{esc(x["texto"])}</li>' for x in reversed(hist[-12:])) + "</ul>"
    else:
        h += '<div class="vazio">Sem registros.</div>'
    h += "</div>"
    h += f'<footer>Gerado em {S.hoje()} a partir do SPEC.md · spec-flow</footer>'
    return pagina(f"{nome} — Painel", h)


def render_all(raiz):
    md, e = carregar(raiz)
    docs = os.path.join(raiz, "docs")
    os.makedirs(docs, exist_ok=True)
    saidas = []
    for nome, conteudo in (("spec.html", render_spec(raiz, md)), ("painel.html", render_painel(raiz, md, e))):
        caminho = os.path.join(docs, nome)
        S.gravar(caminho, conteudo)
        saidas.append(caminho)
    return saidas
