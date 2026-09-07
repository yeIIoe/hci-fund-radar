# -*- coding: utf-8 -*-
"""VIGIA — CAMADA 1 do agente `vigia`. Codigo determinístico, sem IA.

O CASO QUE FEZ ESTE ARQUIVO EXISTIR (07/set/2026, medido, nao suposto)
    A cadeia `macro-direction` roda de 15 em 15 minutos: 96 execucoes por dia. Nas 24 h
    anteriores a este arquivo ela rodou SEIS vezes, e QUATRO delas terminaram como
    CANCELADAS — o trabalho batia no teto de 15 min (a geopolitica levava 8,3 min e o BIS
    5,5 min). Na execucao 34151494850 os passos `sentimento`, `registro imutavel` e o
    `commit` sairam como **skipped**.

    E o GitHub NAO manda e-mail quando uma execucao e CANCELADA. So manda quando ela
    FALHA. O dono nao foi avisado. Os JSON ficaram de 17 a 35 h velhos e a serie de
    snapshots — a unica amostra que torna o backtest de 21/dez possivel — parou.

    Um vigia de CAIXA DE E-MAIL teria ficado calado a semana inteira. E por isso que este
    aqui le o REPOSITORIO (o carimbo DENTRO de cada arquivo) e a API PUBLICA do GitHub
    (as execucoes e os passos), e nao a caixa de entrada de ninguem.

    ⚰️ LEI, ja escrita no cadeia.yml: **nunca leia o mtime.** O `actions/checkout` reescreve
    o mtime de todo arquivo a cada execucao, entao na nuvem ele e sempre "agora". Foi esse
    bug que deixou as fontes uma semana congeladas em 31/ago sem ninguem reclamar. Aqui a
    idade sai SEMPRE do carimbo que esta dentro do arquivo (`gerado_em`, `meta.generated_at`).

O QUE ESTE ARQUIVO FAZ, E O QUE ELE NAO FAZ
    FAZ   mede: idade, contagem de execucoes, passos pulados, frescor, linhas de snapshot.
          Toda aritmetica desta pagina e codigo, reproduzivel, e pode ser recalculada
          identica daqui a tres meses. E a linha dura do ARQUITETURA_AGENTES.md.
    NAO   nao diz a CAUSA. "Estourou o teto", "a fonte caiu", "acabou a cota", "faltou a
          chave de deploy" e JULGAMENTO — e do agente `vigia`, que le esta medicao e nunca
          a recalcula. Ver agentes/vigia/PROMPT.md.

A REGUA DO ALARME (ARQUITETURA_AGENTES.md): todo alarme sai com
    IDENTIFICADOR · ASSUNTO · MEDIDA (o numero) · CONSEQUENCIA em frase inteira.
    Aviso sem consequencia escrita e decoracao, e decoracao ninguem le duas vezes.

SAIDA
    data/agentes/vigia/medicao.json    a medicao crua e completa (camada 1)
    data/agentes/vigia/ultimo.json     o contrato que o site le (preenchido pelo codigo,
                                       com `causa: null` — o agente reescreve por cima)
    data/agentes/vigia/historico.jsonl append-only, uma linha por rodada
    data/agentes/indice.json           so a entrada "vigia" e tocada

USO
    python vigia.py                 mede tudo e grava
    python vigia.py --sem-rede      pula a API do GitHub (util offline; vira limite declarado)
    python vigia.py --janela-h 48   muda a janela das execucoes (padrao 24)
    python vigia.py --estrito       sai com codigo 1 se houver alarme de gravidade alta
    python vigia.py --so-tela       nao grava nada, so imprime

DEPENDENCIAS: nenhuma. So a biblioteca padrao (a casa ja usa urllib, nao requests).
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")
SAIDA_DIR = os.path.join(DATA, "agentes", "vigia")
INDICE = os.path.join(DATA, "agentes", "indice.json")

REPO = "yeIIoe/hci-fund-radar"
API = "https://api.github.com/repos/%s" % REPO

VERSAO_CODIGO = "vigia.py@v1"
# 07/set, refutacao: o selo estava sem acento ("medicao de operacao"), enquanto o
# agentes/vigia/PROMPT.md secao 8 exige a string EXATA acentuada — e o agente nao pode
# corrigi-la, porque o selo nao esta na lista de campos que ele reescreve. O site mostraria
# portugues sem acento para sempre. A string abaixo e a do PROMPT, ao pe da letra.
SELO = "medição de operação — não é leitura de mercado, não vota"

AGORA = datetime.now(timezone.utc)


# =====================================================================================
# 1. OS ARQUIVOS QUE A CADEIA ESCREVE — tolerancia POR ARQUIVO, declarada e PROVISORIA
# =====================================================================================
# ⚠️ TODA tolerancia aqui e PROVISORIA e foi escolhida a mao em 07/set/2026, sem amostra.
#    O criterio foi: "generosa de proposito — o alarme e para dado ESQUECIDO, nao para
#    atraso normal" (a mesma frase do frescor.py). Ela so deixa de ser provisoria quando
#    existir a distribuicao medida do intervalo real entre commits, que ainda nao existe.
#    Nao trate estes numeros como validados; eles estao na saida JSON justamente para
#    poderem ser discutidos e trocados sem mexer no codigo.
#
# campo: o carimbo DENTRO do arquivo. NUNCA o mtime.
ARQUIVOS = [
    # ---------------------------------------------------------------- cadeia de 15 min
    dict(caminho="data/sentimento.json", campos=["gerado_em"], tolerancia_min=90,
         cadeia="macro-direction", cadencia_min=15, gravidade="alta",
         alimenta="a leitura das 8 moedas e dos 28 pares que a tela mostra",
         por_que="e o arquivo que o painel le em primeiro lugar; velho aqui e painel velho"),
    dict(caminho="data/macro_eventos.json", campos=["gerado_em"], tolerancia_min=90,
         cadeia="macro-direction", cadencia_min=15, gravidade="alta",
         alimenta="o calendario interpretado, que alimenta a dimensao de dados (VOTA)",
         por_que="uma das duas dimensoes que ainda votam sai daqui"),
    dict(caminho="data/calendario_resultado.json", campos=["gerado_em"], tolerancia_min=90,
         cadeia="macro-direction", cadencia_min=15, gravidade="alta",
         alimenta="divulgado, consenso e surpresa das 8 moedas (FXStreet)",
         por_que="e a fonte primaria da surpresa; e ela que muda quando o numero sai"),
    dict(caminho="data/bancos_centrais.json", campos=["gerado_em"], tolerancia_min=90,
         cadeia="macro-direction", cadencia_min=15, gravidade="alta",
         alimenta="a dimensao de ciclo (VOTA): ultimo movimento e proxima reuniao",
         por_que="a segunda das duas dimensoes que votam"),
    dict(caminho="data/eua_leitura.json", campos=["gerado_em", "recalculado_em"],
         tolerancia_min=180, cadeia="macro-direction", cadencia_min=15, gravidade="media",
         alimenta="BLS (CPI, NFP, desemprego, salario) e o calendario do FOMC",
         por_que="o script ja tem cache de 60 min por causa da cota de 25/dia do BLS"),
    dict(caminho="data/bc_discursos.json", campos=["gerado_em"], tolerancia_min=180,
         cadeia="macro-direction", cadencia_min=15, gravidade="media",
         alimenta="frases de postura dos bancos centrais — NAO VOTA desde 05/set",
         por_que="e contexto com selo de experimental; atraso nao muda leitura nenhuma"),
    dict(caminho="data/precificacao.json", campos=["gerado_em"], tolerancia_min=180,
         cadeia="macro-direction", cadencia_min=15, gravidade="media",
         alimenta="o que o mercado paga pela proxima decisao — a coluna de comparacao",
         por_que="nao entra no sentimento; e a coluna que o agente `divergencia` usa"),
    dict(caminho="data/noticias.json", campos=["gerado_em"], tolerancia_min=180,
         cadeia="macro-direction", cadencia_min=15, gravidade="baixa",
         alimenta="manchetes por moeda (Google News) — contexto, nao vota",
         por_que="manchete tem peso ZERO na hierarquia de falas; atraso e cosmetico"),
    dict(caminho="data/geopolitica.json", campos=["gerado_em"], tolerancia_min=6 * 60,
         cadeia="macro-direction", cadencia_min=15, gravidade="baixa",
         alimenta="GDELT — NAO VOTA desde 05/set (mede volume de noticia, nao direcao)",
         por_que="o script tem cache de 3 h e carrega a rodada anterior por 24 h"),
    dict(caminho="data/correlacao_juros.json", campos=["gerado_em"], tolerancia_min=30 * 60,
         cadeia="macro-direction", cadencia_min=15, gravidade="baixa",
         alimenta="juro americano x NQ/ES/ouro, 5 anos diarios",
         por_que="dado DIARIO com cache de 20 h dentro do script; 30 h e o cache + folga"),
    # ------------------------------------------------------------- cadeia de 2x por dia
    dict(caminho="data/frescor.json", campos=["gerado_em"], tolerancia_min=18 * 60,
         cadeia="cadeia-2x-dia", cadencia_min=12 * 60, gravidade="alta",
         alimenta="o relatorio da guarda de frescor das fontes brutas",
         por_que="a guarda roda 2x/dia; 18 h ja e um ciclo e meio perdido"),
    dict(caminho="data/yields.json", campos=["meta.generated_at"], tolerancia_min=18 * 60,
         cadeia="cadeia-2x-dia", cadencia_min=12 * 60, gravidade="media",
         alimenta="as curvas oficiais de 2 anos das 8 moedas",
         por_que="curva de juro e D+1 por natureza; 2x/dia basta e 18 h e a folga"),
    dict(caminho="data/fund_snapshot.json", campos=["meta.generated_at"], tolerancia_min=18 * 60,
         cadeia="cadeia-2x-dia", cadencia_min=12 * 60, gravidade="media",
         alimenta="o snapshot do FUND (8 moedas, 28 pares)",
         por_que="mesma cadeia da curva de juro"),
    dict(caminho="data/juros_vs_cambio.json", campos=["gerado_em"], tolerancia_min=30 * 60,
         cadeia="cadeia-2x-dia", cadencia_min=12 * 60, gravidade="baixa",
         alimenta="juro x cambio por par",
         por_que="roda com `|| echo ... segue`: falhar aqui nunca derruba a cadeia"),
    dict(caminho="data/bis_discursos.json", campos=["gerado_em"], tolerancia_min=30 * 60,
         cadeia="cadeia-2x-dia", cadencia_min=12 * 60, gravidade="baixa",
         alimenta="1.319 falas do arquivo do BIS, 2009-2026 — amostra de validacao",
         por_que="e arquivo HISTORICO e o proprio BIS publica com dias de defasagem"),
]

# Passos cujo `skipped` e a assinatura do estouro de teto — a lista que importa.
PASSOS_ESSENCIAIS = [
    ("sentimento", "sem ele a leitura das 8 moedas e dos 28 pares nao e recalculada"),
    ("registro imutavel", "sem ele a serie de snapshots perde a linha daquele instante"),
    ("snapshot", "sem ele a serie de snapshots perde a linha daquele instante"),
    ("publica o essencial", "sem ele nada do que foi medido chega ao site"),
    ("commit", "sem ele nada do que foi medido chega ao site"),
]

# Passos de infraestrutura do proprio runner — pulo aqui e ruido, nao alarme.
PASSOS_IGNORAR = ("post run ", "complete job", "set up job", "post job cleanup")

CONCLUSOES_RUINS = ("failure", "cancelled", "timed_out", "startup_failure", "stale")


# =====================================================================================
# 2. FERRAMENTAS
# =====================================================================================
def _p(rel: str) -> str:
    return os.path.join(AQUI, rel.replace("/", os.sep))


def _cava(d, caminho_pontos):
    """Le `meta.generated_at` de um dicionario aninhado. Devolve None se faltar."""
    atual = d
    for parte in caminho_pontos.split("."):
        if not isinstance(atual, dict) or parte not in atual:
            return None
        atual = atual[parte]
    return atual


def _data_de(texto):
    """Converte carimbo em datetime UTC. Devolve (dt, era_ingenuo, erro).

    ⚠️ ARMADILHA DE RELOGIO (lapide L-H5 da casa): frescor.py e juros_vs_cambio.py gravam
    `datetime.now()` SEM fuso. No runner do GitHub isso e UTC; na maquina do Eduardo e BRT
    (UTC-3). Tratamos ingenuo como UTC e MARCAMOS. Se der idade negativa, e porque o
    arquivo foi escrito em BRT: a idade sai 0 e a observacao vai junto, nunca um alarme.
    """
    if not isinstance(texto, str) or not texto.strip():
        return None, False, "carimbo ausente ou nao e texto"
    t = texto.strip().replace("Z", "+00:00")
    for tentativa in (t, t.replace(" ", "T")):
        try:
            dt = datetime.fromisoformat(tentativa)
        except ValueError:
            continue
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc), True, None
        return dt.astimezone(timezone.utc), False, None
    return None, False, "formato de carimbo nao reconhecido: %r" % texto[:40]


def _hm(minutos):
    """420 -> '7 h 00 min'. Frase, nao numero solto."""
    if minutos is None:
        return "—"
    m = int(round(minutos))
    if m < 60:
        return "%d min" % m
    return "%d h %02d min" % (m // 60, m % 60)


def _le_json(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "arquivo nao existe no repositorio"
    except Exception as e:
        return None, "nao deu para ler (%s: %s)" % (type(e).__name__, e)


# =====================================================================================
# 3. CHECAGEM 1 — IDADE, pelo carimbo DENTRO do arquivo
# =====================================================================================
def checa_idade():
    linhas = []
    for cfg in ARQUIVOS:
        caminho = _p(cfg["caminho"])
        item = {
            "arquivo": cfg["caminho"], "cadeia": cfg["cadeia"],
            "cadencia_min": cfg["cadencia_min"],
            "tolerancia_min": cfg["tolerancia_min"],
            "tolerancia_texto": _hm(cfg["tolerancia_min"]),
            "tolerancia_estado": "PROVISORIA — escolhida a mao em 07/set, sem amostra",
            "por_que_esta_tolerancia": cfg["por_que"],
            "alimenta": cfg["alimenta"], "gravidade_se_velho": cfg["gravidade"],
            "campo_lido": None, "carimbo_literal": None, "carimbo_utc": None,
            "idade_min": None, "idade_texto": None, "carimbo_sem_fuso": False,
            "estado": None, "observacao": None,
        }
        dado, erro = _le_json(caminho)
        if dado is None:
            item["estado"] = "sem dado"
            item["observacao"] = erro
            linhas.append(item)
            continue

        bruto = campo = None
        for c in cfg["campos"]:
            v = _cava(dado, c)
            if isinstance(v, str) and v.strip():
                bruto, campo = v, c
                break
        if bruto is None:
            item["estado"] = "sem dado"
            item["observacao"] = ("nenhum dos campos de carimbo existe no arquivo (%s) — "
                                  "e proibido cair no mtime" % ", ".join(cfg["campos"]))
            linhas.append(item)
            continue

        dt, ingenuo, erro = _data_de(bruto)
        item.update(campo_lido=campo, carimbo_literal=bruto, carimbo_sem_fuso=ingenuo)
        if dt is None:
            item["estado"] = "sem dado"
            item["observacao"] = erro
            linhas.append(item)
            continue

        idade = (AGORA - dt).total_seconds() / 60.0
        if idade < 0:
            item["observacao"] = (
                "o carimbo esta no futuro em %s. O arquivo grava a hora SEM fuso e foi "
                "escrito fora do runner (BRT = UTC-3). Idade tratada como 0; isto e "
                "observacao de relogio, nao alarme." % _hm(-idade))
            idade = 0.0
        elif ingenuo:
            item["observacao"] = ("carimbo sem fuso: lido como UTC. Se este arquivo foi "
                                  "escrito na maquina do dono (BRT), a idade esta "
                                  "superestimada em ate 3 h.")
        item["carimbo_utc"] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        item["idade_min"] = round(idade, 1)
        item["idade_texto"] = _hm(idade)
        item["estado"] = "velho" if idade > cfg["tolerancia_min"] else "ok"
        linhas.append(item)
    return linhas


# =====================================================================================
# 4. CRON — quantas execucoes DEVERIAM ter acontecido na janela
# =====================================================================================
def _campo_cron(spec, lo, hi):
    vals = set()
    for parte in str(spec).split(","):
        parte = parte.strip()
        passo = 1
        if "/" in parte:
            parte, p = parte.split("/", 1)
            passo = int(p)
        if parte in ("*", ""):
            a, b = lo, hi
        elif "-" in parte:
            x, y = parte.split("-", 1)
            a, b = int(x), int(y)
        else:
            a = b = int(parte)
        vals.update(range(a, b + 1, passo))
    return vals


def _casa_cron(cron, dt):
    """Semantica POSIX, inclusive a regra do OU entre dia-do-mes e dia-da-semana."""
    partes = cron.split()
    if len(partes) != 5:
        return False
    mi, ho, dm, mo, ds = partes
    if dt.minute not in _campo_cron(mi, 0, 59):
        return False
    if dt.hour not in _campo_cron(ho, 0, 23):
        return False
    if dt.month not in _campo_cron(mo, 1, 12):
        return False
    dm_restrito, ds_restrito = dm.strip() != "*", ds.strip() != "*"
    dm_ok = dt.day in _campo_cron(dm, 1, 31)
    semana = (dt.weekday() + 1) % 7          # cron: 0 = domingo
    conj = {0 if x == 7 else x for x in _campo_cron(ds, 0, 7)}
    ds_ok = semana in conj
    if dm_restrito and ds_restrito:
        return dm_ok or ds_ok
    if dm_restrito:
        return dm_ok
    if ds_restrito:
        return ds_ok
    return True


def le_workflows():
    """Le nome, crons e teto de tempo de cada workflow SEM depender de pyyaml.

    Regex e nao parser de YAML de proposito: a cadeia nao instala pyyaml, e o vigia nao
    pode ser a peca que quebra por falta de dependencia. O limite disto esta declarado
    na saida (`limites`).
    """
    saida = {}
    for caminho in sorted(glob.glob(os.path.join(AQUI, ".github", "workflows", "*.yml"))):
        texto = open(caminho, encoding="utf-8", errors="replace").read()
        rel = ".github/workflows/" + os.path.basename(caminho)
        m = re.search(r"(?m)^name:\s*(.+?)\s*$", texto)
        crons = re.findall(r"(?m)^\s*-\s*cron:\s*[\"']([^\"']+)[\"']", texto)
        tetos = [int(x) for x in re.findall(r"(?m)^\s*timeout-minutes:\s*(\d+)", texto)]
        saida[rel] = {
            "path": rel,
            "nome": m.group(1).strip() if m else os.path.basename(caminho),
            "crons": crons,
            "teto_min": min(tetos) if tetos else None,
            "tem_agenda": bool(crons),
        }
    return saida


def esperadas_na_janela(crons, inicio, fim):
    """Conta os minutos da janela em que ALGUM cron dispara. Minuto contado uma vez."""
    if not crons:
        return 0
    n = 0
    t = inicio.replace(second=0, microsecond=0)
    while t <= fim:
        if any(_casa_cron(c, t) for c in crons):
            n += 1
        t += timedelta(minutes=1)
    return n


# =====================================================================================
# 5. CHECAGEM 2 e 3 — as execucoes e os passos PULADOS, pela API publica do GitHub
# =====================================================================================
def _http_json(url):
    cab = {"User-Agent": "hci-vigia/1.0", "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        cab["Authorization"] = "Bearer " + tok
    req = urllib.request.Request(url, headers=cab)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def busca_execucoes(inicio, max_paginas=6):
    """Puxa as execucoes ate passar do inicio da janela. Devolve (lista, erro)."""
    todas, erro = [], None
    try:
        for pagina in range(1, max_paginas + 1):
            d = _http_json("%s/actions/runs?per_page=100&page=%d" % (API, pagina))
            runs = d.get("workflow_runs", [])
            if not runs:
                break
            todas.extend(runs)
            ultimo, _, e = _data_de(runs[-1].get("created_at", ""))
            if e or ultimo is None or ultimo < inicio:
                break
    except urllib.error.HTTPError as e:
        corpo = ""
        try:
            corpo = e.read().decode("utf-8", "replace")[:180]
        except Exception:
            pass
        erro = "API do GitHub devolveu HTTP %s (%s). %s" % (
            e.code, e.reason,
            "Limite de 60 chamadas/hora sem chave: a medicao de execucoes fica em branco "
            "nesta rodada." if e.code in (403, 429) else corpo)
    except Exception as e:
        erro = "nao deu para falar com a API do GitHub (%s: %s)" % (type(e).__name__, e)
    return todas, erro


def checa_execucoes(janela_h):
    fim, inicio = AGORA, AGORA - timedelta(hours=janela_h)
    wfs = le_workflows()
    runs, erro = busca_execucoes(inicio)

    por_wf = {}
    for rel, wf in wfs.items():
        por_wf[rel] = {
            "workflow": wf["nome"], "path": rel, "crons": wf["crons"],
            "teto_min": wf["teto_min"], "tem_agenda": wf["tem_agenda"],
            "deveria": esperadas_na_janela(wf["crons"], inicio, fim),
            "rodou_agendadas": 0, "rodou_outras": 0,
            "sucesso": 0, "falhou": 0, "cancelou": 0, "estourou_teto": 0,
            "em_andamento": 0, "ruins": [],
        }

    if erro is None:
        for r in runs:
            dt, _, e = _data_de(r.get("created_at", ""))
            if e or dt is None or dt < inicio or dt > fim:
                continue
            rel = r.get("path") or ""
            if rel not in por_wf:
                por_wf[rel] = {"workflow": r.get("name"), "path": rel, "crons": [],
                               "teto_min": None, "tem_agenda": False, "deveria": 0,
                               "rodou_agendadas": 0, "rodou_outras": 0, "sucesso": 0,
                               "falhou": 0, "cancelou": 0, "estourou_teto": 0,
                               "em_andamento": 0, "ruins": []}
            b = por_wf[rel]
            if r.get("event") == "schedule":
                b["rodou_agendadas"] += 1
            else:
                b["rodou_outras"] += 1
            conc = r.get("conclusion")
            if r.get("status") != "completed":
                b["em_andamento"] += 1
            elif conc == "success":
                b["sucesso"] += 1
            elif conc == "cancelled":
                b["cancelou"] += 1          # ⚠️ CANCELADO CONTA COMO FALHA. E o modo silencioso.
            elif conc == "timed_out":
                b["estourou_teto"] += 1
            elif conc in CONCLUSOES_RUINS:
                b["falhou"] += 1
            if conc in CONCLUSOES_RUINS:
                b["ruins"].append({
                    "id": r.get("id"), "conclusao": conc, "evento": r.get("event"),
                    "criado_em": r.get("created_at"), "url": r.get("html_url"),
                    "tentativa": r.get("run_attempt"),
                })

    lista = sorted(por_wf.values(),
                   key=lambda x: (-(x["deveria"] or 0), x["workflow"] or ""))
    return {
        "janela_h": janela_h,
        "janela_de": inicio.strftime("%Y-%m-%dT%H:%MZ"),
        "janela_ate": fim.strftime("%Y-%m-%dT%H:%MZ"),
        "fonte": "%s/actions/runs (API publica, sem chave)" % API,
        "erro": erro,
        "workflows": lista,
    }


def checa_passos_pulados(execucoes, teto_consultas=8):
    """Busca os jobs das execucoes ruins e procura passos `skipped` — a assinatura do teto.

    Cada consulta e uma chamada a API sem chave (60/hora). Teto de 8 de proposito: melhor
    medir as 8 mais recentes com folga do que estourar a cota e nao medir nenhuma.
    """
    alvos = []
    for wf in execucoes["workflows"]:
        for r in wf["ruins"]:
            alvos.append((wf, r))
    alvos.sort(key=lambda x: x[1].get("criado_em") or "", reverse=True)
    alvos = alvos[:teto_consultas]

    achados, erros = [], []
    for wf, r in alvos:
        try:
            d = _http_json("%s/actions/runs/%s/jobs" % (API, r["id"]))
        except Exception as e:
            erros.append("execucao %s: %s" % (r["id"], e))
            continue
        for j in d.get("jobs", []):
            passos = j.get("steps") or []
            pulados, ultimo_ok, cancelado_em = [], None, None
            for s in passos:
                nome = (s.get("name") or "").strip()
                if any(nome.lower().startswith(x) or x in nome.lower()
                       for x in PASSOS_IGNORAR):
                    continue
                if s.get("conclusion") == "skipped":
                    pulados.append(nome)
                elif s.get("conclusion") == "success":
                    ultimo_ok = nome
                elif s.get("conclusion") in ("cancelled", "failure", "timed_out"):
                    cancelado_em = cancelado_em or nome
            ini, _, _e1 = _data_de(j.get("started_at") or "")
            fim, _, _e2 = _data_de(j.get("completed_at") or "")
            dur = round((fim - ini).total_seconds() / 60.0, 1) if (ini and fim) else None
            essenciais = []
            for nome in pulados:
                for chave, custo in PASSOS_ESSENCIAIS:
                    if chave in nome.lower():
                        essenciais.append({"passo": nome, "custo": custo})
                        break
            teto = wf["teto_min"]
            bateu = bool(teto and dur and dur >= teto * 0.90)
            achados.append({
                "workflow": wf["workflow"], "execucao_id": r["id"],
                "conclusao_execucao": r["conclusao"], "criado_em": r["criado_em"],
                "url": r["url"], "job": j.get("name"),
                "duracao_min": dur, "teto_min": teto,
                "bateu_no_teto": bateu,
                "parou_no_passo": cancelado_em,
                "ultimo_passo_ok": ultimo_ok,
                "passos_pulados": pulados,
                "essenciais_pulados": essenciais,
            })
    return {"consultadas": len(alvos), "teto_consultas": teto_consultas,
            "achados": achados, "erros": erros}


# =====================================================================================
# 6. CHECAGEM 4 — o frescor que o painel ja calcula
# =====================================================================================
def checa_frescor():
    out = {"sentimento": None, "guarda": None}

    d, erro = _le_json(_p("data/sentimento.json"))
    if d is None:
        out["sentimento"] = {"estado": "sem dado", "observacao": erro}
    else:
        f = d.get("frescor") or {}
        out["sentimento"] = {
            "atraso_min": f.get("atraso_min"),
            "atraso_texto": f.get("atraso_texto"),
            "estado": f.get("estado"),
            "bloqueia_leitura": f.get("bloqueia_leitura"),
            "fonte_mais_velha": f.get("fonte_mais_velha"),
            "limiares_provisorios": f.get("limiares_provisorios"),
            "texto_do_painel": f.get("texto"),
            "fontes_que_votam_atrasadas": [
                {"fonte": x.get("fonte"), "atraso_min": x.get("atraso_min"),
                 "alimenta": x.get("alimenta")}
                for x in (f.get("fontes") or [])
                if x.get("vota") and isinstance(x.get("atraso_min"), (int, float))
                and x.get("atraso_min") > ((f.get("limiares_provisorios") or {})
                                           .get("atrasado_min") or 45)
            ],
        }

    g, erro = _le_json(_p("data/frescor.json"))
    if g is None:
        out["guarda"] = {"estado": "sem dado", "observacao": erro}
    else:
        dt, ingenuo, _ = _data_de(g.get("gerado_em") or "")
        idade = max(0.0, (AGORA - dt).total_seconds() / 60.0) if dt else None
        out["guarda"] = {
            "gerado_em": g.get("gerado_em"),
            "carimbo_sem_fuso": ingenuo,
            "idade_min": round(idade, 1) if idade is not None else None,
            "idade_texto": _hm(idade),
            "n_fontes": len(g.get("fontes") or []),
            "fora_da_tolerancia": g.get("fora_da_tolerancia") or [],
            "sem_data_legivel": [x.get("arquivo") for x in (g.get("fontes") or [])
                                 if x.get("ultima_data") is None],
        }
    return out


# =====================================================================================
# 7. CHECAGEM 5 — a serie de snapshots (a amostra do backtest de 21/dez)
# =====================================================================================
def checa_snapshots(dias=10):
    dirn = _p("data/snapshots")
    if not os.path.isdir(dirn):
        return {"estado": "sem dado", "observacao": "data/snapshots nao existe",
                "por_dia": [], "ultimo_dia": None, "linhas_hoje": 0}
    por_dia = []
    for caminho in sorted(glob.glob(os.path.join(dirn, "*.jsonl"))):
        nome = os.path.basename(caminho)
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.jsonl$", nome)
        if not m:
            continue
        try:
            n = sum(1 for linha in open(caminho, encoding="utf-8", errors="replace")
                    if linha.strip())
        except Exception:
            n = None
        por_dia.append({"dia": m.group(1), "linhas": n})
    por_dia.sort(key=lambda x: x["dia"])
    recentes = por_dia[-dias:]
    com_linha = [x for x in por_dia if (x["linhas"] or 0) > 0]
    ultimo = com_linha[-1]["dia"] if com_linha else None
    hoje = AGORA.strftime("%Y-%m-%d")
    linhas_hoje = next((x["linhas"] for x in por_dia if x["dia"] == hoje), 0) or 0
    idade_dias = None
    if ultimo:
        idade_dias = (AGORA.date() - datetime.strptime(ultimo, "%Y-%m-%d").date()).days
    return {
        "estado": "ok" if ultimo else "sem dado",
        "por_dia": recentes,
        "dias_com_linha": len(com_linha),
        "ultimo_dia_com_linha": ultimo,
        "dias_desde_ultima_linha": idade_dias,
        "linhas_hoje": linhas_hoje,
        "hoje_utc": hoje,
        "hora_utc": AGORA.hour,
        "para_que_serve": ("e a UNICA amostra que torna o backtest de 21/dez possivel: a "
                           "leitura de hoje nao pode ser reconstruida amanha, porque a "
                           "FXStreet e buscada ao vivo e as manchetes tem janela de 72 h"),
    }


# =====================================================================================
# 8. OS ALARMES — IDENTIFICADOR · ASSUNTO · MEDIDA · CONSEQUENCIA em frase inteira
# =====================================================================================
def alarme(ident, assunto, medida, consequencia, gravidade, numeros,
           trecho=None, fonte=None, ok=False):
    return {
        "identificador": ident,
        "assunto": assunto,
        "medida": medida,
        "consequencia": consequencia,
        "gravidade": gravidade,            # alta | media | baixa | ok
        "estado": "ok" if ok else "alarme",
        "natureza": "MEDIDO",
        "numeros_citados": numeros,
        "trecho": trecho,
        "fonte": fonte or {},
        "causa": None,                     # ⚠️ so o AGENTE preenche. Codigo nao adivinha causa.
        "causa_confianca": None,
    }


def monta_alarmes(idades, execucoes, pulados, frescor, snapshots, janela_h):
    A = []

    # ---------------------------------------------------------------- 1. IDADE
    for it in idades:
        nome = it["arquivo"]
        base = {"idade_min": it["idade_min"], "tolerancia_min": it["tolerancia_min"],
                "carimbo_utc": it["carimbo_utc"], "campo_lido": it["campo_lido"],
                "cadencia_esperada_min": it["cadencia_min"]}
        fonte = {"titulo": "%s (campo %s, lido DENTRO do arquivo — nunca o mtime)"
                           % (nome, it["campo_lido"]),
                 "link": nome, "quando": it["carimbo_utc"]}
        if it["estado"] == "sem dado":
            A.append(alarme(
                "IDADE-SEM-CARIMBO/" + nome, "carimbo de geracao ilegivel", it["observacao"],
                ("Sem carimbo dentro do arquivo nao da para saber a idade de %s, e a unica "
                 "alternativa seria o mtime — que o checkout reescreve a cada execucao e foi "
                 "exatamente o bug que deixou as fontes uma semana congeladas em 31/ago. "
                 "Enquanto isso durar, este arquivo nao e vigiado por ninguem." % nome),
                "media", base, trecho=it["carimbo_literal"], fonte=fonte))
        elif it["estado"] == "velho":
            A.append(alarme(
                "IDADE/" + nome, "arquivo da cadeia %s alem da tolerancia" % it["cadeia"],
                "%s de idade contra tolerancia de %s (carimbo %s)"
                % (it["idade_texto"], it["tolerancia_texto"], it["carimbo_utc"]),
                ("O painel esta publicando %s como se fosse atual, e ele alimenta %s. Quem "
                 "abrir a tela agora le com cara de novo um numero de %s — o erro que a casa "
                 "ja cometeu em 31/ago e prometeu nao repetir. A cadeia %s deveria reescrever "
                 "este arquivo a cada %s."
                 % (nome, it["alimenta"], it["carimbo_utc"], it["cadeia"],
                    _hm(it["cadencia_min"]))),
                it["gravidade_se_velho"], base, trecho=it["carimbo_literal"], fonte=fonte))
        else:
            A.append(alarme(
                "IDADE/" + nome, "arquivo dentro da tolerancia",
                "%s de idade contra tolerancia de %s" % (it["idade_texto"],
                                                         it["tolerancia_texto"]),
                ("Nada a fazer: %s esta fresco e alimenta %s com dado do carimbo %s."
                 % (nome, it["alimenta"], it["carimbo_utc"])),
                "ok", base, trecho=it["carimbo_literal"], fonte=fonte, ok=True))

    # ------------------------------------------------------- 2. EXECUCOES e CANCELAMENTOS
    if execucoes["erro"]:
        A.append(alarme(
            "EXEC-SEM-MEDICAO", "a API do GitHub nao respondeu nesta rodada",
            execucoes["erro"],
            ("Sem a API nao da para saber quantas execucoes rodaram nem quantas foram "
             "canceladas, e cancelamento e justamente o modo que nao gera e-mail. Esta "
             "rodada do vigia mede idade e snapshot, mas NAO mede execucao: trate a "
             "ausencia de alarme de execucao como ausencia de medicao, nao como saude."),
            "media", {"janela_h": janela_h}, fonte={"titulo": execucoes["fonte"],
                                                    "link": execucoes["fonte"],
                                                    "quando": execucoes["janela_ate"]}))
    else:
        for wf in execucoes["workflows"]:
            if not wf["tem_agenda"]:
                continue
            dev, rod = wf["deveria"], wf["rodou_agendadas"]
            pct = round(100.0 * rod / dev, 1) if dev else None
            ruins = wf["cancelou"] + wf["falhou"] + wf["estourou_teto"]
            nums = {"deveria": dev, "rodou_agendadas": rod, "rodou_por_outro_evento":
                    wf["rodou_outras"], "pct_do_previsto": pct, "sucesso": wf["sucesso"],
                    "cancelada": wf["cancelou"], "falhou": wf["falhou"],
                    "estourou_teto": wf["estourou_teto"], "janela_h": janela_h,
                    "cron": wf["crons"], "teto_min": wf["teto_min"]}
            fonte = {"titulo": "API publica do GitHub Actions, janela de %d h" % janela_h,
                     "link": "%s/actions/runs" % API, "quando": execucoes["janela_ate"]}

            if dev and pct is not None and pct < 60:
                A.append(alarme(
                    "EXEC/" + wf["workflow"], "a cadeia rodou muito menos do que devia",
                    "%d execucoes agendadas em %d h contra %d previstas pelo cron (%s%%)"
                    % (rod, janela_h, dev, pct),
                    ("Cada execucao de `%s` que nao acontece e uma janela de ate %s em que "
                     "o que ela mede nao e atualizado e o commit que publicaria o resultado "
                     "nao e feito. Foi exatamente esta conta que deu 6 de 96 em 07/set, "
                     "quando o painel ficou 17 h velho sem ninguem ser avisado."
                     % (wf["workflow"], _hm(int(round(24 * 60 / dev)) if dev else 0))),
                    "alta", nums, fonte=fonte))
            elif dev and pct is not None and pct < 90:
                A.append(alarme(
                    "EXEC/" + wf["workflow"], "a cadeia rodou menos do que devia",
                    "%d de %d execucoes previstas em %d h (%s%%)" % (rod, dev, janela_h, pct),
                    ("O GitHub declara que o `schedule` atrasa e que algumas execucoes na "
                     "fila sao descartadas em periodo de carga; ate 90%% isso e o ruido "
                     "conhecido do plano gratuito. Abaixo disso deixa de ser ruido. "
                     "Consequencia pratica: a leitura publicada pode estar ate %s atrasada "
                     "sem que nada fique vermelho."
                     % (_hm(2 * int(round(24 * 60 / dev))) if dev else "—")),
                    "media", nums, fonte=fonte))
            elif dev:
                A.append(alarme(
                    "EXEC/" + wf["workflow"], "cadencia dentro do previsto",
                    "%d de %d execucoes previstas em %d h (%s%%)" % (rod, dev, janela_h, pct),
                    "Nada a fazer: a cadeia %s manteve a cadencia na janela medida."
                    % wf["workflow"],
                    "ok", nums, fonte=fonte, ok=True))

            if ruins:
                A.append(alarme(
                    "CANC/" + wf["workflow"],
                    "execucoes terminadas em cancelled, failure ou timed_out",
                    "%d execucoes ruins em %d h: %d canceladas, %d com falha, %d por estouro "
                    "de teto" % (ruins, janela_h, wf["cancelou"], wf["falhou"],
                                 wf["estourou_teto"]),
                    ("CANCELADO NAO GERA E-MAIL DO GITHUB — so `failure` gera. Foram %d "
                     "cancelamentos nesta janela, e cada um deles e uma rodada que morreu em "
                     "silencio, com os passos finais pulados e sem commit. E por isso que "
                     "este vigia le a API e nao a caixa de entrada."
                     % wf["cancelou"]),
                    "alta" if wf["cancelou"] or wf["estourou_teto"] else "media",
                    nums, fonte=fonte,
                    trecho=json.dumps(wf["ruins"][:4], ensure_ascii=False)))

    # ---------------------------------------------------------------- 3. PASSOS PULADOS
    # Agrupado por workflow + passo onde parou: quatro execucoes que morreram no MESMO
    # passo sao UM problema com quatro ocorrencias, nao quatro problemas. Alarme repetido
    # quatro vezes e a forma mais rapida de ensinar alguem a ignorar o alarme.
    grupos = {}
    for a in pulados["achados"]:
        if not a["passos_pulados"]:
            continue
        chave = (a["workflow"], a["parou_no_passo"] or a["ultimo_passo_ok"] or "?")
        grupos.setdefault(chave, []).append(a)

    for (wfnome, parou), itens in grupos.items():
        itens.sort(key=lambda x: x["criado_em"] or "", reverse=True)
        ids = [x["execucao_id"] for x in itens]
        essenciais, custos = [], []
        for x in itens:
            for e in x["essenciais_pulados"]:
                if e["passo"] not in essenciais:
                    essenciais.append(e["passo"])
                    custos.append(e["custo"])
        duracoes = [x["duracao_min"] for x in itens if x["duracao_min"] is not None]
        teto = next((x["teto_min"] for x in itens if x["teto_min"]), None)
        bateu = [x for x in itens if x["bateu_no_teto"]]
        assinatura = ""
        if bateu:
            assinatura = (" Em %d delas o trabalho passou de 90%% do teto (duracao de %s min "
                          "contra teto de %s min declarado no workflow): e a assinatura do "
                          "ESTOURO DE TETO, o mesmo padrao da execucao 34151494850 de 07/set."
                          % (len(bateu),
                             "/".join(str(d) for d in sorted(set(duracoes))), teto))
        A.append(alarme(
            "PULO/%s/%s" % (wfnome, re.sub(r"[^a-z0-9]+", "-", parou.lower()).strip("-")),
            "passos pulados por causa de um passo anterior",
            "%d execucao(oes) de `%s` pararam em '%s' e pularam %d passo(s), sendo %d "
            "essenciais (%s). Execucoes: %s"
            % (len(itens), wfnome, parou, len(itens[0]["passos_pulados"]), len(essenciais),
               ", ".join(essenciais) or "nenhum", ", ".join(str(i) for i in ids[:6])),
            ("A execucao parou em '%s' e tudo o que vinha depois foi pulado, em %d rodadas "
             "desta janela.%s Consequencia: %s. Enquanto o passo de commit nao roda, nada do "
             "que foi medido chega ao site, e o painel continua servindo o arquivo da rodada "
             "anterior com carimbo antigo — o que e correto, e por isso ninguem percebe."
             % (parou, len(itens), assinatura,
                "; ".join(custos) or "nenhum passo essencial na lista")),
            "alta" if essenciais else "media",
            {"n_execucoes": len(itens), "execucoes": ids, "parou_no_passo": parou,
             "duracoes_min": duracoes, "teto_min": teto,
             "n_bateram_no_teto": len(bateu),
             "passos_pulados": itens[0]["passos_pulados"],
             "essenciais_pulados": essenciais},
            trecho=", ".join(itens[0]["passos_pulados"]),
            fonte={"titulo": "jobs das execucoes %s de `%s`"
                             % (", ".join(str(i) for i in ids[:6]), wfnome),
                   "link": itens[0]["url"], "quando": itens[0]["criado_em"]}))
    for e in pulados["erros"]:
        A.append(alarme("PULO-SEM-MEDICAO", "nao deu para ler os jobs de uma execucao", e,
                        ("Sem os jobs nao da para saber se sentimento, snapshot e commit "
                         "foram pulados — que e a assinatura do estouro de teto. Esta "
                         "execucao fica sem diagnostico nesta rodada."),
                        "baixa", {}))

    # ---------------------------------------------------------------- 4. FRESCOR
    fs = frescor["sentimento"] or {}
    if fs.get("estado") == "sem dado":
        A.append(alarme("FRESCOR-SENTIMENTO", "o painel nao conseguiu declarar o proprio frescor",
                        fs.get("observacao"),
                        ("Sem o bloco `frescor` do sentimento.json a tela nao sabe dizer ha "
                         "quanto tempo a leitura foi sincronizada, e o aviso de dado velho "
                         "que o painel mostra sozinho deixa de existir."),
                        "media", {}))
    else:
        nums = {"atraso_min": fs.get("atraso_min"), "estado": fs.get("estado"),
                "bloqueia_leitura": fs.get("bloqueia_leitura"),
                "limiares_provisorios": fs.get("limiares_provisorios"),
                "fonte_mais_velha": fs.get("fonte_mais_velha")}
        ruim = bool(fs.get("bloqueia_leitura")) or fs.get("estado") not in ("ok", None)
        A.append(alarme(
            "FRESCOR-SENTIMENTO",
            "o frescor que o proprio painel calcula",
            "atraso de %s, estado '%s', bloqueia_leitura=%s (fonte mais velha: %s)"
            % (fs.get("atraso_texto"), fs.get("estado"), fs.get("bloqueia_leitura"),
               fs.get("fonte_mais_velha")),
            (("O proprio painel esta declarando a leitura atrasada. Enquanto "
              "bloqueia_leitura for verdadeiro, nenhum julgamento da camada 2 pode sair com "
              "confianca acima de baixa, e a tela precisa mostrar a idade ao lado do numero.")
             if ruim else
             ("Nada a fazer: o painel declara a leitura sincronizada ha %s, e as duas "
              "dimensoes que votam estao dentro dos limiares provisorios."
              % fs.get("atraso_texto"))),
            "alta" if fs.get("bloqueia_leitura") else ("media" if ruim else "ok"),
            nums, ok=not ruim,
            fonte={"titulo": "data/sentimento.json, bloco frescor",
                   "link": "data/sentimento.json", "quando": fs.get("atraso_texto")}))

    fg = frescor["guarda"] or {}
    if fg.get("estado") == "sem dado":
        A.append(alarme("FRESCOR-GUARDA", "o relatorio da guarda de frescor nao existe",
                        fg.get("observacao"),
                        ("data/frescor.json e o unico lugar onde o motivo de uma falha da "
                         "guarda fica visivel sem login no GitHub. Sem ele, quando a guarda "
                         "falhar, o dono ve a Action vermelha e nao sabe qual fonte quebrou."),
                        "media", {}))
    else:
        fora = fg.get("fora_da_tolerancia") or []
        A.append(alarme(
            "FRESCOR-GUARDA", "as fontes brutas contra a guarda de frescor",
            "%d fontes fora da tolerancia (%s); relatorio com %s de idade sobre %d fontes"
            % (len(fora), ", ".join(fora) if fora else "nenhuma", fg.get("idade_texto"),
               fg.get("n_fontes") or 0),
            (("A guarda ja apontou %d fonte(s) vencida(s). Quando isso acontece a cadeia "
              "2x/dia publica so o relatorio e falha de proposito — os dados velhos NAO sao "
              "publicados. Se a Action nao ficou vermelha, o problema e a guarda, nao a fonte."
              % len(fora)) if fora else
             ("Nada a fazer: as %d fontes brutas estao dentro da tolerancia declarada em "
              "frescor.py." % (fg.get("n_fontes") or 0))),
            "alta" if fora else "ok",
            {"n_fora": len(fora), "fora": fora, "idade_min": fg.get("idade_min"),
             "n_fontes": fg.get("n_fontes"),
             "sem_data_legivel": fg.get("sem_data_legivel")},
            ok=not fora,
            fonte={"titulo": "data/frescor.json (guarda de frescor da cadeia 2x/dia)",
                   "link": "data/frescor.json", "quando": fg.get("gerado_em")}))

    # ---------------------------------------------------------------- 5. SNAPSHOTS
    s = snapshots
    nums = {"ultimo_dia_com_linha": s.get("ultimo_dia_com_linha"),
            "dias_desde_ultima_linha": s.get("dias_desde_ultima_linha"),
            "linhas_hoje": s.get("linhas_hoje"), "hora_utc": s.get("hora_utc"),
            "linhas_por_dia": s.get("por_dia")}
    fonte_s = {"titulo": "data/snapshots/*.jsonl (registro imutavel, append-only)",
               "link": "data/snapshots/", "quando": s.get("ultimo_dia_com_linha")}
    if s.get("estado") == "sem dado":
        A.append(alarme("SNAP-SEM-SERIE", "a serie de snapshots nao existe",
                        s.get("observacao"),
                        ("Sem a serie, o backtest de 21/dez nao tem amostra nenhuma: %s."
                         % s["para_que_serve"]),
                        "alta", nums, fonte=fonte_s))
    elif (s.get("dias_desde_ultima_linha") or 0) >= 2:
        A.append(alarme(
            "SNAP-PAROU", "a serie de snapshots parou de crescer",
            "ultima linha em %s, ha %d dias; hoje (%s) tem %d linhas"
            % (s["ultimo_dia_com_linha"], s["dias_desde_ultima_linha"], s["hoje_utc"],
               s["linhas_hoje"]),
            ("Cada dia sem linha e um dia que o backtest de 21/dez perde para sempre, porque "
             "%s. Quando o passo `registro imutavel` e pulado por estouro de teto, e esta a "
             "serie que para junto — e ela e a unica coisa da cadeia que nao pode ser "
             "recuperada depois." % s["para_que_serve"]),
            "alta", nums, fonte=fonte_s))
    elif s.get("linhas_hoje", 0) == 0 and s.get("hora_utc", 0) >= 12:
        A.append(alarme(
            "SNAP-DIA-VAZIO", "o dia de hoje ainda nao tem nenhuma linha de snapshot",
            "0 linhas em %s as %02dh UTC; a ultima linha foi em %s"
            % (s["hoje_utc"], s["hora_utc"], s["ultimo_dia_com_linha"]),
            ("A primeira leitura do dia deveria ter gravado uma linha ha horas. Se o dia "
             "fechar vazio, o backtest de 21/dez perde este pregao, e ele nao pode ser "
             "reconstruido depois: %s." % s["para_que_serve"]),
            "media", nums, fonte=fonte_s))
    else:
        A.append(alarme(
            "SNAP", "a serie de snapshots do backtest",
            "%d linhas hoje (%s); ultima linha em %s; %d dias com linha na serie"
            % (s["linhas_hoje"], s["hoje_utc"], s["ultimo_dia_com_linha"],
               s["dias_com_linha"]),
            "Nada a fazer: a serie continua crescendo e a amostra do backtest de 21/dez "
            "segue viva.",
            "ok", nums, ok=True, fonte=fonte_s))

    return A


# =====================================================================================
# 9. O CONTRATO DE SAIDA
# =====================================================================================
LIMITES_FIXOS = [
    "Este arquivo e a CAMADA 1 do vigia: so medicao. Ele NAO diz a causa de nada. "
    "'Estourou o teto', 'a fonte caiu', 'acabou a cota do BLS' e 'faltou a chave de deploy' "
    "sao JULGAMENTO, e quem os escreve e o agente `vigia` (campo causa), lendo esta medicao "
    "sem nunca recalcula-la.",
    "TODA tolerancia de idade e PROVISORIA: foi escolhida a mao em 07/set/2026, sem amostra "
    "da distribuicao real do intervalo entre commits. Nao ha pre-registro por tras delas.",
    "A idade sai SEMPRE do carimbo DENTRO do arquivo. O mtime e proibido: o actions/checkout "
    "o reescreve a cada execucao, e foi esse bug que deixou as fontes uma semana congeladas "
    "em 31/ago/2026 sem ninguem reclamar.",
    "frescor.json e juros_vs_cambio.json gravam a hora SEM fuso. Aqui sao lidos como UTC e "
    "marcados com carimbo_sem_fuso=true; se tiverem sido escritos na maquina do dono (BRT), "
    "a idade esta superestimada em ate 3 h. E por isso que a tolerancia deles e generosa.",
    "O 'deveria' das execucoes vem do cron declarado no proprio workflow, contado minuto a "
    "minuto na janela. O GitHub documenta que o schedule atrasa e que execucoes na fila podem "
    "ser descartadas em periodo de carga: 100%% nunca e o esperado, e por isso o alarme so "
    "sobe de gravidade abaixo de 60%%.",
    "Os workflows sao lidos por expressao regular, nao por parser de YAML: a cadeia nao "
    "instala pyyaml e o vigia nao pode ser a peca que quebra por falta de dependencia. "
    "Cron em formato exotico pode nao ser lido — e sairia como 'deveria: 0'.",
    "NEM TODO CANCELAMENTO E FALHA: o macro_direction.yml declara "
    "`concurrency: cancel-in-progress: true`, entao uma execucao nova cancela a anterior DE "
    "PROPOSITO. Estouro de teto tem duracao colada no teto (bateu_no_teto=true); "
    "sobreposicao e curta e tem execucao nova logo em seguida. O codigo mede a duracao e o "
    "teto; separar os dois casos e julgamento, e e do agente.",
    "A API do GitHub e consultada SEM chave (60 chamadas/hora por IP). Os jobs sao buscados "
    "so das 8 execucoes ruins mais recentes; se houver mais, as antigas ficam sem "
    "diagnostico de passo pulado nesta rodada.",
    "DESVIO DECLARADO do contrato: a linha do historico.jsonl guarda o contrato SEM a prosa "
    "(motivo, consequencia, fonte, trecho e limites), porque essa prosa e texto fixo "
    "reconstruivel pela versao do prompt e faria o arquivo append-only passar de 160 MB por "
    "ano. Todos os NUMEROS ficam na linha; a medicao crua fica em medicao.json, que e "
    "sobrescrito a cada rodada.",
    "O vigia mede a operacao, nao o mercado. Nada aqui vota no sentimento, e nada aqui e "
    "recomendacao de investimento.",
]


def monta_contrato(alarmes, idades, execucoes, pulados, frescor, snapshots, janela_h):
    rodada = "vigia-%s" % AGORA.strftime("%Y%m%dT%H%MZ")
    julgamentos = []
    for a in alarmes:
        julgamentos.append({
            "chave": a["identificador"],
            "veredito": ("OK" if a["estado"] == "ok" else "ALARME"),
            "confianca": "alta",   # aritmetica de codigo: reproduzivel, nao e opiniao
            "motivo": "%s — %s. %s" % (a["assunto"], a["medida"], a["consequencia"]),
            "trecho": a["trecho"],
            "numeros_citados": a["numeros_citados"],
            "fonte": a["fonte"],
            "vota": False,
            "selo": SELO,
            # campos proprios do vigia (o site le estes para montar a lista de alarmes)
            "assunto": a["assunto"],
            "medida": a["medida"],
            "consequencia": a["consequencia"],
            "gravidade": a["gravidade"],
            "natureza": a["natureza"],
            "causa": a["causa"],
            "causa_confianca": a["causa_confianca"],
        })

    nao_julgados = []
    if execucoes["erro"]:
        nao_julgados.append({"chave": "execucoes-do-github",
                             "porque": execucoes["erro"]})
    for it in idades:
        if it["estado"] == "sem dado":
            nao_julgados.append({"chave": "IDADE/" + it["arquivo"],
                                 "porque": it["observacao"]})

    limites = list(LIMITES_FIXOS)
    if execucoes["erro"]:
        limites.insert(0, "NESTA RODADA a medicao de execucoes NAO aconteceu: %s. Ausencia "
                          "de alarme de execucao aqui e ausencia de medicao, nao saude."
                          % execucoes["erro"])

    altos = [a for a in alarmes if a["estado"] == "alarme" and a["gravidade"] == "alta"]
    medios = [a for a in alarmes if a["estado"] == "alarme" and a["gravidade"] == "media"]
    baixos = [a for a in alarmes if a["estado"] == "alarme" and a["gravidade"] == "baixa"]

    return {
        "agente": "vigia",
        "versao_prompt": VERSAO_CODIGO,
        "escrito_por": ("vigia.py (camada 1) — o agente `vigia` ainda nao passou nesta "
                        "rodada; os campos `causa` e `resumo_pt` estao vazios de proposito"),
        "gerado_em": AGORA.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rodada_id": rodada,
        "resumo_pt": None,          # ⚠️ o AGENTE escreve. Codigo nao escreve texto para o site.
        "placar": {
            "alarmes_alta": len(altos), "alarmes_media": len(medios),
            "alarmes_baixa": len(baixos),
            "checagens_ok": len([a for a in alarmes if a["estado"] == "ok"]),
            "estado_geral": ("vermelho" if altos else ("amarelo" if medios or baixos
                                                       else "verde")),
        },
        "entradas": {
            "arquivo": "data/*.json + data/snapshots/*.jsonl + API do GitHub Actions",
            "gerado_em": AGORA.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "n_itens": len(alarmes),
            "detalhe": [
                {"arquivo": it["arquivo"], "gerado_em": it["carimbo_utc"],
                 "campo_lido": it["campo_lido"], "idade_min": it["idade_min"]}
                for it in idades
            ] + [
                {"arquivo": "%s/actions/runs" % API,
                 "gerado_em": execucoes["janela_ate"],
                 "n_itens": sum(w["rodou_agendadas"] + w["rodou_outras"]
                                for w in execucoes["workflows"])},
                {"arquivo": "data/snapshots/*.jsonl",
                 "gerado_em": snapshots.get("ultimo_dia_com_linha"),
                 "n_itens": snapshots.get("linhas_hoje")},
            ],
        },
        "julgamentos": julgamentos,
        "nao_julgados": nao_julgados,
        "limites": limites,
        # A medicao crua NAO mora aqui de proposito. O historico.jsonl guarda uma copia
        # desta estrutura por rodada; embutir a medicao inteira faria cada linha passar de
        # 50 kB, e 12 rodadas por dia viram centenas de megabytes de JSON por ano num
        # arquivo append-only versionado no git. A casa ja tem lei sobre isso (coleta
        # grande grava comprimida). Os numeros que interessam para calibrar as tolerancias
        # depois estao todos em `julgamentos[].numeros_citados`, que fica na linha.
        "medicao_arquivo": "data/agentes/vigia/medicao.json",
        "medicao_resumo": {
            "janela_h": janela_h,
            "arquivos_medidos": len(idades),
            "arquivos_velhos": [i["arquivo"] for i in idades if i["estado"] == "velho"],
            "arquivos_sem_carimbo": [i["arquivo"] for i in idades
                                     if i["estado"] == "sem dado"],
            "execucoes_medidas": execucoes["erro"] is None,
            "snapshot_ultimo_dia": snapshots.get("ultimo_dia_com_linha"),
            "snapshot_linhas_hoje": snapshots.get("linhas_hoje"),
        },
        "_medicao": {          # so para a tela e para o gravador; retirado do historico
            "janela_h": janela_h,
            "idade": idades,
            "execucoes": execucoes,
            "passos_pulados": pulados,
            "frescor": frescor,
            "snapshots": snapshots,
        },
    }


def grava(contrato):
    os.makedirs(SAIDA_DIR, exist_ok=True)

    medicao = dict(contrato["_medicao"])
    medicao.update({"gerado_em": contrato["gerado_em"],
                    "rodada_id": contrato["rodada_id"],
                    "versao_codigo": VERSAO_CODIGO})
    with open(os.path.join(SAIDA_DIR, "medicao.json"), "w", encoding="utf-8") as f:
        json.dump(medicao, f, ensure_ascii=False, indent=1)

    publico = {k: v for k, v in contrato.items() if k != "_medicao"}
    with open(os.path.join(SAIDA_DIR, "ultimo.json"), "w", encoding="utf-8") as f:
        json.dump(publico, f, ensure_ascii=False, indent=1)

    # append-only: uma linha por rodada. Se o agente rodar depois, ele acrescenta a LINHA
    # DELE com o mesmo rodada_id — nunca reescreve esta.
    with open(os.path.join(SAIDA_DIR, "historico.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(linha_historico(publico), ensure_ascii=False) + "\n")


def linha_historico(publico):
    """A linha do historico: o contrato SEM a prosa, e com os numeros inteiros.

    ⚠️ DESVIO DECLARADO do contrato ("uma linha por rodada, mesmo conteudo"): a prosa dos
    julgamentos (`motivo`, `consequencia`, `fonte`, `trecho`) e TEXTO FIXO, reconstruivel
    a partir de `assunto` + `medida` + a versao do prompt. Guardando-a, cada linha passava
    de 38 kB; a 12 rodadas por dia isso e mais de 160 MB por ano num arquivo append-only
    versionado no git, e a casa ja tem lei sobre isso (coleta grande grava comprimida:
    1,36 GB de JSON viraram 33 MB de parquet).
    O que a linha guarda por inteiro e o que nao se reconstroi depois: os NUMEROS
    (`numeros_citados`), o placar, a causa nomeada pelo agente e o `resumo_pt`. E essa a
    serie que um dia permite medir as tolerancias provisorias contra a distribuicao real.
    """
    enxuto = {k: v for k, v in publico.items() if k not in ("julgamentos", "limites")}
    enxuto["julgamentos"] = [
        {"chave": j["chave"], "veredito": j["veredito"], "gravidade": j["gravidade"],
         "assunto": j["assunto"], "medida": j["medida"],
         "causa": j["causa"], "causa_confianca": j["causa_confianca"],
         "numeros_citados": j["numeros_citados"]}
        for j in publico.get("julgamentos", [])
    ]
    enxuto["n_limites"] = len(publico.get("limites", []))
    enxuto["prosa_omitida"] = (
        "motivo, consequencia, fonte, trecho e limites nao entram na linha do historico: "
        "sao texto fixo do prompt e do codigo, reconstruiveis por versao_prompt. Os numeros "
        "estao todos aqui. Ver ultimo.json da rodada corrente e medicao.json.")
    return enxuto

    idx, _ = _le_json(INDICE)
    if not isinstance(idx, dict) or not isinstance(idx.get("agentes"), list):
        idx = {"agentes": []}
    minha = {"nome": "vigia", "versao_prompt": VERSAO_CODIGO,
             "ultima_rodada": contrato["gerado_em"],
             "estado": "ok"}
    outros = [a for a in idx["agentes"] if a.get("nome") != "vigia"]
    idx["agentes"] = sorted(outros + [minha], key=lambda a: a.get("nome") or "")
    os.makedirs(os.path.dirname(INDICE), exist_ok=True)
    with open(INDICE, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)


# =====================================================================================
# 10. A TELA
# =====================================================================================
def imprime(contrato):
    c = contrato
    print("=" * 96)
    print("VIGIA — a cadeia rodou? o dado esta vivo? (camada 1, so medicao)")
    print("rodada %s   janela %d h   estado %s"
          % (c["rodada_id"], c["_medicao"]["janela_h"], c["placar"]["estado_geral"].upper()))
    print("=" * 96)

    print("\n1) IDADE — carimbo DENTRO do arquivo (nunca o mtime)")
    print("   %-34s %-21s %10s %10s  %s"
          % ("arquivo", "carimbo (UTC)", "idade", "tolerancia", "estado"))
    print("   " + "-" * 88)
    for it in c["_medicao"]["idade"]:
        print("   %-34s %-21s %10s %10s  %s"
              % (it["arquivo"][:34], it["carimbo_utc"] or "—", it["idade_texto"] or "—",
                 it["tolerancia_texto"], it["estado"].upper()))

    print("\n2) EXECUCOES — API publica do GitHub")
    ex = c["_medicao"]["execucoes"]
    if ex["erro"]:
        print("   NAO MEDIDO: %s" % ex["erro"])
    else:
        print("   %-22s %8s %8s %7s %7s %7s %7s %7s"
              % ("workflow", "deveria", "agendad", "avulsas", "ok", "canc.", "falha", "teto"))
        print("   " + "-" * 86)
        for w in ex["workflows"]:
            if not w["tem_agenda"] and not (w["rodou_agendadas"] + w["rodou_outras"]):
                continue
            print("   %-22s %8s %8d %7d %7d %7d %7d %7d"
                  % (str(w["workflow"])[:22], w["deveria"] or "—", w["rodou_agendadas"],
                     w["rodou_outras"], w["sucesso"], w["cancelou"], w["falhou"],
                     w["estourou_teto"]))
        print("   (agendadas = disparadas pelo cron, que e o que se compara com 'deveria'; "
              "avulsas = push ou disparo manual)")

    print("\n3) PASSOS PULADOS")
    ps = c["_medicao"]["passos_pulados"]
    if not ps["achados"]:
        print("   nenhuma execucao ruim consultada nesta janela")
    for a in ps["achados"]:
        print("   %s %s: parou em '%s' apos %s min (teto %s) — pulados: %s"
              % (a["workflow"], a["execucao_id"], a["parou_no_passo"], a["duracao_min"],
                 a["teto_min"], ", ".join(a["passos_pulados"]) or "nenhum"))
    if ps["consultadas"] >= ps["teto_consultas"]:
        print("   (teto de %d consultas atingido: pode haver execucao ruim mais antiga sem "
              "diagnostico nesta rodada)" % ps["teto_consultas"])

    print("\n4) FRESCOR")
    fs = c["_medicao"]["frescor"]["sentimento"] or {}
    fg = c["_medicao"]["frescor"]["guarda"] or {}
    print("   sentimento.json: atraso %s, estado %s, bloqueia_leitura=%s"
          % (fs.get("atraso_texto"), fs.get("estado"), fs.get("bloqueia_leitura")))
    print("   frescor.json:    %d fonte(s) fora da tolerancia %s"
          % (len(fg.get("fora_da_tolerancia") or []),
             (fg.get("fora_da_tolerancia") or "")))

    print("\n5) SNAPSHOTS")
    sn = c["_medicao"]["snapshots"]
    print("   ultima linha em %s (ha %s dias); hoje %s linhas"
          % (sn.get("ultimo_dia_com_linha"), sn.get("dias_desde_ultima_linha"),
             sn.get("linhas_hoje")))
    print("   linhas por dia: %s"
          % ", ".join("%s=%s" % (x["dia"], x["linhas"]) for x in sn.get("por_dia") or []))

    print("\n" + "=" * 96)
    alarmes = [j for j in c["julgamentos"] if j["veredito"] == "ALARME"]
    if not alarmes:
        print("SEM ALARME. %d checagens passaram." % c["placar"]["checagens_ok"])
    else:
        print("%d ALARME(S): %d alta, %d media, %d baixa"
              % (len(alarmes), c["placar"]["alarmes_alta"], c["placar"]["alarmes_media"],
                 c["placar"]["alarmes_baixa"]))
        print("=" * 96)
        ordem = {"alta": 0, "media": 1, "baixa": 2}
        for j in sorted(alarmes, key=lambda x: ordem.get(x["gravidade"], 9)):
            print("\n  [%s] %s" % (j["gravidade"].upper(), j["chave"]))
            print("      assunto      %s" % j["assunto"])
            print("      medida       %s" % j["medida"])
            print("      consequencia %s" % j["consequencia"])
    print()


# =====================================================================================
def main():
    argv = sys.argv[1:]
    janela_h = 24
    if "--janela-h" in argv:
        try:
            janela_h = int(argv[argv.index("--janela-h") + 1])
        except Exception:
            print("--janela-h precisa de um numero. Usando 24.")
    sem_rede = "--sem-rede" in argv
    estrito = "--estrito" in argv
    so_tela = "--so-tela" in argv

    idades = checa_idade()
    if sem_rede:
        execucoes = {"janela_h": janela_h,
                     "janela_de": (AGORA - timedelta(hours=janela_h)).strftime("%Y-%m-%dT%H:%MZ"),
                     "janela_ate": AGORA.strftime("%Y-%m-%dT%H:%MZ"),
                     "fonte": "%s/actions/runs" % API,
                     "erro": "--sem-rede: a API do GitHub nao foi consultada nesta rodada",
                     "workflows": []}
        pulados = {"consultadas": 0, "teto_consultas": 0, "achados": [], "erros": []}
    else:
        execucoes = checa_execucoes(janela_h)
        pulados = (checa_passos_pulados(execucoes) if not execucoes["erro"]
                   else {"consultadas": 0, "teto_consultas": 0, "achados": [], "erros": []})
    frescor = checa_frescor()
    snapshots = checa_snapshots()

    alarmes = monta_alarmes(idades, execucoes, pulados, frescor, snapshots, janela_h)
    contrato = monta_contrato(alarmes, idades, execucoes, pulados, frescor, snapshots,
                              janela_h)
    imprime(contrato)

    if not so_tela:
        grava(contrato)
        print("gravado: data/agentes/vigia/ultimo.json, medicao.json, historico.jsonl")
        print("indice:  data/agentes/indice.json (so a entrada 'vigia')")

    if estrito and contrato["placar"]["alarmes_alta"] > 0:
        print("\n--estrito: %d alarme(s) de gravidade ALTA — saindo com codigo 1."
              % contrato["placar"]["alarmes_alta"])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
