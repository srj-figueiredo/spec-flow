#!/usr/bin/env python3
"""netlify.py: publica a página do cliente no Netlify e lê os envios do formulário. Somente biblioteca padrão + curl.

Autenticação:
  - Sessão na nuvem: o ambiente injeta o token nas chamadas a api.netlify.com (nada a configurar).
  - Máquina local: exporte NETLIFY_AUTH_TOKEN (token pessoal do Netlify).

Comandos:
  site-ensure NOME [--aleatorio] [--ficha PASTA]   cria o site (com --aleatorio, sempre novo e com sufixo impossível de adivinhar); imprime JSON {id, name, url}
  deploy SITE_ID PASTA [--ficha .]   publica a pasta (zip) e espera ficar no ar; imprime JSON {deploy_id, state, url}
  forms SITE_ID               lista os formulários detectados no site
  submissions SITE_ID [--form NOME]   envios do formulário, normalizados, mais antigos primeiro (JSON)
  delete-site SITE_ID         apaga o site (use só em pilotos)
"""
import argparse
import io
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
import zipfile

API = "https://api.netlify.com/api/v1"


def curl(metodo, caminho, corpo=None, tipo=None, params=None, timeout=120):
    url = API + caminho + (("?" + params) if params else "")
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-X", metodo, "-w", "\n%{http_code}", url]
    tok = os.environ.get("NETLIFY_AUTH_TOKEN")
    if tok:
        cmd += ["-H", f"Authorization: Bearer {tok}"]
    if tipo:
        cmd += ["-H", f"Content-Type: {tipo}"]
    arq = None
    if corpo is not None:
        arq = tempfile.NamedTemporaryFile(delete=False)
        arq.write(corpo if isinstance(corpo, bytes) else corpo.encode("utf-8"))
        arq.close()
        cmd += ["--data-binary", "@" + arq.name]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        if arq:
            os.unlink(arq.name)
    if r.returncode != 0:
        die(f"curl falhou: {r.stderr.strip()[:300]}")
    saida, _, codigo = r.stdout.rpartition("\n")
    return int(codigo), saida


def api(metodo, caminho, corpo=None, tipo=None, params=None):
    codigo, saida = curl(metodo, caminho, corpo, tipo, params)
    if codigo in (401, 403):
        die(f"Netlify recusou o acesso (HTTP {codigo}). Falta o token: nuvem = credencial para api.netlify.com; local = NETLIFY_AUTH_TOKEN.")
    if codigo >= 400:
        die(f"Netlify HTTP {codigo}: {saida[:300]}")
    try:
        return json.loads(saida) if saida.strip() else None
    except json.JSONDecodeError:
        die(f"resposta inesperada do Netlify: {saida[:200]}")


def die(msg):
    print(f"erro: {msg}", file=sys.stderr)
    sys.exit(1)


def gravar_ficha_campo(pasta, chave, valor):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import specmd
    d = os.path.abspath(pasta)
    while not os.path.isfile(os.path.join(d, "SPEC.md")):
        pai = os.path.dirname(d)
        if pai == d:
            die(f"SPEC.md não encontrado a partir de {pasta}")
        d = pai
    caminho = os.path.join(d, "SPEC.md")
    specmd.gravar(caminho, specmd.set_ficha(specmd.ler(caminho), chave, valor))


def gravar_ficha(pasta, site_id, url):
    """Registra o site do cliente na Ficha do SPEC.md do projeto (a retomada automática depende disso)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import specmd
    d = os.path.abspath(pasta)
    while not os.path.isfile(os.path.join(d, "SPEC.md")):
        pai = os.path.dirname(d)
        if pai == d:
            die(f"SPEC.md não encontrado a partir de {pasta}")
        d = pai
    caminho = os.path.join(d, "SPEC.md")
    md = specmd.ler(caminho)
    md = specmd.set_ficha(md, "cliente_site_id", site_id)
    md = specmd.set_ficha(md, "cliente_url", url)
    specmd.gravar(caminho, md)


def cmd_site_ensure(a):
    nome = a.nome
    if a.aleatorio:
        # endereço impossível de adivinhar: quem tem o link acessa, ninguém mais acha
        nome = f"{a.nome}-{secrets.token_hex(5)}"[:63]
    else:
        for s in api("GET", "/sites", params="per_page=100&filter=all") or []:
            if s["name"] == nome:
                print(json.dumps({"id": s["id"], "name": s["name"], "url": s.get("ssl_url") or s.get("url"), "criado": False}))
                return
    s = api("POST", "/sites", json.dumps({"name": nome}), "application/json")
    url = s.get("ssl_url") or s.get("url")
    if a.ficha:
        gravar_ficha(a.ficha, s["id"], url)
    print(json.dumps({"id": s["id"], "name": s["name"], "url": url, "criado": True}))


def zip_da_pasta(pasta):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for raiz, _, arqs in os.walk(pasta):
            for f in sorted(arqs):
                caminho = os.path.join(raiz, f)
                z.write(caminho, os.path.relpath(caminho, pasta))
    return buf.getvalue()


def cmd_deploy(a):
    if not os.path.isdir(a.pasta):
        die(f"pasta não existe: {a.pasta}")
    d = api("POST", f"/sites/{a.site_id}/deploys", zip_da_pasta(a.pasta), "application/zip")
    did = d["id"]
    for _ in range(40):
        d = api("GET", f"/deploys/{did}")
        if d["state"] in ("ready", "error"):
            break
        time.sleep(3)
    if d["state"] != "ready":
        die(f"deploy terminou em '{d['state']}': {d.get('error_message') or ''}")
    if a.ficha:
        gravar_ficha_campo(a.ficha, "cliente_publicada_em", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print(json.dumps({"deploy_id": did, "state": d["state"], "url": d.get("ssl_url") or d.get("url")}))


def cmd_forms(a):
    fs = api("GET", f"/sites/{a.site_id}/forms") or []
    print(json.dumps([{"id": f["id"], "name": f["name"], "submission_count": f.get("submission_count")} for f in fs]))


def cmd_submissions(a):
    fs = api("GET", f"/sites/{a.site_id}/forms") or []
    alvo = [f for f in fs if not a.form or f["name"] == a.form]
    if not alvo:
        die("nenhum formulário detectado neste site (a detecção de formulários está ligada? houve deploy depois de ligar?)")
    saida = []
    for f in alvo:
        pagina = 1
        while True:
            lote = api("GET", f"/forms/{f['id']}/submissions", params=f"per_page=100&page={pagina}") or []
            for s in lote:
                saida.append({"id": s["id"], "em": s["created_at"], "form": f["name"], "data": s.get("data") or {}})
            if len(lote) < 100:
                break
            pagina += 1
    saida.sort(key=lambda x: x["em"])
    print(json.dumps(saida, ensure_ascii=False))


def cmd_delete_site(a):
    api("DELETE", f"/sites/{a.site_id}")
    print("site apagado")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("site-ensure"); p.add_argument("nome"); p.add_argument("--aleatorio", action="store_true", help="acrescenta sufixo aleatório (link privado)"); p.add_argument("--ficha", metavar="PASTA", help="grava cliente_site_id e cliente_url na Ficha do SPEC.md do projeto"); p.set_defaults(f=cmd_site_ensure)
    p = sp.add_parser("deploy"); p.add_argument("site_id"); p.add_argument("pasta"); p.add_argument("--ficha", metavar="PASTA", help="grava cliente_publicada_em na Ficha do projeto"); p.set_defaults(f=cmd_deploy)
    p = sp.add_parser("forms"); p.add_argument("site_id"); p.set_defaults(f=cmd_forms)
    p = sp.add_parser("submissions"); p.add_argument("site_id"); p.add_argument("--form"); p.set_defaults(f=cmd_submissions)
    p = sp.add_parser("delete-site"); p.add_argument("site_id"); p.set_defaults(f=cmd_delete_site)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
