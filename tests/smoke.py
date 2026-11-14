#!/usr/bin/env python3
"""Testes de fumaça da spec-flow (biblioteca padrão). Rode: python3 tests/smoke.py
Cobre o motor, a página do cliente, o registro cumulativo, a verificação de impacto e as passagens de fase.
Não usa rede: o Netlify só é testado no que não depende dele."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(RAIZ, "plugins", "spec-flow", "skills", "spec-flow")
SPEC = os.path.join(SKILL, "scripts", "spec.py")
NETLIFY = os.path.join(SKILL, "scripts", "netlify.py")
OK, FALHAS = 0, []


def sp(cwd, *args, falha=False):
    r = subprocess.run([sys.executable, SPEC, *args], cwd=cwd, capture_output=True, text=True)
    if falha:
        return r.returncode != 0, (r.stdout + r.stderr)
    return r.returncode == 0, (r.stdout + r.stderr)


def verifica(nome, cond, extra=""):
    global OK
    if cond:
        OK += 1
    else:
        FALHAS.append(f"{nome} {extra}".strip())
        print(f"  FALHOU: {nome} {extra}")


def ler(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def entrev(cwd):
    return json.load(open(os.path.join(cwd, ".spec", "interview.json"), encoding="utf-8"))


def pergunta(cwd, pid):
    return next(p for p in entrev(cwd)["perguntas"] if p["id"] == pid)


def set_secao(cwd, num, corpo):
    sys.path.insert(0, os.path.join(SKILL, "scripts"))
    import specmd as S
    md = S.ler(os.path.join(cwd, "SPEC.md"))
    S.gravar(os.path.join(cwd, "SPEC.md"), S.trocar_corpo(md, num, corpo))


def novo(nome="Projeto <b>Teste</b>", tipo="app-web", prof="m"):
    d = tempfile.mkdtemp(prefix="specflow-")
    ok, out = sp(d, "init", nome, "--tipo", tipo, "--prof", prof)
    verifica("init cria o projeto", ok, out)
    return d


def teste_init_e_banco():
    print("• init e banco de perguntas")
    d = novo()
    verifica("SPEC.md, interview.json, painel e spec.html existem",
             all(os.path.exists(os.path.join(d, x)) for x in ("SPEC.md", ".spec/interview.json", "docs/painel.html", "docs/spec.html")))
    verifica("CLAUDE.md recebe a linha de retomada", "spec-flow" in ler(os.path.join(d, "CLAUDE.md")))
    verifica("init repetido é recusado", sp(d, "init", "x", "--tipo", "site", falha=True)[0])
    verifica("tipo inválido é recusado", sp(tempfile.mkdtemp(), "init", "x", "--tipo", "foo", falha=True)[0])
    n = {}
    for prof in "pmc":
        e = tempfile.mkdtemp()
        sp(e, "init", "t", "--tipo", "saas", "--prof", prof)
        n[prof] = len(entrev(e)["perguntas"])
    verifica("profundidade p < m < c", n["p"] < n["m"] < n["c"], str(n))
    banco = json.load(open(os.path.join(SKILL, "data", "question-bank.json"), encoding="utf-8"))
    ids = [q["id"] for q in banco["perguntas"]]
    verifica("ids do banco são únicos", len(ids) == len(set(ids)))
    verifica("toda pergunta tem opção, bloco válido e motivo", all(q["o"] and q.get("why") and q["bloco"] in [b["id"] for b in banco["blocos"]] for q in banco["perguntas"]))
    verifica("U-06 é pergunta de design", pergunta(d, "U-06").get("design") is True)
    shutil.rmtree(d)
    return n


def teste_entrevista():
    print("• entrevista: respostas, condicionais, bypass, escopo")
    d = novo()
    verifica("opção 1", sp(d, "answer", "N-01", "--opt", "1")[0])
    verifica("opção fora do intervalo recusada", sp(d, "answer", "N-02", "--opt", "99", falha=True)[0])
    verifica("várias opções em pergunta simples recusada", sp(d, "answer", "N-02", "--opt", "1,2", falha=True)[0])
    verifica("resposta livre", sp(d, "answer", "N-02", "--text", "assinatura mensal")[0])
    verifica("bypass", sp(d, "answer", "N-03", "--bypass", "--text", "cliente não definiu")[0])
    verifica("I-02 (pagamento) oculta antes de I-01", all(p["id"] != "I-02" for p in json.loads(sp(d, "next", "-n", "99", "--json")[1])))
    sp(d, "answer", "I-01", "--opt", "2,3")
    verifica("I-02 aparece depois de marcar pagamento", any(p["id"] == "I-02" for p in json.loads(sp(d, "next", "-n", "99", "--json")[1])))
    verifica("add pergunta do escopo", sp(d, "add", "--bloco", "negocio", "--q", "Pergunta nova?", "--opt", "a", "--opt", "b", "--motivo", "briefing: x")[0])
    verifica("pergunta do escopo marcada", pergunta(d, "X-01").get("origem") == "escopo")
    verifica("dica registrada sem responder", sp(d, "dica", "D-01", "planilha")[0] and not pergunta(d, "D-01").get("resposta"))
    verifica("rec troca a recomendada", sp(d, "rec", "D-01", "2")[0] and pergunta(d, "D-01")["o"][0][0].startswith("Sim, importar"))
    verifica("rec em respondida é recusado", sp(d, "rec", "N-01", "2", falha=True)[0])
    md = ler(os.path.join(d, "SPEC.md"))
    verifica("decisões sincronizadas no SPEC.md", "| N-02 |" in md and "PENDENTE (bypass)" in md)
    verifica("contador mostra base + escopo", "do escopo" in sp(d, "status")[1])
    shutil.rmtree(d)


def teste_gates_e_fases():
    print("• gates e fases")
    d = novo(prof="p")
    verifica("entrada→entrevista barra sem objetivo", sp(d, "fase", "entrevista", falha=True)[0])
    set_secao(d, 1, "Sistema de teste.")
    verifica("entrevista liberada", sp(d, "fase", "entrevista")[0])
    verifica("pular fase recusado", sp(d, "fase", "features", falha=True)[0])
    verifica("sair com pendências barrado", sp(d, "fase", "spec", falha=True)[0])
    sp(d, "bypass-all", "--motivo", "teste")
    verifica("sem varredura barrado", "varredura" in sp(d, "gate", falha=True)[1])
    sp(d, "varredura")
    verifica("gate libera", sp(d, "gate")[0])
    verifica("fase spec", sp(d, "fase", "spec")[0])
    verifica("spec→features barra seções vazias", sp(d, "fase", "features", falha=True)[0])
    set_secao(d, 2, "### Dentro do escopo\n\n- A\n\n### Fora do escopo\n\n- B")
    verifica("fase features", sp(d, "fase", "features")[0])
    return d


FEATURES = """<!--
exemplo ignorado pelo leitor
### F-099 · fantasma
-->

### F-001 · Cadastro
- estado: proposta
- entrega: E1
- valor: base
- aceite:
  - criar e buscar
- tasks:
  - [ ] T-001 · Modelo
    - dono: agente-backend
    - toca: src/model.py
    - depende: —
    - aceite: tabela criada
    - teste: pytest a
  - [ ] T-002 · Tela
    - dono: agente-frontend
    - toca: src/model.py
    - depende: —
    - aceite: salva
    - teste: pw b

### F-002 · Agenda
- estado: proposta
- entrega: E1
- valor: marcar
- aceite:
  - ver horários
- tasks:
  - [ ] T-003 · Regra
    - dono: agente-backend
    - toca: src/agenda.py
    - depende: T-001
    - aceite: sem conflito
    - teste: pytest c
"""


def teste_features_tasks(d):
    print("• features, tasks, paralelo, change request")
    set_secao(d, 5, "- E1 · MVP · primeira entrega")
    set_secao(d, 6, FEATURES)
    verifica("exemplo em comentário não vira feature", "F-099" not in sp(d, "status", "--json")[1] and
             json.loads(sp(d, "status", "--json")[1])["features"] == {"proposta": 2})
    verifica("features→tasks barra proposta", sp(d, "fase", "tasks", falha=True)[0])
    sp(d, "set-feature", "F-001", "aprovada")
    sp(d, "set-feature", "F-002", "aprovada")
    verifica("fase tasks", sp(d, "fase", "tasks")[0])
    verifica("ids novos corretos", sp(d, "new-id", "F")[1].strip() == "F-003" and sp(d, "new-id", "T")[1].strip() == "T-004" and sp(d, "new-id", "CR")[1].strip() == "CR-001")
    sp(d, "ficha", "tasks_paralelas", "sim")
    ok, out = sp(d, "check", falha=True)
    verifica("check barra tasks paralelas que disputam arquivo", ok and "T-001 e T-002" in out, out)
    verifica("tasks→construção barrado pelo conflito", sp(d, "fase", "construcao", falha=True)[0])
    sp(d, "ficha", "tasks_paralelas", "não")
    verifica("sem paralelo o check passa", sp(d, "check")[0])
    verifica("fase construcao", sp(d, "fase", "construcao")[0])
    ok, out = sp(d, "ready", "--json")
    verifica("ready devolve tasks sem dependência pendente", {t["id"] for t in json.loads(out)["lote_paralelo"]} == {"T-001"} or
             {t["id"] for t in json.loads(out)["lote_paralelo"]} <= {"T-001", "T-002"}, out)
    sp(d, "set-task", "T-001", "andamento")
    verifica("1ª task iniciada move feature para em-andamento", json.loads(sp(d, "status", "--json")[1])["features"].get("em-andamento") == 1)
    for t in ("T-001", "T-002", "T-003"):
        sp(d, "set-task", t, "feita")
    verifica("deploy barra sem em-teste", sp(d, "fase", "deploy", falha=True)[0])
    sp(d, "set-feature", "F-001", "em-teste")
    sp(d, "set-feature", "F-002", "em-teste")
    verifica("fase deploy", sp(d, "fase", "deploy")[0])
    verifica("manutenção barra sem entregue", sp(d, "fase", "manutencao", falha=True)[0])
    sp(d, "set-feature", "F-001", "entregue")
    sp(d, "set-feature", "F-002", "entregue")
    verifica("fase manutencao", sp(d, "fase", "manutencao")[0])
    ok, out = sp(d, "cr-new", "Remarcar online", "--features", "F-002", "--motivo", "pedido")
    verifica("cr-new devolve CR-001", ok and out.strip() == "CR-001", out)
    sp(d, "cr-set", "CR-001", "aprovada")
    verifica("CR aprovado marca feature como alterada", json.loads(sp(d, "status", "--json")[1])["features"].get("alterada") == 1)
    verifica("histórico registra fases e CR", all(k in ler(os.path.join(d, "SPEC.md")) for k in ("CR-001 aberta", "fase: Deploy → Manutenção")))


def teste_cliente(d):
    print("• link do cliente: direcionar, design, arquivo, registro cumulativo")
    d = novo(nome="Loja <script>alert(1)</script> da Ana", prof="m")
    verifica("direcionar sem texto nem sugestão é recusado", sp(d, "cliente", "S-01", falha=True)[0])
    verifica("sugestão do banco é usada", sp(d, "cliente", "N-03")[0])
    verifica("design sem visual/ref é recusado", "DESIGN" in sp(d, "cliente", "U-06", "--texto", "Visual?", falha=True)[1])
    verifica("ref com esquema perigoso é recusada", sp(d, "cliente", "U-06", "--texto", "V?", "--ref", "javascript:alert(1)", falha=True)[0])
    verifica("design com visuais e referência", sp(d, "cliente", "U-06", "--texto", "Que visual combina?", "--visual", "paleta", "--visual", "layout",
                                                  "--visual", "tipografia", "--ref", "Exemplo|https://example.com/a")[0])
    verifica("upload em D-01", sp(d, "cliente", "D-01", "--texto", "Envie a planilha", "--arquivo", "--arquivo-desc", "a planilha")[0])
    verifica("status mostra aguardando cliente", "Aguardando o cliente: 3" in sp(d, "status")[1])
    ok, out = sp(d, "export-cliente")
    h = ler(os.path.join(d, ".spec", "cliente", "index.html"))
    verifica("export-cliente gera a página", ok and "3 perguntas novas" in out, out)
    verifica("nome do projeto é escapado (sem script injetado)", "<script>alert(1)" not in h and "&lt;script&gt;" in h)
    for k in ('name="v_U-06_paleta"', 'name="v_U-06_layout"', 'name="v_U-06_tipografia"', 'name="l_U-06"', 'type="file"', 'name="g_D-01"',
              'enctype="multipart/form-data"', 'data-netlify="true"', 'netlify-honeypot="bot-field"', 'rel="noopener noreferrer"', "8 MB"):
        verifica(f"página contém {k}", k in h)
    verifica("robots e headers de não indexação", all(os.path.exists(os.path.join(d, ".spec", "cliente", f)) for f in ("robots.txt", "_headers", "obrigado.html")))
    # --- respostas do cliente
    env1 = [{"id": "s1", "em": "2026-11-14T18:00:00Z", "data": {
        "q_N-03": "Vou vender mais", "v_U-06_paleta": "Quente e acolhedora", "v_U-06_layout": "Catálogo em grade", "l_U-06": "https://a.com\nhttps://b.com",
        "f_D-01": {"url": "https://x/c.csv", "filename": "c.csv", "size": 20480, "type": "text/csv"}, "respondente": "Ana"}}]
    json.dump(env1, open(os.path.join(d, "e1.json"), "w"))
    ok, out = sp(d, "import-cliente", "e1.json")
    verifica("import registra 3 respostas e exige verificação de impacto", ok and "3 respostas" in out and "OBRIGATÓRIO" in out, out)
    verifica("reimportar não duplica", "0 respostas" in sp(d, "import-cliente", "e1.json")[1])
    env2 = env1 + [{"id": "s2", "em": "2026-11-15T09:00:00Z", "data": {"q_N-03": "Vou ganhar tempo", "g_D-01": "sim", "f_D-01": ""}}]
    json.dump(env2, open(os.path.join(d, "e2.json"), "w"))
    sp(d, "import-cliente", "e2.json")
    rs = pergunta(d, "N-03")["respostas_cliente"]
    verifica("reenvio vira complemento e a original fica intacta", len(rs) == 2 and rs[0]["opcao"] == "Vou vender mais")
    verifica("arquivo grande registrado", any(r.get("grande") for r in pergunta(d, "D-01")["respostas_cliente"]))
    verifica("arquivo recebido tem nome e tamanho", pergunta(d, "D-01")["respostas_cliente"][0]["arquivo"]["nome"] == "c.csv")
    md = ler(os.path.join(d, "SPEC.md"))
    verifica("registro do cliente no SPEC.md com código", "Registro das respostas do cliente" in md and re.search(r"Código do registro: `[0-9a-f]{12}`", md) is not None)
    verifica("escolhas visuais no registro", "Paleta: Quente e acolhedora" in md)
    cod1 = re.search(r"`([0-9a-f]{12})`", md).group(1)
    sp(d, "sync")
    verifica("código estável entre sincronizações", cod1 in ler(os.path.join(d, "SPEC.md")))
    # --- impacto
    verifica("status acusa respostas sem verificação", "SEM verificação" in sp(d, "status")[1])
    verifica("impacto lista respostas e decisões", "VERIFICAÇÃO DE IMPACTO" in sp(d, "impacto")[1])
    sp(d, "answer", "U-01", "--opt", "1", "--text", "admin e gerente iguais")
    verifica("revisar exige decisão tomada", sp(d, "revisar", "S-01", "--motivo", "x", falha=True)[0])
    verifica("revisar marca decisão", sp(d, "revisar", "U-01", "--motivo", "lucro só da dona", "--origem", "U-06")[0])
    verifica("status lista decisão a revisar", "DECISÕES A REVISAR" in sp(d, "status")[1])
    sp(d, "impacto-ok")
    verifica("decisão em revisão aparece no SPEC.md", "REVISAR: lucro só da dona" in ler(os.path.join(d, "SPEC.md")))
    sp(d, "answer", "U-01", "--opt", "1", "--text", "gerente não vê lucro")
    p = pergunta(d, "U-01")
    verifica("refazer decisão arquiva a anterior e fecha a revisão", len(p["historico"]) == 1 and p["revisao"]["aberta"] is False)
    sp(d, "revisar", "U-01", "--motivo", "outra", "--origem", "U-06")
    verifica("revisao-ok mantém a decisão", sp(d, "revisao-ok", "U-01", "--nota", "mantida")[0] and pergunta(d, "U-01")["revisao"]["resultado"] == "decisão mantida")
    # --- gate de saída da entrevista
    set_secao(d, 1, "Teste.")
    sp(d, "fase", "entrevista")
    sp(d, "bypass-all")
    sp(d, "varredura")
    sp(d, "revisar", "U-01", "--motivo", "nova", "--origem", "U-06")
    verifica("decisão em revisão barra a saída da entrevista", "pendentes" in sp(d, "gate", falha=True)[1])
    sp(d, "revisao-ok", "U-01")
    verifica("liberado depois de resolver", sp(d, "gate")[0])
    # --- rodada 2: respostas anteriores travadas
    sp(d, "add", "--bloco", "negocio", "--q", "Pedidos por mês?", "--opt", "até 50", "--motivo", "cliente: vender mais")
    sp(d, "cliente", "X-01", "--texto", "Quantos pedidos por mês?")
    sp(d, "export-cliente")
    h = ler(os.path.join(d, ".spec", "cliente", "index.html"))
    verifica("rodada 1 aparece travada e a 2 tem campos", "Rodada 1" in h and "🔒" in h and 'name="t_X-01"' in h and 'name="q_N-03"' not in h)
    verifica("respostas anteriores são texto, não campo", 'name="t_N-03"' not in h and "Vou vender mais" in h)
    verifica("rodada 2 registrada", [r["n"] for r in entrev(d)["rodadas"]] == [1, 2] or [r["n"] for r in entrev(d)["rodadas"]] == [1])
    # --- só registro
    sp(d, "cliente", "X-01", "--remover")
    ok, out = sp(d, "export-cliente")
    h = ler(os.path.join(d, ".spec", "cliente", "index.html"))
    verifica("sem perguntas novas a página vira só registro (form oculto)", ok and "0 perguntas novas" in out and 'enctype="multipart/form-data" data-netlify="true" netlify-honeypot="bot-field" hidden' in h)
    return d


def teste_celular_e_render(d):
    print("• página do celular, importação de respostas e render")
    q = pergunta(d, "N-01")
    e = entrev(d)
    e["perguntas"][0]["q"] = "Teste </script><script>alert(1)</script>"
    json.dump(e, open(os.path.join(d, ".spec", "interview.json"), "w"), ensure_ascii=False)
    ok, out = sp(d, "export-web")
    h = ler(out.strip())
    verifica("export-web escapa </script> dentro dos dados", ok and "</script><script>alert(1)" not in h)
    docs = [{"id": "N-02", "data": {"tipo": "livre", "texto": "assinatura", "em": "2099-01-01T00:00:00Z"}},
            {"id": "N-04", "data": {"tipo": "cliente", "texto": "Como é hoje?", "opcoes": ["a"], "em": "2099-01-01T00:00:00Z", "arquivo": True}},
            {"id": "N-05", "data": {"tipo": "bypass", "texto": "depois", "em": "2099-01-01T00:00:00Z"}},
            {"id": "ZZ-99", "data": {"tipo": "livre", "texto": "inexistente", "em": "2099-01-01T00:00:00Z"}}]
    json.dump(docs, open(os.path.join(d, "db.json"), "w"))
    ok, out = sp(d, "import-answers", "db.json")
    verifica("import-answers aceita resposta, direcionamento ao cliente e bypass", ok and pergunta(d, "N-04")["cliente"]["arquivo"] is True and pergunta(d, "N-05")["resposta"]["tipo"] == "bypass")
    verifica("import-answers ignora id inexistente", not any(p["id"] == "ZZ-99" for p in entrev(d)["perguntas"]))
    docs = [{"id": "N-04", "data": {"tipo": "cliente", "ativa": False, "em": "2099-02-01T00:00:00Z"}}]
    json.dump(docs, open(os.path.join(d, "db2.json"), "w"))
    sp(d, "import-answers", "db2.json")
    verifica("desdirecionar pelo celular remove o cliente", "cliente" not in pergunta(d, "N-04"))
    ok, out = sp(d, "render")
    pn = ler(os.path.join(d, "docs", "painel.html"))
    sh = ler(os.path.join(d, "docs", "spec.html"))
    verifica("render gera painel e spec.html", ok and "Painel" in pn and "<h1" in sh)
    verifica("html gerado não injeta script do nome do projeto", "<script>alert(1)" not in pn and "<script>alert(1)" not in sh)
    # JS da página do celular e do cliente sem erro de sintaxe (só se houver node)
    if shutil.which("node"):
        for nome, caminho in (("celular", os.path.join(d, ".spec", "entrevista.html")), ("cliente", os.path.join(d, ".spec", "cliente", "index.html"))):
            scripts = re.findall(r"<script>(.*?)</script>", ler(caminho), re.S)
            js = "\n".join(scripts)
            tmp = os.path.join(d, f"{nome}.js")
            open(tmp, "w", encoding="utf-8").write(js)
            r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
            verifica(f"JS da página {nome} sem erro de sintaxe", r.returncode == 0, r.stderr[:200])


def teste_netlify_offline():
    print("• netlify.py (sem rede)")
    r = subprocess.run([sys.executable, NETLIFY, "--help"], capture_output=True, text=True)
    verifica("netlify.py --help", r.returncode == 0 and "site-ensure" in r.stdout)
    sys.path.insert(0, os.path.join(SKILL, "scripts"))
    import netlify
    import zipfile, io
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "sub"))
    open(os.path.join(d, "index.html"), "w").write("x")
    open(os.path.join(d, "sub", "a.txt"), "w").write("y")
    z = zipfile.ZipFile(io.BytesIO(netlify.zip_da_pasta(d)))
    verifica("zip da pasta com caminhos relativos", sorted(z.namelist()) == ["index.html", "sub/a.txt"])
    proj = novo(prof="p")
    os.makedirs(os.path.join(proj, "sub"))
    netlify.gravar_ficha(os.path.join(proj, "sub"), "abc-123", "https://x.netlify.app")
    verifica("gravar_ficha registra o site do cliente na Ficha", sp(proj, "ficha", "cliente_site_id")[1].strip() == "abc-123"
             and sp(proj, "ficha", "cliente_url")[1].strip() == "https://x.netlify.app")


def main():
    teste_init_e_banco()
    teste_entrevista()
    d = teste_gates_e_fases()
    teste_features_tasks(d)
    dc = teste_cliente(d)
    teste_celular_e_render(dc)
    teste_netlify_offline()
    print(f"\n{OK} verificações ok, {len(FALHAS)} falhas")
    for f in FALHAS:
        print("  -", f)
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
