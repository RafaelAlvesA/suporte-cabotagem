#!/usr/bin/env python3
"""
Atualiza o painel de chamados do Suporte Cabotagem.

Dois modos, definidos no config.ini:
  modo = api  -> busca os chamados direto na API REST do GLPI
  modo = csv  -> usa o CSV mais recente de uma pasta (export manual)

Em ambos os casos o script reescreve os dados dentro do index.html
(mantendo layout, marca e funcionalidades) e, se configurado, publica no GitHub.

Uso:
    python atualizar_painel.py            # usa o modo do config.ini
    python atualizar_painel.py --csv      # força modo csv
    python atualizar_painel.py --testar   # só testa a conexão com o GLPI
"""
import configparser, csv, html, json, os, re, subprocess, sys, unicodedata
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
CFG = configparser.ConfigParser()
CFG.read(BASE / "config.ini", encoding="utf-8")

def cfg(secao, chave, padrao=""):
    try: return CFG.get(secao, chave).strip()
    except Exception: return padrao

# ------------------------------------------------------------------ util
def sem_acento(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()

MAPST = {"Em atendimento (atribuído)": "Em análise",
         "Em atendimento (planejado)": "Com dev"}

REGRAS = [("CIOT / ANTT", r"\bciot\b|\bantt\b"),
 ("Cancelamento / reversão", r"cancel|anula|revert|estorn|inutiliz|desmarcar"),
 ("Integração / EDI / SAP", r"integra|notfis|\bedi\b|doccob|\bsap\b|json|webservice|nftp|absor|booking|\bsvm\b|hypercare"),
 ("Faturamento e valores", r"fatura|frete|pedagio|valor|tarifa|cobran|debit|tribut|imposto|icms|difal|aliquota|rateio|cofins"),
 ("Emissão fiscal", r"emiss|emitid|emitir|dacte|mdf-?e|ct-?e|ctes|nf-?e|nfs-?e|sefaz|rejeic|averba|danfe|\brps\b|nota fiscal|notas fiscais"),
 ("Relatórios e extração", r"relatorio|extrair|extrac|exportar|\bbi\b|afrmm|control mercante|imprimir"),
 ("XML / arquivo", r"\bxml\b|\bpdf\b|planilha|arquivo"),
 ("Carga travada / etapas", r"travad|travando|retid|preso|nao avanc|etapa|fluxo"),
 ("Cadastro / configuração", r"cadastr|configur|parametr|layout|permiss|acesso|perfil|liberacao de ip"),
 ("Dados divergentes", r"divergen|duplicad|duplicidade|incorret|indevid|errad|vazio|faltando|inconsist"),
 ("Dúvida / orientação", r"duvida|como fazer|orienta|informacao sobre")]

def tema_de(titulo, descricao, modulo, categoria):
    a = sem_acento(f"{titulo} {modulo}")
    for nome, rx in REGRAS:
        if re.search(rx, a): return nome
    b = sem_acento(descricao)[:600]
    for nome, rx in REGRAS:
        if re.search(rx, b): return nome
    return "Dúvida / orientação" if "N1" in categoria else "Não classificado"

def pdata(v):
    v = (v or "").strip()
    for f in ("%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try: return datetime.strptime(v, f)
        except ValueError: pass
    return None

def fmt(d): return d.strftime("%Y-%m-%d %H:%M") if d else None

def sem_html(s):
    if not s: return ""
    s = re.sub(r"<[^>]+>", " ", str(s))
    s = html.unescape(s)
    s = re.sub(r"https?://\S+", "", s)
    return re.sub(r"\s+", " ", s).strip()[:700]

def monta(linha):
    """Recebe um dicionário com os nomes de coluna do export e devolve o registro do painel."""
    g = lambda k: (linha.get(k) or "").strip()
    desc0 = g("Descrição")
    m = re.search(r"URL DA OCORRÊNCIA: (\S+)", desc0)
    modulo = ""
    if m:
        m2 = re.search(r"#([^/\s?]+)", m.group(1))
        if m2: modulo = m2.group(1)
    ver = re.search(r"VERSÃO QUE OCORRE O PROBLEMA: ([^\n]+)", desc0)
    inc = re.search(r"ID INTERNO: ([^\n]+)", desc0)
    dsc = re.search(r"10\) DESCRIÇÃO:([\s\S]*)", desc0) or re.search(r"DESCRIÇÃO:([\s\S]*)", desc0)
    cat = g("Categoria"); partes = [p.strip() for p in cat.split(">")]
    if partes and partes[0].startswith("Cabotagem"):
        inst = partes[1] if len(partes) > 1 else "—"
        niv = partes[2] if len(partes) > 2 else "(sem nível)"
    else:
        inst, niv = "Outros", (partes[-1] if partes else "")
    ab, so = pdata(g("Data de abertura")), pdata(g("Data da solução"))
    pz, ua = pdata(g("Tempo para solução + Progresso")), pdata(g("Última atualização"))
    tit = re.sub(r"^.*\| ", "", g("Título")).strip()
    corpo = (dsc.group(1).strip()[:800] if dsc else "")
    st = g("Status")
    return {
        "id": g("ID"), "titulo": tit, "tipo": g("Tipo"), "status": MAPST.get(st, st),
        "aberto": so is None, "prioridade": g("Prioridade"),
        "tecnico": g("Atribuído - Técnico") or "Não atribuído",
        "requerente": re.sub(r"\s+", " ", g("Requerente - Requerente")),
        "instancia": inst, "nivel": niv, "modulo": modulo,
        "causa": g("Plug-ins - Fluxo Cabotagem - Análise de Causa") or "Não preenchida",
        "justificativa": sem_html(g("Plug-ins - Fluxo Cabotagem - Justificativa de Causa")),
        "tema": tema_de(tit, corpo, modulo, cat),
        "versao": ver.group(1).strip() if ver else "", "inc": inc.group(1).strip() if inc else "",
        "origem": g("Origem da requisição"),
        "abertura": fmt(ab), "solucao": fmt(so), "prazo": fmt(pz), "atualizacao": fmt(ua),
        "horas": round((so - ab).total_seconds() / 3600, 2) if (so and ab) else None,
        "sla": (so <= pz) if (so and pz) else None,
        "sla_nome": g("SLA - SLA Tempo para solução"), "descricao": corpo,
    }

# ------------------------------------------------------------------ origem: CSV
def ler_csv(caminho):
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(caminho, encoding=enc, newline="") as fh:
                linhas = list(csv.DictReader(fh, delimiter=";"))
            break
        except UnicodeDecodeError:
            continue
    return [monta(l) for l in linhas if (l.get("ID") or "").strip() and (l.get("Título") or "").strip()]

def csv_mais_recente(pasta, padrao="glpi*.csv"):
    arqs = sorted(Path(pasta).glob(padrao), key=lambda p: p.stat().st_mtime, reverse=True)
    if not arqs: raise SystemExit(f"nenhum arquivo {padrao} em {pasta}")
    return arqs[0]

# ------------------------------------------------------------------ origem: API
def api_sessao():
    import requests
    url = cfg("glpi", "url").rstrip("/")
    r = requests.get(f"{url}/initSession",
                     headers={"App-Token": cfg("glpi", "app_token"),
                              "Authorization": "user_token " + cfg("glpi", "user_token")},
                     timeout=30)
    r.raise_for_status()
    return url, r.json()["session_token"]

def api_campos(url, tok):
    import requests
    r = requests.get(f"{url}/listSearchOptions/Ticket",
                     headers={"App-Token": cfg("glpi", "app_token"), "Session-Token": tok}, timeout=60)
    r.raise_for_status()
    mapa = {}
    for cid, info in r.json().items():
        if isinstance(info, dict) and "name" in info and str(cid).isdigit():
            mapa.setdefault(sem_acento(info["name"]), str(cid))
            pai = info.get("table") or ""
            mapa.setdefault(sem_acento(f"{pai} {info['name']}"), str(cid))
    return mapa

# nomes que o painel precisa -> como aparecem no GLPI
DESEJADOS = ["ID", "Título", "Entidade", "Tipo", "Status", "Categoria", "Data de abertura",
             "Data da solução", "Tempo para solução + Progresso", "Atribuído - Grupo técnico",
             "Atribuído - Técnico", "Prioridade", "Requerente - Requerente", "Origem da requisição",
             "Última atualização", "SLA - SLA Tempo para solução", "Descrição",
             "Plug-ins - Fluxo Cabotagem - Análise de Causa",
             "Plug-ins - Fluxo Cabotagem - Justificativa de Causa"]

def api_buscar():
    import requests
    url, tok = api_sessao()
    campos = api_campos(url, tok)
    ids, rotulos = [], {}
    for nome in DESEJADOS:
        curto = sem_acento(nome.split(" - ")[-1])
        cid = campos.get(sem_acento(nome)) or campos.get(curto)
        if cid: ids.append(cid); rotulos[cid] = nome
    grupo = cfg("glpi", "grupo_tecnico", "Suporte Cabotagem")
    cid_grupo = campos.get(sem_acento("Grupo técnico")) or campos.get(sem_acento("Atribuído - Grupo técnico"))
    params = [("range", "0-999"), ("giveItems", "1")]
    for i in ids: params.append(("forcedisplay[]", i))
    if cid_grupo and grupo:
        params += [("criteria[0][field]", cid_grupo), ("criteria[0][searchtype]", "contains"),
                   ("criteria[0][value]", grupo)]
    saida, inicio = [], 0
    while True:
        p = [(k, v) for k, v in params if k != "range"] + [("range", f"{inicio}-{inicio+199}")]
        r = requests.get(f"{url}/search/Ticket", params=p,
                         headers={"App-Token": cfg("glpi", "app_token"), "Session-Token": tok}, timeout=120)
        if r.status_code == 401: raise SystemExit("token recusado pelo GLPI (401)")
        r.raise_for_status()
        dados = r.json().get("data", []) or []
        for item in dados:
            linha = {}
            for cid, valor in item.items():
                nome = rotulos.get(str(cid))
                if nome: linha[nome] = "" if valor is None else str(valor)
            saida.append(linha)
        total = r.json().get("totalcount", len(saida))
        inicio += 200
        if inicio >= total or not dados: break
    requests.get(f"{url}/killSession",
                 headers={"App-Token": cfg("glpi", "app_token"), "Session-Token": tok}, timeout=30)
    return [monta(l) for l in saida if (l.get("ID") or "").strip()]

# ------------------------------------------------------------------ escrita
def gravar(registros, destino):
    if not registros: raise SystemExit("nenhum chamado retornado — nada foi gravado")
    ref = max([d for r in registros for d in (pdata(r["abertura"]), pdata(r["solucao"]), pdata(r["atualizacao"])) if d])
    dados = json.dumps({"ref": fmt(ref), "rows": registros}, ensure_ascii=False)
    alvo = Path(destino)
    txt = alvo.read_text(encoding="utf-8")
    novo, n = re.subn(r"let RAW = \{.*?\}; let DATA", lambda m: "let RAW = " + dados + "; let DATA",
                      txt, count=1, flags=re.S)
    if n != 1: raise SystemExit(f"não encontrei o bloco de dados em {alvo}")
    alvo.write_text(novo, encoding="utf-8")
    return len(registros), sum(1 for r in registros if r["aberto"]), fmt(ref)

def publicar(pasta_repo, mensagem):
    for cmd in (["git", "add", "index.html"],
                ["git", "commit", "-m", mensagem],
                ["git", "push"]):
        r = subprocess.run(cmd, cwd=pasta_repo, capture_output=True, text=True)
        if r.returncode and "nothing to commit" not in (r.stdout + r.stderr):
            print("  git:", (r.stdout + r.stderr).strip()[:300]); return False
    return True

# ------------------------------------------------------------------ main
def main():
    modo = "csv" if "--csv" in sys.argv else cfg("geral", "modo", "csv")
    if "--testar" in sys.argv:
        url, tok = api_sessao()
        campos = api_campos(url, tok)
        print("conexão OK com", url)
        print("campos reconhecidos:", sum(1 for n in DESEJADOS
              if campos.get(sem_acento(n)) or campos.get(sem_acento(n.split(' - ')[-1]))), "de", len(DESEJADOS))
        return
    if modo == "api":
        print("buscando na API do GLPI…"); regs = api_buscar()
    else:
        arq = csv_mais_recente(cfg("csv", "pasta", str(Path.home() / "Downloads")),
                               cfg("csv", "padrao", "glpi*.csv"))
        print("lendo", arq.name); regs = ler_csv(arq)
    destino = cfg("geral", "arquivo_painel", str(BASE.parent / "index.html"))
    total, abertos, ref = gravar(regs, destino)
    print(f"painel atualizado: {total} chamados, {abertos} em aberto, referência {ref}")
    repo = cfg("github", "pasta_repo", "")
    if repo and cfg("github", "publicar", "nao").lower() in ("sim", "true", "1"):
        ok = publicar(repo, f"Atualiza painel — {ref}")
        print("publicado no GitHub" if ok else "falha ao publicar (veja a mensagem acima)")

if __name__ == "__main__":
    main()
