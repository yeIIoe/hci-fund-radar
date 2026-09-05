# -*- coding: utf-8 -*-
"""SNAPSHOT — o REGISTRO IMUTAVEL da leitura, para o backtest existir um dia.

╔══════════════════════════════════════════════════════════════════════════════╗
║  ARQUIVO APPEND-ONLY. NUNCA se edita nem se apaga uma linha ja gravada.       ║
║  Este script SO acrescenta. Se um numero antigo estiver errado, a correcao e  ║
║  uma linha NOVA depois — jamais um retoque na linha velha. O valor de um      ║
║  registro para backtest vem exatamente disso: ele nao pode ser reescrito pelo ║
║  que se aprendeu depois.                                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

POR QUE ISTO EXISTE
    O painel e um retrato do AGORA: sentimento.py roda de 15 em 15 minutos, busca a
    FXStreet ao vivo, le as manchetes das ultimas 72 h e recalcula tudo com os pesos de
    hoje. Nada disso pode ser reconstruido depois. Sem um registro gravado no instante,
    a "conviccao historica" nunca sai de null — nao ha amostra para calibrar.
    Este arquivo e a amostra. Cada linha e uma leitura carimbada, com o que se sabia
    naquele momento, e com os campos em branco para o Eduardo preencher a mao o que
    aconteceu depois (BO de 4 h, ZOI de 30 min, primeiro toque, entrada, resultado em R).

ONDE GRAVA
    data/snapshots/AAAA-MM-DD.jsonl — um arquivo por dia, uma linha JSON por par por
    instante de gravacao. Formato de uma linha em data/snapshots/LEIA-ME.md.

QUANDO GRAVA (a regra anti-entulho)
    A cadeia roda 96 vezes por dia. Gravar os 28 pares em toda rodada dariam 2.688 linhas
    por dia, quase todas identicas — entulho, nao amostra. Entao grava-se quando:
      1. e a PRIMEIRA leitura do par no dia (sempre grava, mesmo sem mudanca nenhuma);
      2. mudou a DIRECAO, a DIVERGENCIA ou a QUALIDADE DA EVIDENCIA em relacao a ultima
         linha do par naquele dia (qualquer um dos tres basta);
      3. saiu um evento de IMPACTO ALTO de uma das duas pernas depois da ultima linha do
         par — a leitura imediatamente posterior ao evento e sempre gravada, mesmo que os
         tres numeros nao tenham se mexido. E justamente o "nao se mexeu com NFP na mesa"
         que o backtest vai querer ler.
    Fora disso, nao grava. O campo `gatilho` de cada linha diz qual das tres regras a
    fez existir.

O QUE ELE NAO FAZ
    Nao chama fonte externa nenhuma. Le apenas os arquivos que a cadeia ja produziu
    (sentimento.json, bancos_centrais.json, calendario_resultado.json). Se um deles
    faltar, o campo correspondente sai null e a linha e gravada assim mesmo — buraco
    declarado, nunca zero.

    Nao inventa conviccao. `divergencia` e `qualidade_evidencia` sao os numeros da regua
    PROVISORIA de hoje; a calibracao contra resultado nao existe ainda, e por isso este
    arquivo esta sendo criado.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))

SENTIMENTO = os.path.join(AQUI, "data", "sentimento.json")
BANCOS = os.path.join(AQUI, "data", "bancos_centrais.json")
CALENDARIO = os.path.join(AQUI, "data", "calendario_resultado.json")
PASTA = os.path.join(AQUI, "data", "snapshots")

# Faixas PROVISORIAS. Sao a regua declarada do contrato, ainda sem calibracao — o backtest
# que este arquivo alimenta e que vai dizer se elas prestam. Usadas so como reserva, quando
# o sentimento.json ainda nao traz `estado` / `faixas_provisorias` prontos.
FAIXAS_RESERVA = {"sem_tese": [0, 14], "observacao": [15, 24], "moderada": [25, 39],
                  "forte": [40, 100]}

IMPACTO_ALTO = ("HIGH", "ALTO", "3")

LEIA_ME = """# data/snapshots — REGISTRO IMUTAVEL

## A regra, antes de qualquer coisa

**Estes arquivos sao APPEND-ONLY. Nunca se edita nem se apaga uma linha ja gravada.**

Quem escreve aqui e o `snapshot.py`, e ele so sabe acrescentar. Se um numero de uma linha
antiga estiver errado, a correcao e uma **linha nova depois**, com carimbo novo — jamais um
retoque na linha velha. Todo o valor deste diretorio para o backtest vem disso: uma leitura
gravada nao pode ser reescrita pelo que se aprendeu depois. Reescrever uma linha aqui e a
mesma coisa que apagar o backtest.

Nao rode script nenhum que reordene, deduplique ou "limpe" estes arquivos. Linhas repetidas
com carimbos diferentes sao informacao (a leitura nao mudou entre dois instantes), nao lixo.

## O que e cada arquivo

`AAAA-MM-DD.jsonl` — um arquivo por dia, uma linha JSON por par por instante de gravacao.
O par aparece varias vezes no mesmo dia, com carimbos diferentes.

## Quando uma linha e gravada

A cadeia roda de 15 em 15 minutos. Gravar tudo em toda rodada dariam ~2.688 linhas por dia,
quase todas identicas. Entao grava-se quando:

1. e a **primeira leitura do par no dia** — sempre;
2. mudou a **direcao**, a **divergencia** ou a **qualidade da evidencia** em relacao a
   ultima linha daquele par no dia — qualquer um dos tres basta;
3. saiu um **evento de impacto alto** de uma das duas pernas depois da ultima linha —
   a leitura logo apos o evento entra mesmo se os tres numeros nao se mexeram. E
   justamente o "nao se mexeu com o NFP na mesa" que o backtest vai querer ler.

O campo `gatilho` de cada linha diz qual das tres regras a fez existir.

## O formato de uma linha

```json
{"gravado_em": "2026-09-05T12:34:56.789012+00:00",
 "par": "AUDCAD",
 "direcao": "COMPRA",
 "divergencia": 37,
 "qualidade_evidencia": 58,
 "estado": "moderada",
 "gatilho": "primeira_do_dia",
 "perna_dominante": {"moeda": "AUD", "share_pct": 85},
 "dados_disponiveis": {"ultimo_evento_utc": "2026-09-04T01:30:00+00:00",
                       "ultimo_evento_alto_utc": "2026-09-03T01:30:00+00:00",
                       "n_eventos_janela": 27, "n_falas": 19,
                       "fontes": ["bancos_centrais", "fxstreet", "manchetes_google_news"]},
 "proximo_evento_invalidante": {"moeda": "AUD", "evento": "RBA",
                                "data": "2026-09-29", "dias": 24},
 "preenchido_pelo_operador": {"bo_h4": null, "zoi_m30": null, "primeiro_toque": null,
                              "entrada": null, "resultado_r": null}}
```

`gatilho` e `dados_disponiveis.ultimo_evento_alto_utc` sao acrescimos ao contrato, ambos
aditivos: o primeiro para a auditoria saber por que a linha existe, o segundo porque e o
relogio que dispara a regra 3.

## O bloco do operador

`preenchido_pelo_operador` sai **todo em null**, de proposito. Nenhum robo escreve nele.
E o Eduardo que preenche a mao, depois, o que aconteceu com aquela leitura:

- `bo_h4` — houve rompimento na janela de 4 h?
- `zoi_m30` — o preco chegou na zona de 30 min?
- `primeiro_toque` — carimbo do primeiro toque
- `entrada` — entrou, e a que preco
- `resultado_r` — o resultado em multiplos de risco

Enquanto essa coluna estiver vazia nao ha backtest, e por isso o campo
`conviccao_historica` do painel continua saindo `null` com "ainda nao calibrada".

## O que uma linha NAO prova

A linha e o retrato do que o **painel de hoje** dizia naquele instante. Ela nao e imune a
tudo: os pesos e limiares usados sao os do dia da gravacao, e se a regua mudar amanha, as
linhas velhas continuam com a regua velha — o que e correto para o backtest e uma armadilha
para quem comparar linhas de meses diferentes sem olhar a data. Ver a auditoria de
look-ahead no banner do corte de tempo do painel.
"""


def carrega(fn):
    try:
        return json.load(io.open(fn, encoding="utf-8"))
    except Exception:
        return None


# ------------------------------------------------------------------ TRAVA DE ESCRITA
#
# ⚠️ MEDIDO EM 05/set/2026, e por isso esta trava existe. O modo "a" do Python NAO garante
# append atomico no Windows: o CRT posiciona no fim e escreve, e dois processos podem
# posicionar no MESMO offset. Teste feito com este mesmo padrao de escrita (dois processos,
# 28 linhas de ~700 B cada, largados juntos): em 9 de 25 rodadas o arquivo terminou com 28
# linhas em vez de 56 — METADE DAS LINHAS SUMIU, sem erro nenhum, sem linha corrompida para
# denunciar, com os dois processos saindo com codigo 0. Um arquivo que se diz APPEND-ONLY
# perdendo linhas ja gravadas e o pior defeito possivel aqui: o backtest le um registro
# incompleto sem saber.
#
# E ha dois escritores de verdade: o proprio snapshot.py (chamado pela cadeia e tambem de
# dentro do sentimento.py) e a rotina de RESERVA do sentimento.py. Alem disso o
# macro_direction.yml roda com `cancel-in-progress`, que mata uma rodada no meio enquanto
# outra comeca. A trava fecha essa janela.
TRAVA_ESPERA_S = 20.0


@contextlib.contextmanager
def trava_exclusiva(caminho):
    """Trava exclusiva de processo, presa a um arquivo `.lock` ao lado do .jsonl.

    Windows usa msvcrt.locking, POSIX usa fcntl.flock. Se nao der para travar dentro do
    prazo, NAO grava: e melhor perder uma leitura de 15 em 15 minutos do que arriscar
    apagar linha ja gravada. O chamador recebe False e diz isso na tela.
    """
    fh = io.open(caminho + ".lock", "a+b")
    preso = False
    limite = time.time() + TRAVA_ESPERA_S
    try:
        try:
            import msvcrt                                              # noqa: WPS433
            travar = lambda: msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)      # noqa: E731
            soltar = lambda: (fh.seek(0), msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1))  # noqa: E731
        except ImportError:
            import fcntl                                               # noqa: WPS433
            travar = lambda: fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # noqa: E731
            soltar = lambda: fcntl.flock(fh.fileno(), fcntl.LOCK_UN)   # noqa: E731
        while time.time() < limite:
            try:
                fh.seek(0)
                travar()
                preso = True
                break
            except OSError:
                time.sleep(0.15)
        yield preso
    finally:
        if preso:
            try:
                soltar()
            except Exception:
                pass
        fh.close()


# --------------------------------------------------------------------------- leitura


def _num(x):
    try:
        return int(round(float(x)))
    except (TypeError, ValueError):
        return None


def direcao_do_par(p):
    """COMPRA / VENDA / SEM_TESE. Prefere o campo `acao` do contrato; se ele ainda nao
    existir no sentimento.json, cai no `sinal` antigo (BULL/BEAR/SEM_TESE)."""
    acao = str(p.get("acao") or "").strip().lower()
    if acao.startswith("compra"):
        return "COMPRA"
    if acao.startswith("venda"):
        return "VENDA"
    if acao.startswith("sem tese"):
        return "SEM_TESE"
    sinal = str(p.get("sinal") or "").upper()
    return {"BULL": "COMPRA", "BEAR": "VENDA"}.get(sinal, "SEM_TESE")


def divergencia_do_par(p):
    """`divergencia` e o nome novo do antigo `conviccao_pct`. Aceita os dois."""
    v = _num(p.get("divergencia"))
    return v if v is not None else _num(p.get("conviccao_pct"))


def qualidade_do_par(p, moedas):
    """A qualidade do par e o ELO FRACO: a MENOR das duas pernas. Se o contrato ainda nao
    trouxe o campo pronto, monta a partir de moedas[X].qualidade_evidencia.nota."""
    v = _num(p.get("qualidade_evidencia"))
    if v is not None:
        return v
    notas = []
    for m in (p.get("base"), p.get("cotada")):
        q = ((moedas or {}).get(m) or {}).get("qualidade_evidencia") or {}
        n = _num(q.get("nota"))
        if n is not None:
            notas.append(n)
    return min(notas) if len(notas) == 2 else None


def estado_do_par(p, direcao, divergencia):
    """Reserva: se o contrato ainda nao trouxe `estado`, deriva das faixas provisorias."""
    e = p.get("estado")
    if e:
        return str(e)
    if direcao == "SEM_TESE" or divergencia is None:
        return "sem_tese"
    faixas = p.get("faixas_provisorias") or FAIXAS_RESERVA
    for nome, faixa in faixas.items():
        try:
            if int(faixa[0]) <= divergencia <= int(faixa[1]):
                return nome
        except Exception:
            continue
    return "sem_tese"


def perna_dominante_do_par(p):
    """Reserva: `perna_motivo` mais o share pelo tamanho dos dois scores."""
    pd = p.get("perna_dominante")
    if isinstance(pd, dict) and pd.get("moeda"):
        return {"moeda": pd.get("moeda"), "share_pct": _num(pd.get("share_pct"))}
    perna = p.get("perna_motivo")
    if not perna or perna == "ambas":
        return {"moeda": None, "share_pct": None}
    try:
        sb = abs(float((p.get("leitura_base") or {}).get("score") or 0.0))
        sq = abs(float((p.get("leitura_cotada") or {}).get("score") or 0.0))
        total = sb + sq
        meu = sb if perna == p.get("base") else sq
        share = _num(meu / total * 100) if total > 0 else None
    except Exception:
        share = None
    return {"moeda": perna, "share_pct": share}


def invalidante_do_par(p, bancos):
    """A proxima reuniao que pode virar a mesa. Prefere o campo do contrato; na reserva,
    pega a perna cuja decisao vem primeiro."""
    inv = p.get("proximo_evento_invalidante")
    if isinstance(inv, dict) and inv.get("data"):
        return inv
    B = (bancos or {}).get("bancos") or {}
    cand = []
    for m in (p.get("base"), p.get("cotada")):
        b = B.get(m) or {}
        if b.get("proxima"):
            cand.append({"moeda": m, "evento": b.get("sigla") or b.get("banco"),
                         "data": b.get("proxima"), "dias": _num(b.get("dias_ate"))})
    if not cand:
        return None
    cand.sort(key=lambda x: (x["dias"] if x["dias"] is not None else 9999))
    return cand[0]


def eventos_do_par(cal, p, agora_iso):
    """Do calendario ja gravado: o ultimo evento DIVULGADO de cada perna e o ultimo de
    IMPACTO ALTO. So conta o que ja saiu (divulgado != None) e cujo carimbo nao e futuro."""
    ev = (cal or {}).get("eventos") or []
    moedas = {p.get("base"), p.get("cotada")}
    ult, ult_alto, n = None, None, 0
    for e in ev:
        if e.get("moeda") not in moedas:
            continue
        q = e.get("quando_utc")
        if not q or q > agora_iso:
            continue
        if e.get("divulgado") is None:
            continue
        n += 1
        if ult is None or q > ult:
            ult = q
        if str(e.get("impacto") or "").upper() in IMPACTO_ALTO:
            if ult_alto is None or q > ult_alto:
                ult_alto = q
    return ult, ult_alto, n


def fontes_do_par(p, moedas):
    """De onde veio a evidencia das duas pernas, sem enfeite. A distincao que importa e
    fala do banco x manchete de imprensa — o painel ja errou isso uma vez."""
    f = {"fxstreet", "bancos_centrais"}
    for m in (p.get("base"), p.get("cotada")):
        dims = ((moedas or {}).get(m) or {}).get("dimensoes") or {}
        t = dims.get("texto") or {}
        origem = str(t.get("origem") or "").lower()
        if origem in ("headlines", "manchete"):
            f.add("manchetes_google_news")
        elif origem in ("discurso_oficial", "comunicado_ata", "imprensa_com_fala"):
            f.add("bc_discursos")
        elif t:
            f.add("bc_discursos")
        if (dims.get("geo") or {}):
            f.add("gdelt")
    return sorted(f)


def n_falas_do_par(p, moedas):
    total, achou = 0, False
    for m in (p.get("base"), p.get("cotada")):
        t = (((moedas or {}).get(m) or {}).get("dimensoes") or {}).get("texto") or {}
        n = _num(t.get("n"))
        if n is not None:
            total += n
            achou = True
    return total if achou else None


# --------------------------------------------------------------------- append-only


def linhas_do_dia(caminho):
    """Le o arquivo do dia e devolve a ULTIMA linha de cada par. Linha corrompida e
    ignorada em silencio — nunca reescrita, nunca apagada."""
    ultimas = {}
    total = 0
    if not os.path.exists(caminho):
        return ultimas, total
    with io.open(caminho, encoding="utf-8") as fh:
        for bruta in fh:
            bruta = bruta.strip()
            if not bruta:
                continue
            total += 1
            try:
                obj = json.loads(bruta)
            except Exception:
                continue
            par = obj.get("par")
            if par:
                ultimas[par] = obj
    return ultimas, total


def precisa_gravar(anterior, nova):
    """As tres regras. Devolve o GATILHO, ou None quando nao ha o que gravar."""
    if anterior is None:
        return "primeira_do_dia"
    mudou = []
    if anterior.get("direcao") != nova["direcao"]:
        mudou.append("direcao")
    if anterior.get("divergencia") != nova["divergencia"]:
        mudou.append("divergencia")
    if anterior.get("qualidade_evidencia") != nova["qualidade_evidencia"]:
        mudou.append("qualidade_evidencia")
    if mudou:
        return "mudou_" + "_e_".join(mudou)
    ant_dd = anterior.get("dados_disponiveis") or {}
    # Linha antiga SEM o campo do relogio (gravada por outra versao do script) e "nao sei",
    # nao "mudou". Disparar aqui geraria uma enxurrada de linhas identicas na primeira
    # rodada depois de um upgrade — exatamente o entulho que a regra existe para evitar.
    if "ultimo_evento_alto_utc" not in ant_dd:
        return None
    a_alto = ant_dd.get("ultimo_evento_alto_utc")
    n_alto = (nova.get("dados_disponiveis") or {}).get("ultimo_evento_alto_utc")
    if n_alto and n_alto != a_alto:
        return "evento_de_impacto_alto"
    return None


def main():
    sent = carrega(SENTIMENTO)
    if not sent or not isinstance(sent.get("pares"), list):
        print("! data/sentimento.json ausente ou sem 'pares' — nada a gravar")
        return 1
    bancos = carrega(BANCOS)
    cal = carrega(CALENDARIO)
    moedas = sent.get("moedas") or {}

    agora = dt.datetime.now(dt.timezone.utc)
    agora_iso = agora.isoformat()
    dia = agora.date().isoformat()

    os.makedirs(PASTA, exist_ok=True)
    leia_me = os.path.join(PASTA, "LEIA-ME.md")
    if not os.path.exists(leia_me):
        with io.open(leia_me, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(LEIA_ME)

    caminho = os.path.join(PASTA, dia + ".jsonl")

    # A REGUA DO DIA, copiada do sentimento.json. Sem ela a linha NAO e reconstruivel: as
    # faixas, o limiar, o teto por item e o decaimento do ciclo sao os do dia da gravacao.
    # Medido em 05/set: o AUDCAD saiu com divergencia 37 as 04:17 e 25 as 04:20, com o MESMO
    # mercado — mudou a regua, e nada na linha antiga dizia isso.
    # (Desde a tarde de 05/set a divergencia e normalizada pelo teto TEORICO, constante em
    # 1,50, justamente para o denominador parar de se mexer sozinho quando uma dimensao cai.
    # O teto ligado continua gravado ao lado, como medida de quanta dimensao estava de pe.)
    regua_do_dia = dict(sent.get("regua") or {})
    regua_do_dia["sentimento_gerado_em"] = sent.get("gerado_em")
    regua_do_dia["origem_eventos"] = sent.get("origem_eventos")

    with trava_exclusiva(caminho) as preso:
        if not preso:
            print("! outro processo esta gravando o snapshot — nada gravado nesta rodada")
            print("  (a trava existe porque append concorrente no Windows APAGA linha ja")
            print("   gravada: medido, 9 de 25 rodadas perderam METADE das linhas, sem erro)")
            return 3

        ultimas, total_antes = linhas_do_dia(caminho)

        novas, motivos = [], {}
        for p in sent["pares"]:
            par = p.get("par")
            if not par:
                continue
            direcao = direcao_do_par(p)
            divergencia = divergencia_do_par(p)
            qualidade = qualidade_do_par(p, moedas)
            estado = estado_do_par(p, direcao, divergencia)
            # COERENCIA: par na zona neutra nao sai com lado. O arquivo de hoje ja tem 10
            # linhas dizendo "COMPRA" com estado "sem_tese" (gravadas antes de existir o
            # campo `acao`), e um backtest que leia `direcao` conta as 10 como operacao.
            # Linha velha nao se conserta — o arquivo e append-only — mas da para nao
            # produzir mais nenhuma.
            if estado == "sem_tese" and direcao in ("COMPRA", "VENDA"):
                direcao = "SEM_TESE"
            ult, ult_alto, n_ev = eventos_do_par(cal, p, agora_iso)
            linha = {
                "gravado_em": agora_iso,
                "par": par,
                "direcao": direcao,
                "divergencia": divergencia,
                "qualidade_evidencia": qualidade,
                "estado": estado,
                "gatilho": None,
                "perna_dominante": perna_dominante_do_par(p),
                # A CONTA POR EXTENSO, para a linha se explicar sozinha daqui a um ano.
                "como_a_divergencia_saiu": {
                    "diff": p.get("diff"),
                    "teto_ligado": p.get("diff_teto"),
                    "teto_teorico": p.get("diff_teto_teorico"),
                    "score_base": ((p.get("leitura_base") or {}).get("score")),
                    "score_cotada": ((p.get("leitura_cotada") or {}).get("score")),
                    "conta": "divergencia = |diff| / teto_teorico x 100 (o teto teorico e 1,50: 0,25 x 3 dimensoes que votam, nas duas pernas). O teto LIGADO fica ao lado so para dizer quanta dimensao estava de pe.",
                },
                "regua_em_vigor": regua_do_dia,
                "dados_disponiveis": {
                    "ultimo_evento_utc": ult,
                    "ultimo_evento_alto_utc": ult_alto,
                    "n_eventos_janela": n_ev,
                    "n_falas": n_falas_do_par(p, moedas),
                    "fontes": fontes_do_par(p, moedas),
                },
                "proximo_evento_invalidante": invalidante_do_par(p, bancos),
                # SO o Eduardo preenche. Nenhum robo escreve aqui.
                "preenchido_pelo_operador": {"bo_h4": None, "zoi_m30": None,
                                             "primeiro_toque": None, "entrada": None,
                                             "resultado_r": None},
            }
            gat = precisa_gravar(ultimas.get(par), linha)
            if not gat:
                continue
            linha["gatilho"] = gat
            novas.append(linha)
            motivos[gat] = motivos.get(gat, 0) + 1

        if novas:
            # "a" — APPEND. Nunca "w". Nunca reescreve o arquivo. Com flush + fsync antes de
            # soltar a trava: sem isso o buffer de 8 KB pode cortar linha no meio.
            with io.open(caminho, "a", encoding="utf-8", newline="\n") as fh:
                for linha in novas:
                    fh.write(json.dumps(linha, ensure_ascii=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())

        _, total_depois = linhas_do_dia(caminho)

    print("SNAPSHOT — registro imutavel (append-only, com trava exclusiva)")
    print("  arquivo ...... data/snapshots/%s.jsonl" % dia)
    print("  pares lidos .. %d" % len(sent["pares"]))
    print("  linhas antes . %d" % total_antes)
    print("  gravadas ..... %d %s" % (len(novas),
                                      ("(" + ", ".join("%s x%d" % (k, v)
                                       for k, v in sorted(motivos.items())) + ")")
                                      if motivos else "(nada mudou — nenhuma linha nova)"))
    print("  linhas depois  %d" % total_depois)
    return 0


if __name__ == "__main__":
    sys.exit(main())
