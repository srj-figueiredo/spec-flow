"""render: gera docs/spec.html (documento legível) e docs/painel.html (controle visual). Somente biblioteca padrão."""
import html
import json
import os

import specmd as S
import cliente_html as CH

esc = html.escape

CSS = """
:root{color-scheme:light dark;--bg:#f6f5f2;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#7b7a75;--line:#e3e2dd;
--track:#e8e7e3;--blue:#2a78d6;--wait:#6250d6;--blue-soft:#cde2fb;--good:#0ca30c;--warn:#fab219;--serious:#ec835a;--crit:#d03b3b;--code:#f0efec}
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
.bar .seg{display:block;height:100%}.seg.ok{background:var(--blue)}.seg.wait{background:#6250d6}.seg.byp{background:var(--warn)}.seg.done{background:var(--good)}.seg.run{background:var(--blue)}
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
.tabs{display:flex;gap:6px;overflow-x:auto;margin:0 0 14px;padding-bottom:2px;scrollbar-width:thin}
.tabs button{flex:0 0 auto;border:1px solid var(--line);background:var(--surface);color:var(--ink2);border-radius:999px;padding:8px 14px;font:inherit;font-size:.9rem;cursor:pointer;min-height:40px}
.tabs button.on{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:600}.tabs .n{opacity:.8;margin-left:4px;font-size:.8rem}
.tab{display:none}.tab.on{display:block}
.chip.ts-passou{background:var(--good);border-color:var(--good);color:#fff}.chip.ts-falhou{background:var(--crit);border-color:var(--crit);color:#fff}
.chip.ts-bloqueado{border-color:var(--crit);color:var(--crit)}.chip.ts-em-execucao{background:var(--blue);border-color:var(--blue);color:#fff}
.chip.ts-n-a{color:var(--muted)}.chip.cok{border-color:var(--blue);color:var(--blue)}.chip.cwt{border-color:#6250d6;color:#6250d6}.chip.cby{border-color:var(--warn);color:var(--ink)}.chip.crv{border-color:var(--serious);color:var(--ink)}
.dec{font-size:.88rem;color:var(--ink2)}
.dl{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;margin:8px 0 0;font-size:.92rem}.dl dt{color:var(--muted)}.dl dd{margin:0;overflow-wrap:anywhere}
.big{font-size:1.15rem;font-weight:650;overflow-wrap:anywhere}.aviso2{background:#fff4d6;border:1px solid var(--warn);border-radius:12px;padding:10px 12px;margin:10px 0;font-size:.92rem}
@media (prefers-color-scheme:dark){.aviso2{background:#3a3016}}
.chip.ck-feito{background:var(--good);border-color:var(--good);color:#fff}.chip.ck-andamento{background:var(--blue);border-color:var(--blue);color:#fff}.chip.ck-bloqueado{background:var(--crit);border-color:var(--crit);color:#fff}.chip.ck-n-a{opacity:.7}
@media(max-width:560px){.dl{grid-template-columns:1fr}.dl dt{margin-top:6px}}.hs{font-size:.8rem;color:var(--muted);margin:4px 0 0}
.grupo{margin:14px 0 4px;font-weight:650;font-size:.95rem}
.fdet{border-top:1px solid var(--line);padding:10px 0}.fdet h3{margin:0 0 4px;font-size:1rem}.fdet ul{margin:4px 0 0;padding-left:20px;font-size:.9rem}
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


ORIGEM_ROT = {"recomendada": "recomendada", "alternativa": "alternativa", "livre": "resposta livre"}


def _tab_entrevista(e, ent):
    vs, C, c = ent
    h = (f'<div class="card"><h2>Decisões da entrevista</h2><div class="sub">{c["total"]} perguntas ({c["base"]} da base + {c["escopo"]} do escopo) · '
         f'{len([p for p in e["perguntas"] if p.get("descartada")])} da base não se aplicam a este projeto.</div>')
    blocos = []
    for p in e["perguntas"]:
        if p["bloco"] not in blocos and (p in vs or p.get("descartada")):
            blocos.append(p["bloco"])
    for b in blocos:
        h += f'<div class="grupo">{esc(C.nome_bloco(e, b))}</div><div class="tabela"><table><tr><th>ID</th><th>Pergunta</th><th>Decisão</th><th>Situação</th></tr>'
        for p in e["perguntas"]:
            if p["bloco"] != b or not (p in vs or p.get("descartada")):
                continue
            if p.get("descartada"):
                dec, sit = f'Não se aplica: {esc(p["descartada"]["motivo"])}', '<span class="chip ts-n-a">não se aplica</span>'
            else:
                k = C.estado_p(p)
                r = p.get("resposta") or {}
                if k == "respondida":
                    dec = esc(C.texto_resposta(p))
                    sit = f'<span class="chip cok">{esc(ORIGEM_ROT.get(r.get("origem", ""), "respondida"))}</span>'
                elif k == "revisar":
                    dec = esc(C.texto_resposta(p)) + f'<div class="hs">↻ Revisar: {esc(p["revisao"].get("motivo", ""))} (origem {esc(p["revisao"].get("origem", "?"))})</div>'
                    sit = '<span class="chip crv">a revisar</span>'
                elif k == "bypass":
                    dec = esc(r.get("texto") or "Pulada (decidir depois)")
                    sit = '<span class="chip cby">bypass</span>'
                elif k == "aguardando":
                    minha = ""
                    if p.get("resposta") and p["resposta"]["tipo"] != "bypass":
                        minha = f'<div class="hs">✓ Sua resposta (provisória): {esc(C.texto_resposta(p))}</div>'
                    dec = "Com o cliente: " + esc((C.cliente_efetivo(p) or {}).get("texto", "")) + minha
                    sit = '<span class="chip cwt">aguardando cliente</span>' + (' <span class="chip cwt">📌 sugerida por mim</span>' if p.get("cliente") is None else "")
                else:
                    dec = "—"
                    sit = '<span class="chip">pendente</span>'
            extra = ""
            for rc in p.get("respostas_cliente") or []:
                extra += f'<div class="hs">🔒 Cliente ({esc(rc["em"][:10])}{" · " + esc(rc["respondente"]) if rc.get("respondente") else ""}): {esc(" · ".join(CH.resumo(rc)))}</div>'
            for hs in p.get("historico") or []:
                extra += f'<div class="hs">Decisão anterior ({esc(hs["substituida_em"][:10])}): {esc(hs.get("texto", ""))}</div>'
            tag = ('<span class="chip">escopo</span> ' if p.get("origem") == "escopo" else "") + (
                '<span class="chip ts-n-a">você dispensou o envio ao cliente</span> ' if p.get("selecao_cliente") == "dispensada" else "")
            h += f'<tr><td>{esc(p["id"])}</td><td>{tag}{esc(p["q"])}</td><td class="dec">{dec}{extra}</td><td>{sit}</td></tr>'
        h += "</table></div>"
    return h + "</div>"


def _tab_features(feats, tab_features):
    if not feats:
        return '<div class="card"><div class="vazio">Ainda não há features. Elas nascem depois da entrevista.</div></div>'
    d = '<div class="card"><h2>Detalhe das features</h2>'
    for x in feats:
        d += (f'<div class="fdet"><h3>{esc(x["id"])} · {esc(x["titulo"])} {chip(x["estado"])}</h3>'
              f'<div class="sub">{esc(x["entrega"] or "sem entrega")}{" · " + esc(x["origem"]) if x.get("origem") else ""} · {esc(x["valor"])}</div>')
        if x["aceite"]:
            d += "<div class='sub' style='margin-top:6px'>Critérios de aceite:</div><ul>" + "".join(f"<li>{esc(a)}</li>" for a in x["aceite"]) + "</ul>"
        if x["tasks"]:
            ok = sum(1 for t in x["tasks"] if t["estado"] == "feita")
            d += f"<div class='sub' style='margin-top:6px'>{ok}/{len(x['tasks'])} tasks feitas</div>"
        d += "</div>"
    return tab_features + d + "</div>"


def _tab_testes(tst, feats):
    if not tst:
        return '<div class="card"><h2>Plano de testes</h2><div class="vazio">Ainda não há plano de testes. Ele nasce junto com as features e é executado no momento que fizer sentido para cada caso.</div></div>'
    cont = {k: sum(1 for t in tst if t["estado"] == k) for k in S.TESTE_ESTADOS}
    resumo = " · ".join(f"{S.TESTE_NOME[k]}: {v}" for k, v in cont.items() if v)
    nomes = {x["id"]: x["titulo"] for x in feats}
    h = f'<div class="card"><h2>Plano de testes</h2><div class="sub">{esc(resumo)}. Cada teste é executado no momento que faz sentido para o caso; os autônomos rodam sozinhos e deixam evidência.</div>'
    for q in S.TESTE_QUANDO:
        grupo = [t for t in tst if t["quando"] == q]
        if not grupo:
            continue
        h += f'<div class="grupo">{esc(S.QUANDO_NOME[q])}</div><div class="tabela"><table><tr><th>Teste</th><th>Feature</th><th>Tipo</th><th>Modo</th><th>Estado</th><th>Evidência</th><th>Por que neste momento</th></tr>'
        for t in grupo:
            modo = "🤖 autônomo" if t["modo"] == "autonomo" else "🧑 manual"
            evp = t["evidencia"]
            if evp.startswith("docs/") and not evp.startswith("docs/../"):
                ev = f'<a href="{esc(evp[5:])}"><code>{esc(evp)}</code></a>'
            elif evp.startswith(("http://", "https://")):
                ev = f'<a href="{esc(evp)}">{esc(evp)}</a>'
            else:
                ev = f"<code>{esc(evp)}</code>" if evp else "—"
            h += (f'<tr><td><b>{esc(t["id"])}</b> {esc(t["titulo"])}<div class="hs">{esc(t["criterio"])}</div></td>'
                  f'<td>{esc(t["feature"] or "—")}<div class="hs">{esc(nomes.get(t["feature"], ""))}</div></td><td>{esc(t["tipo"] or "—")}</td><td>{modo}</td>'
                  f'<td><span class="chip ts-{t["estado"]}">{esc(S.TESTE_NOME.get(t["estado"], t["estado"]))}</span></td><td>{ev}</td><td class="dec">{esc(t["motivo_momento"] or "—")}</td></tr>')
        h += "</table></div>"
    return h + "</div>"


def _n_espera(e):
    if not e:
        return ""
    import spec as C
    n = sum(1 for p in C.visiveis(e) if C.vai_ao_cliente(p) and not p.get("respostas_cliente"))
    return f"{n} aguardando" if n else ""


def _n_deploy(md):
    ck = S.deploy(md)["checklist"]
    return f'{sum(1 for i in ck if i["estado"] == "feito")}/{len(ck)}' if ck else ""


def _tab_historico(md, hist, crs, f):
    h = '<div class="card"><h2>Links e endereços</h2><ul class="pend">'
    achou = False
    for chave, rot in (("cliente_url", "Página do cliente"), ("entrevista_web", "Entrevista completa (celular)")):
        v = f.get(chave, "")
        if v and v != "—":
            achou = True
            h += f'<li><span class="ic">🔗</span><span>{esc(rot)}: ' + (f'<a href="{esc(v)}">{esc(v)}</a>' if v.startswith("http") else esc(v)) + "</span></li>"
    h += "</ul>" if achou else ""
    if not achou:
        h += '<li class="vazio">Nenhum link registrado ainda.</li></ul>'
    h += '</div><div class="card"><h2>Histórico completo</h2>'
    if hist:
        h += '<ul class="hist">' + "".join(f'<li><time>{esc(x["data"])}</time>{esc(x["texto"])}</li>' for x in reversed(hist)) + "</ul>"
    else:
        h += '<div class="vazio">Sem registros.</div>'
    return h + "</div>"


def _link_evidencia(evp):
    if evp.startswith("docs/") and not evp.startswith("docs/../"):
        return f'<a href="{esc(evp[5:])}"><code>{esc(evp)}</code></a>'
    if evp.startswith(("http://", "https://")):
        return f'<a href="{esc(evp)}">{esc(evp)}</a>'
    return f"<code>{esc(evp)}</code>" if evp else "—"


DEPLOY_IDS = ("DP-01", "DP-02", "DP-03", "DP-04", "DP-05", "S-02", "A-03", "A-05", "SG-03", "D-03", "D-05")


def _tab_deploy(md, e, tst, f):
    dp = S.deploy(md)
    info, itens, pubs = dp["info"], dp["checklist"], dp["publicacoes"]
    fase = f.get("fase", "entrada")
    chegou = S.FASES.index(fase) >= S.FASES.index("deploy") if fase in S.FASES else False
    h = '<div class="card"><h2>Onde está no ar</h2>'
    url = info.get("url", "")
    if url and url.startswith("http"):
        h += f'<div class="big"><a href="{esc(url)}">{esc(url)}</a></div>'
    else:
        h += '<div class="vazio">Ainda não publicado em produção.</div>'
    ult = pubs[-1] if pubs else None
    if ult:
        cor = {"ok": "ck-feito", "falhou": "ck-bloqueado", "revertido": "ts-n-a"}[ult["resultado"]]
        h += (f'<p class="sub">Última publicação: {esc(ult["data"])} · {esc(ult["ambiente"])} · <span class="chip {cor}">{esc(ult["resultado"])}</span>'
              f'{" · commit " + esc(ult["commit"]) if ult["commit"] else ""}{" · " + esc(ult["nota"]) if ult["nota"] else ""}</p>')
    rot = (("ambiente", "Ambiente"), ("dominio", "Domínio e DNS"), ("como_publicar", "Como publicar de novo"), ("como_reverter", "Como reverter"), ("monitoramento", "Monitoramento"))
    linhas = [(r, info[k]) for k, r in rot if info.get(k)]
    if linhas:
        h += '<dl class="dl">' + "".join(f"<dt>{esc(r)}</dt><dd>{esc(v)}</dd>" for r, v in linhas) + "</dl>"
    elif not chegou:
        h += '<p class="sub">Estes dados são preenchidos ao entrar na fase de Deploy (`deploy-init`), a partir das decisões da entrevista.</p>'
    h += "</div>"
    # checklist
    h += '<div class="card"><h2>Checklist de deploy</h2>'
    if itens:
        feitos = sum(1 for i in itens if i["estado"] in ("feito", "n-a"))
        h += f'<div class="sub">{feitos} de {len(itens)} itens concluídos</div>{barra([("done" if feitos == len(itens) else "run", pct(feitos, len(itens)))])}'
        h += '<div class="tabela"><table><tr><th>Item</th><th>Estado</th><th>Decisão / nota</th></tr>'
        for i in itens:
            if i["evidencia"]:
                rot_ev = "Não se aplica: " if i["estado"] == "n-a" else "Evidência: "
                ev = f'<div class="hs">{rot_ev}{_link_evidencia(i["evidencia"]) if i["estado"] != "n-a" else esc(i["evidencia"])}</div>'
            else:
                ev = '<div class="hs">sem evidência registrada</div>' if i["estado"] == "feito" else ""
            h += (f'<tr><td><b>{esc(i["id"])}</b> {esc(i["titulo"])}</td><td><span class="chip ck-{i["estado"]}">{esc(i["estado"])}</span></td>'
                  f'<td class="dec">{esc(i["nota"] or "—")}{ev}</td></tr>')
        h += "</table></div>"
    else:
        h += '<div class="vazio">Checklist ainda não criado: ele é montado ao entrar na fase de Deploy.</div>'
    h += "</div>"
    # publicações
    h += '<div class="card"><h2>Publicações</h2>'
    if pubs:
        h += '<div class="tabela"><table><tr><th>Data</th><th>Ambiente</th><th>Resultado</th><th>Endereço</th><th>Commit</th><th>Nota</th></tr>'
        for x in reversed(pubs):
            cor = {"ok": "ck-feito", "falhou": "ck-bloqueado", "revertido": "ts-n-a"}[x["resultado"]]
            link = f'<a href="{esc(x["url"])}">{esc(x["url"])}</a>' if x["url"].startswith("http") else "—"
            h += (f'<tr><td>{esc(x["data"])}</td><td>{esc(x["ambiente"])}</td><td><span class="chip {cor}">{esc(x["resultado"])}</span></td>'
                  f'<td>{link}</td><td><code>{esc(x["commit"] or "—")}</code></td><td class="dec">{esc(x["nota"] or "—")}</td></tr>')
        h += "</table></div>"
    else:
        h += '<div class="vazio">Nenhuma publicação registrada ainda.</div>'
    h += "</div>"
    # testes pós-deploy
    pos = [t for t in tst if t["quando"] == "pos-deploy"]
    h += '<div class="card"><h2>Testes depois do deploy</h2>'
    if pos:
        h += '<div class="tabela"><table><tr><th>Teste</th><th>Modo</th><th>Estado</th><th>Evidência</th></tr>'
        for t in pos:
            h += (f'<tr><td><b>{esc(t["id"])}</b> {esc(t["titulo"])}<div class="hs">{esc(t["criterio"])}</div></td><td>{"🤖 autônomo" if t["modo"] == "autonomo" else "🧑 manual"}</td>'
                  f'<td><span class="chip ts-{t["estado"]}">{esc(S.TESTE_NOME.get(t["estado"], t["estado"]))}</span></td><td>{_link_evidencia(t["evidencia"])}</td></tr>')
        h += "</table></div>"
    else:
        h += '<div class="vazio">Nenhum teste marcado para depois do deploy.</div>'
    h += "</div>"
    # decisões que guiam o deploy
    if e:
        por_id = {p["id"]: p for p in e["perguntas"]}
        import spec as C
        linhas = [(i, por_id[i]) for i in DEPLOY_IDS if i in por_id and not por_id[i].get("descartada")]
        if linhas:
            h += '<div class="card"><h2>Decisões da entrevista que guiam o deploy</h2><div class="tabela"><table><tr><th>ID</th><th>Pergunta</th><th>Decisão</th></tr>'
            for i, p in linhas:
                k = C.estado_p(p)
                dec = esc(C.texto_resposta(p)) if p.get("resposta") and p["resposta"]["tipo"] != "bypass" else f'<span class="mut">{esc(k)}</span>'
                h += f'<tr><td>{esc(i)}</td><td>{esc(p["q"])}</td><td class="dec">{dec}</td></tr>'
            h += "</table></div></div>"
    return h


def _tab_cliente(md, e, f):
    if not e:
        return '<div class="card"><div class="vazio">Sem entrevista.</div></div>'
    import spec as C
    pc = C.estado_pagina_cliente(md, e)
    perguntas = e["perguntas"]
    h = '<div class="card"><h2>Página do cliente</h2>'
    if pc["url"].startswith("http"):
        h += f'<div class="big"><a href="{esc(pc["url"])}">{esc(pc["url"])}</a></div>'
    if not pc["gerada_em"]:
        h += '<p class="sub"><span class="chip">ainda não criada</span> Ela é gerada a partir das perguntas marcadas para o dono do negócio (`export-cliente`).</p>'
    else:
        est = '<span class="chip ck-feito">publicada</span>' if pc["publicada"] else '<span class="chip cby">gerada, ainda não publicada</span>'
        h += f'<p class="sub">{est} · gerada em {esc(pc["gerada_em"][:16].replace("T", " "))}' + (f' · publicada em {esc(pc["publicada_em"][:16].replace("T", " "))}' if pc["publicada_em"] else "") + "</p>"
        if pc["faltam"] or pc["sobram"]:
            h += '<div class="aviso2">⚠ <b>A página está desatualizada.</b> '
            if pc["faltam"]:
                h += f'Marcadas e ainda fora da página: {esc(", ".join(pc["faltam"]))}. '
            if pc["sobram"]:
                h += f'Na página, mas já desmarcadas: {esc(", ".join(pc["sobram"]))}. '
            h += "Peça ao Claude para atualizar a página do cliente (mesmo endereço).</div>"
    h += '<p class="sub">Privada por endereço (sem senha): só quem tem o link acessa. As respostas dele ficam travadas depois de enviadas.</p></div>'
    # aguardando
    espera = [p for p in visiveis_(e, C) if C.vai_ao_cliente(p) and not p.get("respostas_cliente")]
    h += f'<div class="card"><h2>Aguardando o dono do negócio ({len(espera)})</h2>'
    if espera:
        h += '<div class="tabela"><table><tr><th>ID</th><th>Pergunta que ele vê</th><th>Origem</th><th>Sua resposta provisória</th></tr>'
        for p in espera:
            c = C.cliente_efetivo(p)
            origem = '<span class="chip cwt">📌 sugerida por mim</span>' if p.get("cliente") is None else '<span class="chip">escolhida por você</span>'
            minha = esc(C.texto_resposta(p)) if p.get("resposta") and p["resposta"]["tipo"] != "bypass" else "—"
            h += f'<tr><td>{esc(p["id"])}</td><td>{esc(c.get("texto", ""))}</td><td>{origem}</td><td class="dec">{minha}</td></tr>'
        h += "</table></div>"
    else:
        h += '<div class="vazio">Nenhuma pergunta aguardando o cliente.</div>'
    h += "</div>"
    # respostas recebidas
    reg = C._registro(e)
    h += f'<div class="card"><h2>Respostas recebidas ({len(reg)})</h2>'
    if reg:
        por_id = {p["id"]: p for p in perguntas}
        rod = None
        for it in reg:
            if it["rodada"] != rod:
                rod = it["rodada"]
                h += f'<div class="grupo">Rodada {rod}</div>'
            p = por_id[it["id"]]
            traduzida = bool(p.get("resposta"))
            ver = all(r.get("verificada") for r in it["respostas"])
            chips = ('<span class="chip ck-feito">traduzida</span>' if traduzida else '<span class="chip cby">a traduzir</span>') + \
                    (' <span class="chip ck-feito">impacto verificado</span>' if ver else ' <span class="chip cby">impacto a verificar</span>')
            h += f'<div class="fdet"><h3>{esc(it["id"])} · {esc(it["pergunta"])}</h3><div class="sub">{chips}</div>'
            for k, r in enumerate(it["respostas"]):
                quem = f" · {esc(r['respondente'])}" if r.get("respondente") else ""
                h += f'<div class="hs">🔒 {"Resposta" if k == 0 else "Complemento"} · {esc(r["em"][:10])}{quem}</div><div class="dec">{"<br>".join(esc(x) for x in CH.resumo(r))}</div>'
            if traduzida:
                h += f'<div class="hs">Sua decisão: {esc(C.texto_resposta(p))}</div>'
            h += "</div>"
        h += f'<p class="cod">Código do registro: <code>{C._codigo_registro(reg)}</code></p>'
    else:
        h += '<div class="vazio">O cliente ainda não respondeu.</div>'
    h += "</div>"
    disp = [p for p in perguntas if p.get("selecao_cliente") == "dispensada" and not C.vai_ao_cliente(p)]
    if disp:
        h += f'<div class="card"><h2>Dispensadas por você ({len(disp)})</h2><p class="sub">Sugestões do Claude que você tirou da lista do cliente. Ele não as remarca.</p><div class="dec">{esc(", ".join(p["id"] for p in disp))}</div></div>'
    return h


def visiveis_(e, C):
    return C.visiveis(e)


def _abas(md, e, ent, feats, tasks, tst, hist, crs, f, visao, tab_features, tab_tasks):
    corpos = [("visao", "Visão geral", "", visao),
              ("entrevista", "Entrevista", f'{ent[2]["respondidas"]}/{ent[2]["total"]}' if ent else "", _tab_entrevista(e, ent) if ent else '<div class="card"><div class="vazio">Sem entrevista.</div></div>'),
              ("cliente", "Cliente", _n_espera(e), _tab_cliente(md, e, f)),
              ("features", "Features", str(len(feats)) if feats else "", _tab_features(feats, tab_features)),
              ("tasks", "Tasks", f'{sum(1 for t in tasks if t["estado"] == "feita")}/{len(tasks)}' if tasks else "",
               tab_tasks or '<div class="card"><div class="vazio">Ainda não há tasks.</div></div>'),
              ("testes", "Testes", f'{sum(1 for t in tst if t["estado"] == "passou")}/{sum(1 for t in tst if t["estado"] != "n-a")}' if tst else "", _tab_testes(tst, feats)),
              ("deploy", "Deploy", _n_deploy(md), _tab_deploy(md, e, tst, f)),
              ("historico", "Histórico", "", _tab_historico(md, hist, crs, f))]
    nav = '<nav class="tabs" role="tablist">' + "".join(
        f'<button type="button" data-t="{k}"{" class=on" if i == 0 else ""}>{esc(r)}' + (f'<span class="n">{esc(n)}</span>' if n else "") + "</button>"
        for i, (k, r, n, _) in enumerate(corpos)) + "</nav>"
    pain = "".join(f'<section class="tab{" on" if i == 0 else ""}" id="t-{k}">{c}</section>' for i, (k, _, _, c) in enumerate(corpos))
    js = ("<script>(function(){var b=document.querySelectorAll('.tabs button'),t=document.querySelectorAll('.tab');"
          "function go(k){b.forEach(function(x){x.classList.toggle('on',x.dataset.t===k)});t.forEach(function(x){x.classList.toggle('on',x.id==='t-'+k)});"
          "if(history.replaceState)history.replaceState(null,'','#'+k);}"
          "b.forEach(function(x){x.addEventListener('click',function(){go(x.dataset.t)})});"
          "var h=location.hash.slice(1);if(h&&document.getElementById('t-'+h))go(h);"
          "var at=document.querySelector('ol.fases li.atual');if(at&&at.scrollIntoView)at.scrollIntoView({inline:'center',block:'nearest'});})();</script>"
          "<noscript><style>.tab{display:block!important}.tabs{display:none}</style></noscript>")
    return nav + pain + js


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
    marks = []

    # pendências (calculadas antes para o KPI)
    pend = []
    bypass_q = []
    if ent:
        bypass_q = [p for p in ent[0] if ent[1].estado_p(p) == "bypass"]
        if bypass_q:
            pend.append(("⚠", "w", f"{len(bypass_q)} pergunta(s) da entrevista puladas (bypass): decidir antes de construir"))
        espera = [p for p in ent[0] if ent[1].estado_p(p) == "aguardando"]
        trad = [p["id"] for p in espera if p.get("resposta_cliente")]
        sem = [p["id"] for p in espera if not p.get("resposta_cliente")]
        if sem:
            pend.append(("⏳", "w", f"Aguardando o dono do negócio: {len(sem)} pergunta(s) ({', '.join(sem[:8])}{'...' if len(sem) > 8 else ''})"))
        rev = [p["id"] for p in ent[0] if ent[1].estado_p(p) == "revisar"]
        if rev:
            pend.append(("↻", "c", f"Decisões a REVISAR (afetadas por resposta do cliente): {', '.join(rev)}"))
        nao_ver = ent[1]._nao_verificadas(e)
        if nao_ver:
            pend.append(("🔍", "w", f"{len(nao_ver)} resposta(s) do cliente sem verificação de impacto"))
        if trad:
            pend.append(("✎", "w", f"Cliente respondeu, falta traduzir para decisão técnica: {', '.join(trad)}"))
    for t in tasks:
        if t["estado"] == "bloqueada":
            pend.append(("■", "c", f"Task bloqueada · {t['id']} · {t['titulo']}"))
    tst = S.testes(md)
    for t in tst:
        if t["estado"] == "falhou":
            pend.append(("✗", "c", f"Teste FALHOU · {t['id']} · {t['titulo']}"))
        elif t["estado"] == "bloqueado":
            pend.append(("■", "c", f"Teste bloqueado · {t['id']} · {t['titulo']}"))
        elif t["modo"] == "manual" and t["estado"] in ("pendente", "em-execucao") and idx >= S.FASES.index("testes"):
            pend.append(("🧑", "w", f"Teste manual aguardando você · {t['id']} · {t['titulo']}"))
    dpl = S.deploy(md)
    if idx >= S.FASES.index("deploy"):
        abertos = [i for i in dpl["checklist"] if i["estado"] != "feito"]
        for i in abertos:
            if i["estado"] == "bloqueado":
                pend.append(("■", "c", f"Deploy bloqueado · {i['id']} · {i['titulo']}"))
        if dpl["checklist"] and abertos:
            pend.append(("☐", "w", f"Checklist de deploy: {len(abertos)} de {len(dpl['checklist'])} itens abertos"))
        if not dpl["checklist"]:
            pend.append(("☐", "w", "Checklist de deploy ainda não criado (deploy-init)"))
    if e:
        import spec as C2
        pc = C2.estado_pagina_cliente(md, e)
        if pc["gerada_em"] and pc["desatualizada"]:
            pend.append(("⟳", "w", "A página do cliente está desatualizada: peça para atualizar (mesmo endereço)"))
        elif pc["a_publicar"]:
            pend.append(("⟳", "w", "A página do cliente foi gerada, mas ainda não está publicada: o cliente não consegue ver"))
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
               f'<div class="s">{c["respondidas"]} respondidas · {c["bypass"]} puladas · {c["aguardando"]} com o cliente · {c["pendentes"]} pendentes</div></div>')
    kp += (f'<div class="card kpi"><div class="l">Features entregues</div><div class="n">{entregues}/{len(ativas)}</div>'
           f'<div class="s">{pct(entregues, len(ativas))}% do escopo ativo</div></div>')
    kp += (f'<div class="card kpi"><div class="l">Tasks feitas</div><div class="n">{feitas}/{len(tasks)}</div>'
           f'<div class="s">{pct(feitas, len(tasks))}% concluído</div></div>')
    if tst:
        tp = sum(1 for t in tst if t["estado"] == "passou")
        tv = sum(1 for t in tst if t["estado"] != "n-a")
        kp += (f'<div class="card kpi"><div class="l">Testes que passaram</div><div class="n">{tp}/{tv}</div>'
               f'<div class="s">{sum(1 for t in tst if t["estado"] == "falhou")} falharam</div></div>')
    kp += (f'<div class="card kpi"><div class="l">Pendências</div><div class="n">{len(pend)}</div>'
           f'<div class="s">{"nada travando" if not pend else "veja a lista abaixo"}</div></div>')
    marks.append(("kpi", len(h)))
    h += f'<div class="grid g4">{kp}</div>'

    marks.append(("ent", len(h)))
    if ent:
        vs, C, c = ent
        h += '<div class="card"><h2>Entrevista de requisitos</h2>'
        h += (f'<div class="sub">{c["total"]} perguntas até agora ({c["base"]} da base + {c["escopo"]} do escopo) · '
              f'varredura de lacunas: {esc(f.get("varredura_lacunas", "não"))}. Novas perguntas podem surgir conforme o escopo se define.</div>')
        h += barra([("ok", pct(c["respondidas"], c["total"])), ("wait", pct(c["aguardando"], c["total"])), ("byp", pct(c["bypass"], c["total"]))])
        blocos = []
        for p in vs:
            if p["bloco"] not in blocos:
                blocos.append(p["bloco"])
        for b in blocos:
            ps = [p for p in vs if p["bloco"] == b]
            r = sum(1 for p in ps if C.estado_p(p) == "respondida")
            y = sum(1 for p in ps if C.estado_p(p) == "bypass")
            w = sum(1 for p in ps if C.estado_p(p) == "aguardando")
            h += (f'<div class="row"><span>{esc(C.nome_bloco(e, b))}</span>'
                  f'{barra([("ok", pct(r, len(ps))), ("wait", pct(w, len(ps))), ("byp", pct(y, len(ps)))])}<span class="v">{r + y}/{len(ps)}</span></div>')
        h += '<div class="sub">Azul: respondida · roxo: com o cliente · amarelo: pulada (bypass, vira pendência)</div></div>'

    marks.append(("entregas", len(h)))
    if ents:
        h += '<div class="card"><h2>Entregas</h2>'
        for en in ents:
            fs = [x for x in ativas if x["entrega"] == en["id"]]
            ts = [t for x in fs for t in x["tasks"]]
            ok = sum(1 for t in ts if t["estado"] == "feita")
            ent_ok = sum(1 for x in fs if x["estado"] == "entregue")
            h += (f'<div class="row"><span><b>{esc(en["id"])}</b> · {esc(en["nome"])}</span>'
                  f'{barra([("done" if (fs and ent_ok == len(fs)) else "run", pct(ok, len(ts)) if ts else pct(ent_ok, len(fs)))])}'
                  f'<span class="v">{ent_ok}/{len(fs)} features · {pct(ok, len(ts))}% tasks</span></div>')
            if en["objetivo"]:
                h += f'<div class="sub">{esc(en["objetivo"])}</div>'
        h += "</div>"

    marks.append(("feats", len(h)))
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

    marks.append(("tasks", len(h)))
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

    marks.append(("pend", len(h)))
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

    marks.append(("hist", len(h)))
    h += '<div class="card"><h2>Últimos registros</h2>'
    if hist:
        h += '<ul class="hist">' + "".join(f'<li><time>{esc(x["data"])}</time>{esc(x["texto"])}</li>' for x in reversed(hist[-12:])) + "</ul>"
    else:
        h += '<div class="vazio">Sem registros.</div>'
    h += "</div>"
    marks.append(("fim", len(h)))
    seg = {n: h[a:(marks[i + 1][1])] for i, (n, a) in enumerate(marks[:-1])}
    cabeca = h[:marks[0][1]]
    painel = _abas(md, e, ent, feats, tasks, tst, hist, crs, f,
                   visao=seg["kpi"] + seg["ent"] + seg["entregas"] + seg["pend"] + seg["hist"],
                   tab_features=seg["feats"], tab_tasks=seg["tasks"])
    rodape = f'<footer>Gerado em {S.hoje()} a partir do SPEC.md · spec-flow</footer>'
    return pagina(f"{nome} — Painel", cabeca + painel + rodape)


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
