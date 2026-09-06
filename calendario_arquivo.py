# -*- coding: utf-8 -*-
"""ARQUIVADOR POINT-IN-TIME DO CALENDARIO — o consenso com carimbo de data.

O PORQUE (leia antes de mexer)
    A FXStreet entrega uma janela ROLANTE de aproximadamente 42 dias. Medido em
    06/set/2026: `data/calendario_resultado.json` continha 233 eventos indo de
    2026-09-03 a 2026-09-13. O que sai da janela SOME. O consenso de um evento
    existe enquanto a janela o cobre e depois nao volta mais: nao ha endpoint de
    historico, nao ha "as of", nao ha reprocessamento.

    Sem consenso com carimbo de data nao existe backtest honesto do lado
    fundamental. Surpresa = divulgado - consenso. Daqui a tres meses, sem este
    arquivo, ninguem sabe o que o mercado esperava hoje — e a tentacao vira
    reconstruir o consenso a posteriori, que e exatamente o furo que matou o
    backtest do Deep Value (sem point-in-time, sem sobreviventes, sem teste).

    Cada hora sem este arquivador e dado que nao volta. Por isso ele e barato de
    rodar (append-only, so grava o que mudou) e caro de burlar (hash por linha
    mais encadeamento por arquivo).

O QUE ELE FAZ
    Le `data/calendario_resultado.json` (fonte primaria: tem o `id` estavel da
    FXStreet) e `data/macro_eventos.json` (enriquecimento) e ACRESCENTA linhas em
    `data/calendario_arquivo/AAAA-MM.jsonl`. Um arquivo por MES DA LEITURA,
    append-only: linha antiga nunca e reescrita, arquivo de mes passado nunca e
    reaberto para escrita.

REGRA ANTI-ENTULHO
    So grava quando um dos campos de VALOR mudou (consenso, anterior, divulgado,
    revisado) em relacao a ULTIMA linha daquele evento. Reexecucao sem mudanca
    nao grava nada — e o que permite rodar a cada 15 minutos sem inchar o repo.

    Sub-regra honesta: valor conhecido que volta NULO nao conta como mudanca (a
    fonte piscando nao pode apagar o que ja foi observado). Se a linha for gravada
    por outro motivo, o campo sai como a fonte deu (nulo) e o nome dele aparece em
    `perdeu`, para quem le decidir.

INTEGRIDADE
    `hash_valores` = sha256 dos campos de valor + id do evento, 12 hex.
    `hash_cadeia`  = sha256 encadeado com a linha anterior DO MESMO ARQUIVO.
    Editar uma linha antiga quebra a cadeia de todas as seguintes. `--verifica`
    recalcula tudo e aponta a primeira linha divergente.

LEITURA PARA BACKTEST
    `reconstroi(data_iso)` devolve o que se sabia naquele instante. Ele NAO abre
    nenhuma linha com `quando_li_utc` posterior a data pedida — e por construcao:
    filtra linha a linha e conta quantas ignorou, para o numero poder ser exibido.

LEIS DA CASA RESPEITADAS
    Campo sem fonte e nulo com motivo escrito, nunca estimativa disfarcada.
    `titulo_pt` sai NULO hoje porque nenhuma das duas fontes publica titulo em
    portugues (a traducao vive no navegador, em ui_lang.js, que este script nao
    toca). Quando algum coletor passar a emitir o campo, ele e arquivado sozinho.
    Nada aqui entra no sentimento: isto e arquivo, nao leitura.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = os.path.dirname(os.path.abspath(__file__))
DIR_DADOS = os.path.join(RAIZ, "data")
ARQ_CALENDARIO = os.path.join(DIR_DADOS, "calendario_resultado.json")
ARQ_EVENTOS = os.path.join(DIR_DADOS, "macro_eventos.json")
DIR_ARQUIVO = os.path.join(DIR_DADOS, "calendario_arquivo")

# Os quatro campos que definem "mudou alguma coisa". O resto (titulo, impacto,
# unidade, pais) e identidade/metadado e nao dispara linha nova sozinho.
CAMPOS_VALOR = ("consenso", "anterior", "divulgado", "revisado")

# Chaves alternativas onde um titulo em portugues poderia aparecer no futuro.
CHAVES_TITULO_PT = ("titulo_pt", "title_pt", "titulo_traduzido", "titulo_ptbr")


# ----------------------------------------------------------------------------
# utilitarios
# ----------------------------------------------------------------------------
def agora_utc() -> str:
    """Instante da leitura, em ISO-8601 UTC. Um so por execucao."""
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _le_json(caminho: str):
    """Le um JSON do disco. Devolve (dado, motivo_da_falha)."""
    if not os.path.exists(caminho):
        return None, "arquivo nao existe"
    try:
        with io.open(caminho, "r", encoding="utf-8") as f:
            return json.load(f), None
    except (ValueError, OSError) as e:
        return None, "%s: %s" % (type(e).__name__, str(e)[:120])


def _num(v):
    """Normaliza um valor da fonte SEM inventar.

    Numero continua numero. Texto vazio (ou '-') vira nulo. Texto que e numero
    vira numero. Texto que nao e numero fica como texto, aparado — a fonte que
    responde por ele.
    """
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    if s == "" or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return s


def _texto(v):
    """Texto aparado; vazio vira nulo."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def chave_derivada(titulo, moeda, quando_utc) -> str:
    """Chave estavel para evento SEM id na fonte: titulo + moeda + quando_utc.

    Sai como 'd-' + 16 hex para nunca colidir com o formato de id da FXStreet
    (UUID). O titulo entra normalizado em minusculas e com espacos colapsados,
    porque a fonte oscila em maiusculas e espaco duplo.
    """
    t = " ".join(str(titulo or "").lower().split())
    m = str(moeda or "").upper().strip()
    q = str(quando_utc or "").strip()
    bruto = "|".join([t, m, q])
    return "d-" + hashlib.sha256(bruto.encode("utf-8")).hexdigest()[:16]


def hash_valores(evento_id, valores: dict) -> str:
    """sha256 curto (12 hex) do id + campos de valor. E o que prova que a linha
    nao foi editada depois."""
    corpo = json.dumps([evento_id] + [valores.get(c) for c in CAMPOS_VALOR],
                       ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(corpo.encode("utf-8")).hexdigest()[:12]


def hash_cadeia(anterior: str, nome_arquivo: str, seq: int, h_val: str,
                quando_li_utc: str, evento_id: str) -> str:
    """Encadeia a linha na anterior DO MESMO ARQUIVO. A primeira linha de cada
    arquivo usa o nome do arquivo como semente (genese)."""
    base = anterior or ("genese:" + nome_arquivo)
    corpo = "|".join([base, str(seq), h_val, quando_li_utc, evento_id])
    return hashlib.sha256(corpo.encode("utf-8")).hexdigest()[:12]


def _mes(iso: str) -> str:
    return str(iso)[:7]


def _arquivos_jsonl(dir_arquivo: str, ate_mes: str | None = None):
    """Lista os .jsonl em ordem cronologica; opcionalmente so ate um mes (AAAA-MM)."""
    if not os.path.isdir(dir_arquivo):
        return []
    nomes = sorted(n for n in os.listdir(dir_arquivo)
                   if n.endswith(".jsonl") and len(n) == 13)
    if ate_mes:
        nomes = [n for n in nomes if n[:7] <= ate_mes]
    return [os.path.join(dir_arquivo, n) for n in nomes]


def _linhas(caminho: str):
    """Itera as linhas de um .jsonl, pulando linha em branco. Linha corrompida
    e devolvida como None para o chamador contar em vez de estourar."""
    with io.open(caminho, "r", encoding="utf-8") as f:
        for bruta in f:
            bruta = bruta.strip()
            if not bruta:
                continue
            try:
                yield json.loads(bruta)
            except ValueError:
                yield None


# ----------------------------------------------------------------------------
# leitura das fontes
# ----------------------------------------------------------------------------
def _registro(e: dict, id_fonte, fonte: str) -> dict:
    """Converte um evento cru da fonte no formato canonico do arquivo."""
    titulo = _texto(e.get("titulo"))
    moeda = _texto(e.get("moeda"))
    quando = _texto(e.get("quando_utc"))
    pt = None
    for k in CHAVES_TITULO_PT:
        if e.get(k):
            pt = _texto(e.get(k))
            break
    return {
        "id_fonte": id_fonte,
        "chave": chave_derivada(titulo, moeda, quando),
        "titulo": titulo,
        "titulo_pt": pt,
        "moeda": moeda,
        "pais": _texto(e.get("pais")),
        "quando_utc": quando,
        "impacto": _texto(e.get("impacto")),
        # `calendario_resultado.json` diz consenso/divulgado; `macro_eventos.json`
        # diz previsao/resultado. Sao os mesmos numeros com nome diferente.
        "consenso": _num(e.get("consenso") if e.get("consenso") is not None else e.get("previsao")),
        "anterior": _num(e.get("anterior")),
        "divulgado": _num(e.get("divulgado") if e.get("divulgado") is not None else e.get("resultado")),
        "revisado": _num(e.get("revisado")),
        "unidade": _texto(e.get("unidade")),
        "fontes": [fonte],
    }


def coleta(caminho_calendario: str = ARQ_CALENDARIO,
           caminho_eventos: str = ARQ_EVENTOS):
    """Le as duas fontes e devolve (registros, diagnostico).

    `calendario_resultado.json` manda: tem o `id` estavel. `macro_eventos.json`
    so ENRIQUECE evento ja existente (preenche campo nulo, soma o nome da fonte);
    se um evento estiver apenas nele, entra com id_fonte nulo, porque perder o
    evento seria pior do que arquivar sem id.
    """
    diag = {"calendario": None, "eventos": None, "ambiguos": 0, "so_em_eventos": 0}
    cal, erro_cal = _le_json(caminho_calendario)
    evt, erro_evt = _le_json(caminho_eventos)
    diag["calendario"] = erro_cal or "ok"
    diag["eventos"] = erro_evt or "ok"

    registros = []
    por_chave = {}

    lista_cal = (cal or {}).get("eventos") or []
    for e in lista_cal:
        if not isinstance(e, dict):
            continue
        r = _registro(e, _texto(e.get("id")), "calendario_resultado.json")
        registros.append(r)
        por_chave.setdefault(r["chave"], []).append(r)

    lista_evt = (evt or {}).get("eventos") or []
    for e in lista_evt:
        if not isinstance(e, dict):
            continue
        r = _registro(e, None, "macro_eventos.json")
        alvos = por_chave.get(r["chave"], [])
        if len(alvos) == 1:
            alvo = alvos[0]
            for campo in ("titulo_pt", "unidade", "pais", "impacto") + CAMPOS_VALOR:
                if alvo.get(campo) is None and r.get(campo) is not None:
                    alvo[campo] = r[campo]
            if "macro_eventos.json" not in alvo["fontes"]:
                alvo["fontes"].append("macro_eventos.json")
        elif len(alvos) > 1:
            # Dois eventos diferentes com titulo+moeda+hora identicos (ex.: CPI da
            # zona do euro publicado por dois paises no mesmo minuto). Sem `pais`
            # do lado do macro_eventos nao da para saber qual e qual: nao se
            # adivinha, so se conta.
            diag["ambiguos"] += 1
        else:
            registros.append(r)
            por_chave.setdefault(r["chave"], []).append(r)
            diag["so_em_eventos"] += 1

    for r in registros:
        r["evento_id"] = r["id_fonte"] or r["chave"]
    return registros, diag


# ----------------------------------------------------------------------------
# estado do arquivo
# ----------------------------------------------------------------------------
def estado(dir_arquivo: str = DIR_ARQUIVO, ate_mes: str | None = None):
    """Ultima linha conhecida de cada evento, lendo os .jsonl em ordem."""
    ultimo = {}
    for caminho in _arquivos_jsonl(dir_arquivo, ate_mes):
        for linha in _linhas(caminho):
            if linha and linha.get("evento_id"):
                ultimo[linha["evento_id"]] = linha
    return ultimo


def _mudou(anterior: dict | None, novo: dict):
    """Decide se a leitura merece linha nova. Devolve (bool, campos, perdeu)."""
    if anterior is None:
        return True, ["primeira leitura"], []
    campos, perdeu = [], []
    for c in CAMPOS_VALOR:
        a, n = anterior.get(c), novo.get(c)
        if a == n:
            continue
        if n is None:
            perdeu.append(c)      # fonte piscou: nao apaga o que ja foi visto
            continue
        campos.append(c)
    return (len(campos) > 0), campos, perdeu


# ----------------------------------------------------------------------------
# escrita
# ----------------------------------------------------------------------------
def arquiva(dir_arquivo: str = DIR_ARQUIVO,
            caminho_calendario: str = ARQ_CALENDARIO,
            caminho_eventos: str = ARQ_EVENTOS,
            quando_li_utc: str | None = None,
            silencioso: bool = False):
    """Roda uma leitura e acrescenta ao arquivo so o que mudou.

    Devolve um dicionario com o resumo. Levanta RuntimeError se NENHUMA fonte
    puder ser lida — quem chama pela linha de comando vira isso em sys.exit(1),
    e nada no arquivo e tocado.
    """
    quando_li_utc = quando_li_utc or agora_utc()
    registros, diag = coleta(caminho_calendario, caminho_eventos)
    if not registros:
        raise RuntimeError(
            "nenhum evento lido (calendario: %s / macro_eventos: %s) — "
            "arquivo preservado, nada gravado" % (diag["calendario"], diag["eventos"]))

    os.makedirs(dir_arquivo, exist_ok=True)
    anterior = estado(dir_arquivo)

    nome = _mes(quando_li_utc) + ".jsonl"
    caminho = os.path.join(dir_arquivo, nome)
    seq, cadeia = 0, ""
    if os.path.exists(caminho):
        for linha in _linhas(caminho):
            if linha:
                seq = int(linha.get("seq") or (seq + 1))
                cadeia = linha.get("hash_cadeia") or ""

    fonte_gerado = None
    cal, _ = _le_json(caminho_calendario)
    if isinstance(cal, dict):
        fonte_gerado = _texto(cal.get("gerado_em"))

    novas, motivos = [], {}
    for r in registros:
        ok, campos, perdeu = _mudou(anterior.get(r["evento_id"]), r)
        if not ok:
            continue
        seq += 1
        h_val = hash_valores(r["evento_id"], r)
        cadeia = hash_cadeia(cadeia, nome, seq, h_val, quando_li_utc, r["evento_id"])
        linha = {
            "seq": seq,
            "evento_id": r["evento_id"],
            "id_fonte": r["id_fonte"],
            "chave": r["chave"],
            "titulo": r["titulo"],
            "titulo_pt": r["titulo_pt"],
            "moeda": r["moeda"],
            "pais": r["pais"],
            "quando_utc": r["quando_utc"],
            "impacto": r["impacto"],
            "consenso": r["consenso"],
            "anterior": r["anterior"],
            "divulgado": r["divulgado"],
            "revisado": r["revisado"],
            "unidade": r["unidade"],
            "quando_li_utc": quando_li_utc,
            "fonte_gerado_em": fonte_gerado,
            "fontes": r["fontes"],
            "mudou": campos,
            "perdeu": perdeu,
            "hash_valores": h_val,
            "hash_cadeia": cadeia,
        }
        novas.append(linha)
        for c in campos:
            motivos[c] = motivos.get(c, 0) + 1

    if novas:
        with io.open(caminho, "a", encoding="utf-8", newline="\n") as f:
            for linha in novas:
                f.write(json.dumps(linha, ensure_ascii=False, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    escreve_leiame(dir_arquivo)

    resumo = {
        "quando_li_utc": quando_li_utc,
        "arquivo": caminho,
        "eventos_lidos": len(registros),
        "linhas_gravadas": len(novas),
        "eventos_ja_conhecidos": len(anterior),
        "motivos": motivos,
        "diagnostico": diag,
    }
    if not silencioso:
        _imprime(resumo)
    return resumo


def _imprime(r: dict):
    print("=" * 72)
    print("ARQUIVADOR DO CALENDARIO — leitura de %s" % r["quando_li_utc"])
    print("=" * 72)
    d = r["diagnostico"]
    print("  fonte calendario_resultado.json : %s" % d["calendario"])
    print("  fonte macro_eventos.json        : %s" % d["eventos"])
    print("  eventos lidos nesta rodada      : %d" % r["eventos_lidos"])
    print("  eventos ja no arquivo           : %d" % r["eventos_ja_conhecidos"])
    print("  linhas GRAVADAS agora           : %d" % r["linhas_gravadas"])
    if r["motivos"]:
        print("  o que mudou                     : %s" %
              ", ".join("%s=%d" % (k, v) for k, v in sorted(r["motivos"].items())))
    if d["ambiguos"]:
        print("  ⚠ eventos ambiguos (mesmo titulo+moeda+hora, pais diferente): %d "
              "— enriquecimento pulado, nada adivinhado" % d["ambiguos"])
    if d["so_em_eventos"]:
        print("  eventos vindos so do macro_eventos.json (sem id): %d" % d["so_em_eventos"])
    print("  arquivo                         : %s" % r["arquivo"])
    if r["linhas_gravadas"] == 0:
        print("  → nada mudou desde a ultima leitura. Zero bytes escritos (regra anti-entulho).")


# ----------------------------------------------------------------------------
# leitura point-in-time — a funcao que o backtest usa
# ----------------------------------------------------------------------------
def reconstroi(data_iso: str, dir_arquivo: str = DIR_ARQUIVO, moedas=None):
    """Devolve o que se SABIA no instante `data_iso`.

    Regra dura: nenhuma linha com `quando_li_utc` POSTERIOR a `data_iso` entra no
    resultado. As ignoradas sao contadas em `linhas_ignoradas_futuro` para o
    numero poder ser mostrado — filtro que ninguem consegue conferir nao vale.

    `data_iso` sem hora ('2026-09-06') e lido como 00:00:00 UTC daquele dia, o
    corte mais conservador: nunca usa leitura do proprio dia mais tarde.
    """
    alvo = _instante(data_iso)
    mes_alvo = alvo.strftime("%Y-%m")
    eventos, lidas, ignoradas, corrompidas = {}, 0, 0, 0
    arquivos = _arquivos_jsonl(dir_arquivo, ate_mes=mes_alvo)
    for caminho in arquivos:
        for linha in _linhas(caminho):
            if linha is None:
                corrompidas += 1
                continue
            q = linha.get("quando_li_utc")
            if not q:
                corrompidas += 1
                continue
            if _instante(q) > alvo:
                ignoradas += 1
                continue
            if moedas and linha.get("moeda") not in moedas:
                continue
            lidas += 1
            eventos[linha["evento_id"]] = linha
    return {
        "pedido_utc": alvo.isoformat(),
        "arquivos_lidos": [os.path.basename(c) for c in arquivos],
        "linhas_usadas": lidas,
        "linhas_ignoradas_futuro": ignoradas,
        "linhas_corrompidas": corrompidas,
        "eventos": eventos,
    }


def _instante(iso: str) -> dt.datetime:
    """ISO-8601 para datetime ciente de fuso (UTC quando nao vier fuso)."""
    s = str(iso).strip().replace("Z", "+00:00")
    if len(s) == 10:
        s += "T00:00:00+00:00"
    d = dt.datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.UTC)
    return d.astimezone(dt.UTC)


# ----------------------------------------------------------------------------
# verificacao de integridade
# ----------------------------------------------------------------------------
def verifica(dir_arquivo: str = DIR_ARQUIVO):
    """Recalcula hash de valor e cadeia de todos os arquivos.

    Devolve (ok, problemas). Uma linha editada a mao quebra `hash_valores`; uma
    linha inserida, removida ou reordenada quebra `hash_cadeia` dali para frente.
    """
    problemas, total = [], 0
    for caminho in _arquivos_jsonl(dir_arquivo):
        nome = os.path.basename(caminho)
        cadeia, esperado_seq = "", 0
        for linha in _linhas(caminho):
            total += 1
            if linha is None:
                problemas.append("%s: linha ilegivel (JSON quebrado)" % nome)
                break
            esperado_seq += 1
            if linha.get("seq") != esperado_seq:
                problemas.append("%s: seq fora de ordem (esperado %d, veio %s)"
                                 % (nome, esperado_seq, linha.get("seq")))
                break
            hv = hash_valores(linha.get("evento_id"), linha)
            if hv != linha.get("hash_valores"):
                problemas.append("%s seq %d: hash_valores nao confere (linha editada?)"
                                 % (nome, esperado_seq))
                break
            cadeia = hash_cadeia(cadeia, nome, esperado_seq, hv,
                                 linha.get("quando_li_utc"), linha.get("evento_id"))
            if cadeia != linha.get("hash_cadeia"):
                problemas.append("%s seq %d: hash_cadeia nao confere (linha inserida/removida?)"
                                 % (nome, esperado_seq))
                break
    return (len(problemas) == 0), {"linhas": total, "problemas": problemas}


# ----------------------------------------------------------------------------
# LEIA-ME
# ----------------------------------------------------------------------------
LEIAME = """# Arquivo point-in-time do calendario macro

Gerado e mantido por `calendario_arquivo.py`. Este texto e documentacao e pode
ser reescrito; os `.jsonl` ao lado NAO — eles sao append-only.

## Por que este arquivo existe

A FXStreet serve uma janela ROLANTE de ~42 dias. Medido em 06/set/2026:
`data/calendario_resultado.json` trazia 233 eventos, de 2026-09-03 a 2026-09-13.
Evento que sai da janela leva o consenso junto, e nao ha endpoint de historico.

Surpresa = divulgado - consenso. Sem o consenso congelado ANTES do resultado, a
surpresa vira reconstrucao a posteriori — o mesmo furo que matou o backtest do
Deep Value. Este diretorio e a unica copia point-in-time que teremos.

## Formato

Um arquivo por MES DA LEITURA: `AAAA-MM.jsonl`, uma linha JSON por leitura de
evento. O mes e o do `quando_li_utc`, nao o do evento — assim cada execucao
escreve em um unico arquivo, e arquivo de mes fechado nunca mais e aberto para
escrita.

Campos de cada linha:

| campo | o que e |
|---|---|
| `seq` | posicao da linha dentro do arquivo (1, 2, 3...) |
| `evento_id` | identidade do evento: o `id` da fonte quando existe, senao a `chave` |
| `id_fonte` | `id` estavel da FXStreet, ou nulo |
| `chave` | `d-` + sha256(titulo+moeda+quando_utc), 16 hex — usada quando nao ha id |
| `titulo`, `titulo_pt`, `moeda`, `pais`, `quando_utc`, `impacto`, `unidade` | identidade e metadado |
| `consenso`, `anterior`, `divulgado`, `revisado` | **os campos de valor** |
| `quando_li_utc` | instante em que ESTE processo leu (o carimbo point-in-time) |
| `fonte_gerado_em` | `gerado_em` do JSON de origem (sempre <= `quando_li_utc`) |
| `fontes` | quais arquivos contribuiram |
| `mudou` | quais campos de valor mudaram e provocaram esta linha |
| `perdeu` | campos que eram conhecidos e voltaram nulos nesta leitura |
| `hash_valores` | sha256(evento_id + 4 campos de valor), 12 hex |
| `hash_cadeia` | sha256 encadeado com a linha anterior do mesmo arquivo, 12 hex |

`titulo_pt` sai **nulo** hoje: nenhuma das duas fontes publica titulo em
portugues (a traducao vive na interface). Campo sem fonte fica nulo — nao se
inventa traducao no arquivo.

## Append-only e anti-entulho

- Linha antiga nunca e reescrita nem removida. So se acrescenta ao fim.
- So se grava quando **consenso, anterior, divulgado ou revisado** mudou em
  relacao a ultima linha daquele evento. Rodar de novo sem novidade grava zero
  bytes — e o que permite o cron de 15 minutos.
- Valor conhecido que volta **nulo** nao conta como mudanca (a fonte piscando
  nao apaga o que ja foi visto). Se a linha for gravada por outro motivo, o
  campo sai nulo mesmo e o nome dele aparece em `perdeu`.
- Limite conhecido: **remarcacao de horario sozinha nao gera linha**. Se um
  evento com `id` for adiado sem mudar nenhum valor, o `quando_utc` novo so
  aparece na proxima linha que algum valor provocar. Para evento sem `id`, o
  horario entra na `chave`, entao a remarcacao vira um evento novo.

## Integridade — como provar que ninguem editou

    python calendario_arquivo.py --verifica

Recalcula `hash_valores` de cada linha e refaz a cadeia. Linha editada quebra o
hash dela; linha inserida, apagada ou reordenada quebra a cadeia dali para
frente, e a verificacao aponta a primeira divergencia.

## Como reconstruir o estado de uma data qualquer

    from calendario_arquivo import reconstroi
    estado = reconstroi("2026-09-06T12:00:00+00:00")
    estado["eventos"]["<evento_id>"]["consenso"]

`reconstroi` le so arquivos ate o mes pedido e descarta linha a linha tudo com
`quando_li_utc` posterior ao instante — o total descartado sai em
`linhas_ignoradas_futuro`, para o corte poder ser conferido. Data sem hora
(`2026-09-06`) e lida como 00:00:00 UTC daquele dia, o corte mais conservador.

Pela linha de comando:

    python calendario_arquivo.py --reconstroi 2026-09-06T12:00:00+00:00

## Ate onde a serie vai para tras

{BACKFILL}
"""


def escreve_leiame(dir_arquivo: str = DIR_ARQUIVO, backfill: str | None = None):
    """(Re)escreve o LEIA-ME.md. E documentacao, nao registro: pode ser reescrito."""
    os.makedirs(dir_arquivo, exist_ok=True)
    texto = LEIAME.replace("{BACKFILL}", backfill or TEXTO_BACKFILL)
    with io.open(os.path.join(dir_arquivo, "LEIA-ME.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


TEXTO_BACKFILL = """**A serie propria comeca em 06/set/2026.** Antes disso nao ha consenso
arquivado por nos — nao se inventa.

Existe um caminho de backfill PARCIAL, ainda nao executado, medido em
06/set/2026 sobre `wayback_ff/cdx_all.json.gz` (59.953 capturas do calendario do
Forex Factory no Internet Archive):

- capturas de pagina de calendario "limpa" (sem filtro na URL) e com corpo
  > 8 kB: **12.417**, de 2007 a 2026;
- dias uteis com captura tirada no mesmo dia ou antes, dentro da semana
  exibida — ou seja, com consenso congelado antes do resultado:
  **2.584 de 2.870 dias uteis entre 2014 e 2024 = 90,0%**;
  por ano: 2014 96,2% · 2015 73,9% · 2016 82,8% · 2017 89,6% · 2018 91,6% ·
  2019 92,7% · 2020 93,9% · 2021 91,2% · 2022 97,7% · 2023 95,8% · 2024 85,1%;
- antes de 2014 a cobertura cai muito: 2013 50,2% · 2012 43,7% · 2011 44,2% ·
  2010 26,4% · 2009 17,2% · 2008 6,1% · 2007 41,0%;
- 2025 (27,6%) e 2026 (8,8%) estao mortos: o Forex Factory entrou atras de
  Cloudflare e o crawler do Archive parou. Dali em diante so arquivador proprio
  — este aqui.

Amostra REAL de 8 capturas baixadas em 06/set/2026 (2015, 2018, 2021, 2024):
537 linhas das 8 majors, 258 com resultado, 355 com previsao e **146
observacoes point-in-time** (resultado vazio + previsao preenchida), ou seja
**18,2 observacoes PIT por captura**. Nas duas capturas de 2015 o leitor
devolveu 0 linhas: o HTML daquela epoca usa `class="currency"`, e o de 2017+ usa
`class="calendar__currency"`, e 2023+ tem um JSON embutido
(`calendarComponentStates`). Sao **tres leitores diferentes** — o backfill custa
codigo, nao acesso.

Conclusao honesta: da para reconstruir consenso historico do Forex Factory de
~2014 a 2024 com ~90% dos dias uteis cobertos, e de 2007 a 2013 com cobertura
irregular (6% a 50%), desde que se escrevam os leitores das tres eras e se leia
`FF.timezone` de dentro de cada pagina (o relogio da pagina e o do crawl, nao o
do evento). Nada disso foi colhido ainda: **hoje o arquivo comeca em
06/set/2026**.
"""


# ----------------------------------------------------------------------------
# linha de comando
# ----------------------------------------------------------------------------
def _cli(argv):
    if "--verifica" in argv:
        ok, r = verifica()
        print("VERIFICACAO DE INTEGRIDADE — %d linhas" % r["linhas"])
        if ok:
            print("  ✔ todas as linhas conferem (hash de valor e cadeia)")
            return 0
        for p in r["problemas"]:
            print("  ✘ %s" % p)
        return 1

    if "--reconstroi" in argv:
        i = argv.index("--reconstroi")
        if i + 1 >= len(argv):
            print("uso: python calendario_arquivo.py --reconstroi AAAA-MM-DD[THH:MM:SSZ]")
            return 1
        r = reconstroi(argv[i + 1])
        print("RECONSTRUCAO EM %s" % r["pedido_utc"])
        print("  arquivos lidos            : %s" % (", ".join(r["arquivos_lidos"]) or "nenhum"))
        print("  linhas usadas             : %d" % r["linhas_usadas"])
        print("  linhas ignoradas (futuro) : %d" % r["linhas_ignoradas_futuro"])
        print("  eventos conhecidos        : %d" % len(r["eventos"]))
        com = sum(1 for e in r["eventos"].values() if e.get("consenso") is not None)
        print("  destes, com consenso      : %d" % com)
        return 0

    if "--estado" in argv:
        e = estado()
        print("ESTADO ATUAL — %d eventos no arquivo" % len(e))
        return 0

    try:
        arquiva()
    except RuntimeError as err:
        print("FALHA: %s" % err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
