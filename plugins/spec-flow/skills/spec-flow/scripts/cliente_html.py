"""cliente_html: blocos da página do cliente (opções visuais, links de referência, upload de arquivo). Biblioteca padrão."""
import html
import re

esc = html.escape

LIMITE_MB = 8          # limite do Netlify Forms: 8 MB por envio (requisição inteira), 1 arquivo por campo
MARGEM_MB = 7.5        # a página barra acima disso, para sobrar espaço para o resto do formulário

TITULOS = {
    "paleta": "Cores: qual combina mais com o seu negócio?",
    "layout": "Organização da tela: qual se parece mais com o que você imagina?",
    "tipografia": "Letras: qual estilo você prefere?",
}
NOMES = {"paleta": "Paleta", "layout": "Organização", "tipografia": "Letras"}

PALETAS = [
    ("Sóbria e profissional", ["#1f2937", "#3b82f6", "#f3f4f6"]),
    ("Quente e acolhedora", ["#7c2d12", "#f59e0b", "#fff7ed"]),
    ("Fresca e moderna", ["#0f766e", "#34d399", "#ecfeff"]),
    ("Vibrante e jovem", ["#6d28d9", "#ec4899", "#faf5ff"]),
    ("Clássica e elegante", ["#111827", "#b45309", "#fafaf9"]),
]

_R = '<rect x="2" y="2" width="116" height="76" rx="6" fill="none" stroke="currentColor" opacity=".5"/>'


def _blk(x, y, w, h, o):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="currentColor" opacity="{o}"/>'


LAYOUTS = {
    "hero": ("Página com destaque no topo", _R + _blk(8, 8, 104, 8, .25) + _blk(8, 22, 104, 26, .38)
             + _blk(8, 54, 32, 18, .2) + _blk(44, 54, 32, 18, .2) + _blk(80, 54, 32, 18, .2)),
    "painel": ("Menu lateral e painel", _R + _blk(8, 8, 26, 64, .3) + _blk(40, 8, 72, 10, .25)
               + _blk(40, 24, 34, 22, .2) + _blk(78, 24, 34, 22, .2) + _blk(40, 52, 72, 20, .2)),
    "grade": ("Catálogo em grade", _R + _blk(8, 8, 104, 8, .25) + _blk(8, 22, 32, 24, .25) + _blk(44, 22, 32, 24, .25)
              + _blk(80, 22, 32, 24, .25) + _blk(8, 50, 32, 22, .2) + _blk(44, 50, 32, 22, .2) + _blk(80, 50, 32, 22, .2)),
    "lista": ("Lista simples", _R + _blk(8, 8, 104, 8, .25) + _blk(8, 22, 104, 10, .22) + _blk(8, 36, 104, 10, .22)
              + _blk(8, 50, 104, 10, .22) + _blk(8, 64, 104, 8, .22)),
}

TIPOGRAFIAS = [
    ("Moderna (sem serifa)", "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"),
    ("Clássica (com serifa)", "Georgia, 'Times New Roman', serif"),
    ("Arredondada e amigável", "'Trebuchet MS', 'Segoe UI', ui-rounded, sans-serif"),
]


def opcoes_padrao(tipo):
    """Opções visuais padrão de cada tipo, no formato [{rotulo, dado}]."""
    if tipo == "paleta":
        return [{"rotulo": r, "dado": ",".join(c)} for r, c in PALETAS]
    if tipo == "layout":
        return [{"rotulo": v[0], "dado": k} for k, v in LAYOUTS.items()]
    if tipo == "tipografia":
        return [{"rotulo": r, "dado": f} for r, f in TIPOGRAFIAS]
    raise ValueError(f"tipo visual inválido: {tipo} (use paleta, layout ou tipografia)")


def _hex_ok(c):
    return bool(re.fullmatch(r"#[0-9a-fA-F]{3,8}", c.strip()))


def _miniatura(tipo, dado):
    if tipo == "paleta":
        cores = [c.strip() for c in dado.split(",") if _hex_ok(c)]
        return '<span class="sw">' + "".join(f'<i style="background:{esc(c)}"></i>' for c in cores) + "</span>"
    if tipo == "layout":
        svg = LAYOUTS.get(dado, LAYOUTS["hero"])[1]
        return f'<svg viewBox="0 0 120 80" class="wf" aria-hidden="true">{svg}</svg>'
    if tipo == "tipografia":
        fam = re.sub(r"[^\w\s,'\"\-]", "", dado)
        return f'<span class="ty" style="font-family:{esc(fam)}">Aa Bolo de chocolate</span>'
    return ""


def render_visuais(pid, visuais):
    h = ""
    for g in visuais:
        tipo = g["tipo"]
        h += f'<fieldset class="vg"><legend>{esc(g.get("titulo") or TITULOS.get(tipo, tipo))}</legend><div class="vgrid">'
        for o in g["opcoes"]:
            h += (f'<label class="vc"><input type="radio" name="v_{esc(pid)}_{esc(tipo)}" value="{esc(o["rotulo"])}">'
                  f'<span class="vbox">{_miniatura(tipo, o.get("dado", ""))}<b>{esc(o["rotulo"])}</b></span></label>')
        h += "</div></fieldset>"
    return h + '<p class="nota3">Se nenhuma opção agradar, explique abaixo com suas palavras.</p>' if visuais else ""


def _url_ok(u):
    return bool(re.fullmatch(r"https?://[^\s<>\"']+", u.strip()))


def render_refs(refs):
    itens = ""
    for r in refs:
        if not _url_ok(r["url"]):
            continue
        rot = r.get("rotulo") or r["url"]
        itens += f'<li><a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{esc(rot)}</a></li>'
    return f'<div class="refs"><p class="t2">Exemplos para você olhar (abrem em outra aba):</p><ul>{itens}</ul></div>' if itens else ""


def render_links_campo(pid):
    return (f'<label class="t" for="l_{esc(pid)}">Tem algum site ou perfil que você acha bonito e gostaria como referência? '
            f'Cole o link (um por linha).</label><textarea id="l_{esc(pid)}" name="l_{esc(pid)}" class="lk"></textarea>')


def render_arquivo(pid, desc):
    rot = esc(desc) if desc else "Se tiver, envie o arquivo aqui"
    return (f'<div class="arq"><label class="t" for="f_{esc(pid)}">📎 {rot}</label>'
            f'<input type="file" id="f_{esc(pid)}" name="f_{esc(pid)}" data-g="g_{esc(pid)}">'
            f'<p class="aviso">Tamanho máximo: {LIMITE_MB} MB por envio (somando todos os arquivos desta página) e um arquivo por pergunta. '
            f'Não envie senhas nem documentos pessoais sensíveis.</p>'
            f'<label class="opt"><input type="checkbox" name="g_{esc(pid)}" value="sim"><span>Meu arquivo é maior que {LIMITE_MB} MB. '
            f'O desenvolvedor entrará em contato para combinar como pegar o arquivo.</span></label></div>')


def resumo(r):
    """Resumo em linhas de uma resposta do cliente (opção, escolhas visuais, texto, links, arquivo)."""
    linhas = []
    if r.get("opcao"):
        linhas.append(r["opcao"])
    for v in r.get("visuais", []):
        linhas.append(v)
    if r.get("texto"):
        linhas.append(r["texto"])
    if r.get("links"):
        linhas.append("Referências: " + ", ".join(x for x in re.split(r"\s+", r["links"]) if x))
    a = r.get("arquivo")
    if a:
        tam = f" ({a['tamanho'] // 1024} KB)" if a.get("tamanho") else ""
        linhas.append(f"Arquivo enviado: {a.get('nome') or 'sem nome'}{tam}")
    if r.get("grande"):
        linhas.append("Arquivo grande: o desenvolvedor entrará em contato para pegar")
    return linhas
