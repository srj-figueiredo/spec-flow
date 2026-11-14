"""specmd: leitura e escrita do SPEC.md (somente biblioteca padrão do Python)."""
import datetime
import html
import re

FASES = ["entrada", "entrevista", "spec", "features", "tasks", "construcao", "deploy", "manutencao"]
FASES_NOME = {
    "entrada": "Entrada", "entrevista": "Entrevista", "spec": "Spec", "features": "Features",
    "tasks": "Tasks", "construcao": "Construção", "deploy": "Deploy", "manutencao": "Manutenção",
}
ESTADOS_FEATURE = ["proposta", "aprovada", "em-andamento", "em-teste", "entregue", "alterada", "descartada"]
ESTADO_NOME = {
    "proposta": "Proposta", "aprovada": "Aprovada", "em-andamento": "Em andamento",
    "em-teste": "Em teste", "entregue": "Entregue", "alterada": "Alterada", "descartada": "Descartada",
}
MARCAS = {" ": "pendente", "~": "andamento", "x": "feita", "!": "bloqueada"}
MARCA_DE = {v: k for k, v in MARCAS.items()}
PLACEHOLDER = "(preencher)"
DEC_INI = "<!-- decisoes:inicio -->"
DEC_FIM = "<!-- decisoes:fim -->"
PROF_NOME = {"p": "pequeno", "m": "médio", "c": "completo"}


def hoje():
    return datetime.date.today().isoformat()


def agora():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def gravar(caminho, texto):
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


# ---------- seções ----------
SEC_RE = re.compile(r"^## (\d+)\. (.*)$", re.M)


def mascara(md):
    """Troca o conteúdo de comentários HTML por espaços, preservando posições."""
    return re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), md, flags=re.S)


def secoes(md):
    """Retorna lista de dicts: num, titulo, ini (início do corpo), fim. Posições valem para o texto original."""
    ms = list(SEC_RE.finditer(mascara(md)))
    out = []
    for i, m in enumerate(ms):
        fim = ms[i + 1].start() if i + 1 < len(ms) else len(md)
        out.append({"num": int(m.group(1)), "titulo": m.group(2).strip(), "ini": m.end() + 1, "fim": fim})
    return out


def corpo(md, num):
    """Corpo da seção já sem comentários (uso: leitura/parse)."""
    m = mascara(md)
    for s in secoes(md):
        if s["num"] == num:
            return m[s["ini"]:s["fim"]]
    return ""


def trocar_corpo(md, num, novo):
    for s in secoes(md):
        if s["num"] == num:
            return md[:s["ini"]] + "\n" + novo.strip("\n") + "\n\n" + md[s["fim"]:].lstrip("\n")
    raise KeyError(f"seção {num} não existe")


def titulo_projeto(md):
    m = re.match(r"#\s+(.+)", md)
    return m.group(1).strip() if m else "Projeto"


# ---------- ficha ----------
def ficha(md):
    d = {}
    for linha in corpo(md, 0).splitlines():
        m = re.match(r"^- ([\w_]+):\s*(.*)$", linha)
        if m:
            d[m.group(1)] = m.group(2).strip()
    return d


def set_ficha(md, chave, valor):
    for s in secoes(md):
        if s["num"] == 0:
            bloco = md[s["ini"]:s["fim"]]
            if re.search(rf"^- {re.escape(chave)}:", bloco, re.M):
                bloco = re.sub(rf"^(- {re.escape(chave)}:).*$", lambda m: f"{m.group(1)} {valor}", bloco, flags=re.M)
            else:
                bloco = bloco.rstrip("\n") + f"\n- {chave}: {valor}\n\n"
            return md[:s["ini"]] + bloco + md[s["fim"]:]
    raise KeyError("seção 0 (Ficha) não existe")


def vazio(texto):
    """Seção ainda não preenchida: vazia ou só com o marcador de preenchimento."""
    t = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    t = re.sub(r"^#{3,}.*$", "", t, flags=re.M)
    t = t.replace(PLACEHOLDER, "").strip()
    return len(t) < 3


# ---------- entregas ----------
def entregas(md):
    out = []
    for linha in corpo(md, 5).splitlines():
        m = re.match(r"^- (E\d+) · ([^·]+?)(?: · (.*))?$", linha.strip())
        if m:
            out.append({"id": m.group(1), "nome": m.group(2).strip(), "objetivo": (m.group(3) or "").strip()})
    return out


# ---------- features e tasks ----------
FEAT_RE = re.compile(r"^### (F-\d+) · (.*)$")
TASK_RE = re.compile(r"^  - \[([ ~x!])\] (T-\d+) · (.*)$")


def _lista(v):
    v = v.strip()
    if v in ("", "-", "—", "nenhuma"):
        return []
    return [x.strip() for x in re.split(r"[,;]", v) if x.strip()]


def features(md):
    feats = []
    atual = None
    chave = None
    tarefa = None
    for linha in corpo(md, 6).splitlines():
        m = FEAT_RE.match(linha)
        if m:
            atual = {"id": m.group(1), "titulo": m.group(2).strip(), "estado": "proposta", "entrega": "",
                     "valor": "", "origem": "", "aceite": [], "tasks": []}
            feats.append(atual)
            chave = None
            tarefa = None
            continue
        if atual is None:
            continue
        mt = TASK_RE.match(linha)
        if mt:
            tarefa = {"id": mt.group(2), "titulo": mt.group(3).strip(), "marca": mt.group(1),
                      "estado": MARCAS[mt.group(1)], "dono": "", "toca": [], "depende": [], "aceite": "",
                      "teste": "", "feature": atual["id"]}
            atual["tasks"].append(tarefa)
            continue
        mf = re.match(r"^    - ([\w_]+):\s*(.*)$", linha)
        if mf and tarefa is not None:
            k, v = mf.group(1), mf.group(2).strip()
            if k in ("toca", "depende"):
                tarefa[k] = _lista(v)
            else:
                tarefa[k] = v
            continue
        mk = re.match(r"^- ([\w_]+):\s*(.*)$", linha)
        if mk:
            chave = mk.group(1)
            tarefa = None
            v = mk.group(2).strip()
            if chave == "aceite":
                atual["aceite"] = [x for x in [v] if x]
            elif chave != "tasks":
                atual[chave] = v
            continue
        ml = re.match(r"^  - (.+)$", linha)
        if ml and chave == "aceite":
            atual["aceite"].append(ml.group(1).strip())
    return feats


def todas_tasks(md):
    return [t for f in features(md) for t in f["tasks"]]


def _bloco_feature(md, fid):
    s6 = next((s for s in secoes(md) if s["num"] == 6), None)
    if not s6:
        return None
    sub = mascara(md)[s6["ini"]:s6["fim"]]
    m = re.search(rf"^### {re.escape(fid)} · .*$", sub, re.M)
    if not m:
        return None
    prox = re.search(r"^### ", sub[m.end():], re.M)
    fim = m.end() + prox.start() if prox else len(sub)
    return s6["ini"] + m.start(), s6["ini"] + fim


def set_estado_feature(md, fid, estado):
    if estado not in ESTADOS_FEATURE:
        raise ValueError(f"estado inválido: {estado}. Use: {', '.join(ESTADOS_FEATURE)}")
    pos = _bloco_feature(md, fid)
    if not pos:
        raise KeyError(f"feature {fid} não encontrada")
    bloco = md[pos[0]:pos[1]]
    if re.search(r"^- estado:", bloco, re.M):
        bloco = re.sub(r"^- estado:.*$", f"- estado: {estado}", bloco, count=1, flags=re.M)
    else:
        linhas = bloco.split("\n", 1)
        bloco = linhas[0] + f"\n- estado: {estado}\n" + (linhas[1] if len(linhas) > 1 else "")
    return md[:pos[0]] + bloco + md[pos[1]:]


def set_marca_task(md, tid, estado):
    if estado not in MARCA_DE:
        raise ValueError(f"estado de task inválido: {estado}. Use: {', '.join(MARCA_DE)}")
    m = re.search(rf"^(  - \[)[ ~x!](\] {re.escape(tid)} · )", mascara(md), re.M)
    if not m:
        raise KeyError(f"task {tid} não encontrada")
    pos = m.start() + len(m.group(1))
    return md[:pos] + MARCA_DE[estado] + md[pos + 1:]


# ---------- change requests e histórico ----------
CR_RE = re.compile(r"^### (CR-\d+) · (.*)$")


def change_requests(md):
    out = []
    atual = None
    for linha in corpo(md, 7).splitlines():
        m = CR_RE.match(linha)
        if m:
            atual = {"id": m.group(1), "titulo": m.group(2).strip(), "estado": "aberta", "features": [], "motivo": "",
                     "data": ""}
            out.append(atual)
            continue
        if atual is None:
            continue
        mk = re.match(r"^- ([\w_]+):\s*(.*)$", linha)
        if mk:
            k, v = mk.group(1), mk.group(2).strip()
            atual[k] = _lista(v) if k == "features" else v
    return out


def historico(md):
    out = []
    for linha in corpo(md, 8).splitlines():
        m = re.match(r"^- (\d{4}-\d{2}-\d{2}) · (.*)$", linha)
        if m:
            out.append({"data": m.group(1), "texto": m.group(2).strip()})
    return out


def add_historico(md, texto):
    for s in secoes(md):
        if s["num"] == 8:
            corpo8 = md[s["ini"]:s["fim"]].rstrip("\n")
            corpo8 = re.sub(rf"\n?{re.escape(PLACEHOLDER)}\s*$", "", corpo8).rstrip("\n")
            return md[:s["ini"]] + corpo8 + f"\n- {hoje()} · {texto}\n"
    return md.rstrip("\n") + f"\n\n## 8. Histórico\n\n- {hoje()} · {texto}\n"


_DEF = {
    "F": r"^### F-(\d+) ·", "CR": r"^### CR-(\d+) ·", "T": r"^  - \[[ ~x!]\] T-(\d+) ·", "E": r"^- E(\d+) ·",
}


def proximo_id(md, prefixo, largura=3):
    """Próximo id livre. Conta só definições reais (não menções em texto nem comentários)."""
    if prefixo in _DEF:
        nums = [int(x) for x in re.findall(_DEF[prefixo], mascara(md), re.M)]
        if prefixo == "E":
            return f"E{(max(nums) + 1 if nums else 1)}"
    else:
        nums = [int(x) for x in re.findall(rf"\b{prefixo}-(\d+)\b", md)]
    return f"{prefixo}-{(max(nums) + 1 if nums else 1):0{largura}d}"


# ---------- markdown -> html ----------
def _inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)

    def link(m):
        url = m.group(2)
        if not re.match(r"^(https?://|#|\./|\.\./|[\w./-]+$)", url):
            return m.group(0)
        return f'<a href="{url}">{m.group(1)}</a>'
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    return t


def _slug(t):
    t = re.sub(r"[^\w\s-]", "", t.lower()).strip()
    return re.sub(r"[\s_]+", "-", t)


def _badge_estado(valor):
    from_estado = valor if valor in ESTADO_NOME else None
    if from_estado:
        return f'<span class="chip e-{from_estado}">{ESTADO_NOME[from_estado]}</span>'
    return None


def md_para_html(md):
    """Conversor mínimo (títulos, listas aninhadas, tabelas, citações, código, parágrafos)."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    linhas = md.split("\n")
    out = []
    toc = []
    i = 0
    n = len(linhas)
    lista_stack = []  # indentações abertas

    def fechar_listas(ate=-1):
        while lista_stack and lista_stack[-1] > ate:
            lista_stack.pop()
            out.append("</ul>")

    while i < n:
        ln = linhas[i]
        if ln.strip().startswith("```"):
            fechar_listas()
            buf = []
            i += 1
            while i < n and not linhas[i].strip().startswith("```"):
                buf.append(linhas[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            continue
        m = re.match(r"^(#{1,4}) (.*)$", ln)
        if m:
            fechar_listas()
            nivel = len(m.group(1))
            txt = m.group(2).strip()
            sid = _slug(txt)
            if nivel in (2, 3):
                toc.append((nivel, txt, sid))
            out.append(f'<h{nivel} id="{sid}">{_inline(txt)}</h{nivel}>')
            i += 1
            continue
        if re.match(r"^\s*\|.*\|\s*$", ln) and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", linhas[i + 1]):
            fechar_listas()
            cab = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            linhas_t = []
            while i < n and re.match(r"^\s*\|.*\|\s*$", linhas[i]):
                linhas_t.append([c.strip() for c in linhas[i].strip().strip("|").split("|")])
                i += 1
            h = "<div class='tabela'><table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in cab) + "</tr></thead><tbody>"
            for r in linhas_t:
                h += "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>"
            out.append(h + "</tbody></table></div>")
            continue
        m = re.match(r"^(\s*)- (.*)$", ln)
        if m:
            ind = len(m.group(1))
            item = m.group(2)
            if not lista_stack or ind > lista_stack[-1]:
                lista_stack.append(ind)
                out.append("<ul>")
            else:
                while lista_stack and ind < lista_stack[-1]:
                    lista_stack.pop()
                    out.append("</ul>")
            mc = re.match(r"^\[([ ~x!])\] (.*)$", item)
            if mc:
                marca = mc.group(1)
                glifo = {" ": "○", "~": "▶", "x": "✓", "!": "■"}[marca]
                cls = {" ": "pendente", "~": "andamento", "x": "feita", "!": "bloqueada"}[marca]
                out.append(f'<li class="task t-{cls}"><span class="g">{glifo}</span> {_inline(mc.group(2))}</li>')
            else:
                me = re.match(r"^estado:\s*(\S+)$", item)
                badge = _badge_estado(me.group(1)) if me else None
                if badge:
                    out.append(f"<li><span class='k'>estado</span> {badge}</li>")
                else:
                    mk = re.match(r"^([\w_]+):\s*(.*)$", item)
                    if mk and len(mk.group(1)) < 20 and mk.group(2):
                        out.append(f"<li><span class='k'>{html.escape(mk.group(1))}</span> {_inline(mk.group(2))}</li>")
                    else:
                        out.append(f"<li>{_inline(item)}</li>")
            i += 1
            continue
        if ln.startswith(">"):
            fechar_listas()
            buf = []
            while i < n and linhas[i].startswith(">"):
                buf.append(linhas[i].lstrip("> "))
                i += 1
            out.append("<blockquote>" + _inline(" ".join(buf)) + "</blockquote>")
            continue
        if re.match(r"^\s*---+\s*$", ln):
            fechar_listas()
            out.append("<hr>")
            i += 1
            continue
        if not ln.strip():
            fechar_listas()
            i += 1
            continue
        fechar_listas()
        buf = [ln.strip()]
        i += 1
        while i < n and linhas[i].strip() and not re.match(r"^(#{1,4} |\s*- |\s*\||>|```)", linhas[i]):
            buf.append(linhas[i].strip())
            i += 1
        out.append("<p>" + _inline(" ".join(buf)) + "</p>")
    fechar_listas()
    return "\n".join(out), toc
