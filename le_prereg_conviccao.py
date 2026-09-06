# -*- coding: utf-8 -*-
"""Le a amostra do PREREG_CONVICCAO e diz SO quanto falta. Nao calcula resultado.

O PROBLEMA QUE ISTO RESOLVE
    O campo `conviccao_historica` do painel sai `null` porque nunca foi calibrado. A
    calibracao esta pre-registrada em PREREG_CONVICCAO.md, congelada em 06/set/2026, e o
    pre-registro tem uma data de leitura fixa: 2026-12-21. A tentacao, todo dia ate la, e
    "so dar uma espiada em como esta indo". Espiar e o que transforma pre-registro em
    justificativa: quem viu o parcial escolhe quando parar de colher.

    Entao este script existe justamente para NAO calcular. Ele conta, valida a estrutura da
    amostra e mostra o quanto falta. A conta do acerto so passa a existir dentro dele depois
    da data marcada, e so quando n >= 60 par-eventos com >= 25 blocos.

O QUE ELE FAZ HOJE
    1. le tudo em data/snapshots/*.jsonl (append-only, nunca escreve nada la)
    2. confere campo a campo se a linha tem o contrato que o backtest vai precisar
    3. monta as observacoes pela regra do secao 1 do pre-registro:
       par-evento = (par x ciclo de evento invalidante), aberto na PRIMEIRA linha do ciclo
       com direcao diferente de SEM_TESE
    4. separa as ABERTAS (evento ainda no futuro) das FECHADAS (evento ja passou)
    5. conta os BLOCOS = (semana ISO em que a janela fecha) x (moeda da perna dominante) --
       a unidade de informacao do nulo, porque pares que compartilham a perna e morrem na
       mesma semana sao a mesma aposta, nao observacoes independentes
    6. imprime "n atual X de 60, faltam Y dias" e vai embora

O QUE ELE NAO FAZ, E NAO VAI FAZER ANTES DA DATA
    Nao busca preco. Nao calcula retorno, acerto, percentil, nem sorteio. Nao escreve arquivo
    nenhum. Nao le a coluna do operador. Nao toca nos snapshots.

CODIGO DE SAIDA
    0 = amostra integra (mesmo com n=0, que e o esperado hoje)
    1 = diretorio ausente, arquivo ilegivel, JSON quebrado ou linha sem campo obrigatorio.
        Falha aqui e barulho de proposito: amostra torta descoberta em dezembro nao tem
        conserto, porque nao ha backfill (secao 8 do pre-registro).
"""
from __future__ import annotations

import datetime as dt
import glob
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_SNAPS = os.path.join(AQUI, "data", "snapshots")

# --- constantes CONGELADAS pelo PREREG_CONVICCAO.md (06/set/2026) -----------------------
DATA_LEITURA = dt.date(2026, 12, 21)  # secao 5.2 -- nada de olhar antes
N_MINIMO = 60                         # secao 4.1 -- par-eventos fechados e validos
BLOCOS_MINIMO = 25                    # secao 4.1 -- a unidade de informacao e o bloco
MIN_PREGOES = 3                       # secao 1.3 -- janela curta e descartada
MAX_DIAS_JANELA = 45                  # secao 1.3 -- acima disso, truncada

# Contrato da linha. Chave -> obrigatoria?
CAMPOS_TOPO = {
    "gravado_em": True,
    "par": True,
    "direcao": True,
    "divergencia": True,
    "qualidade_evidencia": True,
    "estado": True,
    "perna_dominante": True,
    "dados_disponiveis": True,
    "proximo_evento_invalidante": True,   # pode vir null, mas a CHAVE tem de existir
    "preenchido_pelo_operador": True,
    "gatilho": False,                     # so existe desde 05/set a tarde
    "como_a_divergencia_saiu": False,
    "regua_em_vigor": False,
}
DIRECOES = {"COMPRA", "VENDA", "SEM_TESE"}
CAMPOS_OPERADOR = {"bo_h4", "zoi_m30", "primeiro_toque", "entrada", "resultado_r"}


def carimbo(texto):
    """Le o gravado_em em ISO com fuso. Devolve datetime aware ou None."""
    try:
        d = dt.datetime.fromisoformat(str(texto))
    except Exception:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def dias_uteis(d0: dt.date, d1: dt.date) -> int:
    """Dias uteis entre duas datas, exclusivo no inicio, inclusivo no fim.

    ESTIMATIVA. A contagem que vale no dia da leitura e a de PREGOES da propria serie de
    preco (secao 2.4 do pre-registro). Aqui serve so para antecipar quantas observacoes
    provavelmente cairao na regra da janela curta.
    """
    n, d = 0, d0
    while d < d1:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def valida_linha(d, origem, num):
    """Devolve lista de problemas da linha. Lista vazia = linha integra."""
    problemas = []
    if not isinstance(d, dict):
        return ["linha nao e objeto JSON"]
    for campo, obrigatorio in CAMPOS_TOPO.items():
        if obrigatorio and campo not in d:
            problemas.append("falta o campo obrigatorio '%s'" % campo)
    if "direcao" in d and d["direcao"] not in DIRECOES:
        problemas.append("direcao invalida: %r" % (d["direcao"],))
    if "gravado_em" in d and carimbo(d["gravado_em"]) is None:
        problemas.append("gravado_em ilegivel: %r" % (d["gravado_em"],))
    for campo in ("divergencia", "qualidade_evidencia"):
        v = d.get(campo)
        if v is not None and not (isinstance(v, (int, float)) and 0 <= v <= 100):
            problemas.append("%s fora de 0-100 ou nao numerico: %r" % (campo, v))
    pd_ = d.get("perna_dominante")
    if pd_ is not None and not (isinstance(pd_, dict) and "moeda" in pd_):
        problemas.append("perna_dominante sem 'moeda'")
    pe = d.get("proximo_evento_invalidante")
    if pe is not None:
        if not isinstance(pe, dict):
            problemas.append("proximo_evento_invalidante nao e objeto")
        else:
            for k in ("moeda", "evento", "data"):
                if k not in pe:
                    problemas.append("proximo_evento_invalidante sem '%s'" % k)
            try:
                dt.date.fromisoformat(str(pe.get("data")))
            except Exception:
                problemas.append("data do evento ilegivel: %r" % (pe.get("data"),))
    op = d.get("preenchido_pelo_operador")
    if op is not None:
        if not isinstance(op, dict):
            problemas.append("preenchido_pelo_operador nao e objeto")
        else:
            faltando = CAMPOS_OPERADOR - set(op)
            if faltando:
                problemas.append("coluna do operador sem %s" % ", ".join(sorted(faltando)))
    return ["%s linha %d: %s" % (os.path.basename(origem), num, p) for p in problemas]


def main():
    hoje = dt.date.today()

    if not os.path.isdir(DIR_SNAPS):
        print("ERRO: diretorio ausente -> %s" % DIR_SNAPS)
        print("Sem registro imutavel nao existe amostra, e nao ha backfill possivel.")
        sys.exit(1)

    arquivos = sorted(glob.glob(os.path.join(DIR_SNAPS, "*.jsonl")))
    if not arquivos:
        print("ERRO: nenhum arquivo AAAA-MM-DD.jsonl em %s" % DIR_SNAPS)
        sys.exit(1)

    linhas_total = 0
    problemas = []
    quebradas = 0
    linhas = []

    for caminho in arquivos:
        try:
            conteudo = io.open(caminho, encoding="utf-8", errors="replace").read()
        except Exception as e:
            print("ERRO: nao consegui ler %s (%s)" % (caminho, e))
            sys.exit(1)
        for num, bruta in enumerate(conteudo.splitlines(), start=1):
            bruta = bruta.strip()
            if not bruta:
                continue
            linhas_total += 1
            try:
                d = json.loads(bruta)
            except Exception as e:
                quebradas += 1
                problemas.append("%s linha %d: JSON quebrado (%s)"
                                 % (os.path.basename(caminho), num, e))
                continue
            ruins = valida_linha(d, caminho, num)
            if ruins:
                problemas.extend(ruins)
                continue
            linhas.append(d)

    # ---- monta as observacoes pela regra da secao 1 -------------------------------------
    # ciclo = (par, evento, data do evento). Abre na PRIMEIRA linha com tese do ciclo.
    linhas.sort(key=lambda d: (carimbo(d["gravado_em"]), d["par"]))
    abertura = {}
    sem_evento = 0
    for d in linhas:
        if d["direcao"] == "SEM_TESE":
            continue
        pe = d.get("proximo_evento_invalidante")
        if not pe:
            sem_evento += 1          # secao 1.3: sem relogio de fim, nao abre observacao
            continue
        chave = (d["par"], pe.get("evento"), pe.get("data"))
        if chave not in abertura:
            abertura[chave] = d

    fechadas, abertas, curtas = [], [], []
    for chave, d in abertura.items():
        pe = d["proximo_evento_invalidante"]
        d_evento = dt.date.fromisoformat(str(pe["data"]))
        d0 = carimbo(d["gravado_em"]).date()
        # estimativa da janela: do dia seguinte ao carimbo ate a vespera do evento
        n_est = max(0, dias_uteis(d0, d_evento) - 1)
        registro = (chave[0], d0.isoformat(), d["direcao"], pe.get("evento"),
                    d_evento.isoformat(), n_est)
        if n_est < MIN_PREGOES:
            curtas.append(registro)
        elif d_evento < hoje:
            fechadas.append(registro)
        else:
            abertas.append(registro)

    def blocos_de(regs, so_moeda=False):
        # BLOCO = (semana ISO do fim da janela) x (moeda da perna dominante) -- secao 3.2
        # so_moeda=True devolve o bloco SEVERO usado na robustez da secao 3.5
        s = set()
        for par, d0, direcao, evento, d_ev, n in regs:
            d = abertura_por_registro[(par, d0, evento, d_ev)]
            moeda = (d.get("perna_dominante") or {}).get("moeda")
            if so_moeda:
                s.add(moeda)
            else:
                iso = dt.date.fromisoformat(d_ev).isocalendar()
                s.add(("%d-S%02d" % (iso[0], iso[1]), moeda))
        return s

    abertura_por_registro = {}
    for chave, d in abertura.items():
        pe = d["proximo_evento_invalidante"]
        d0 = carimbo(d["gravado_em"]).date().isoformat()
        abertura_por_registro[(chave[0], d0, pe.get("evento"), str(pe.get("data")))] = d

    blocos_fechados = blocos_de(fechadas)
    blocos_abertos = blocos_de(abertas)

    n_atual = len(fechadas)
    faltam_dias = (DATA_LEITURA - hoje).days

    # ---- relatorio ---------------------------------------------------------------------
    print("=" * 78)
    print("PREREG_CONVICCAO — leitor da amostra (NAO calcula resultado)")
    print("=" * 78)
    print("Hoje: %s   |   Data da leitura CONGELADA: %s" % (hoje, DATA_LEITURA))
    print("")
    print("-- ESTRUTURA DA AMOSTRA --------------------------------------------------")
    print("arquivos ...................... %d (%s)"
          % (len(arquivos), ", ".join(os.path.basename(a) for a in arquivos)))
    print("linhas lidas .................. %d" % linhas_total)
    print("linhas integras ............... %d" % len(linhas))
    print("linhas com problema ........... %d (JSON quebrado: %d)" % (len(problemas), quebradas))
    if problemas:
        for p in problemas[:20]:
            print("   ! %s" % p)
        if len(problemas) > 20:
            print("   ! ... e mais %d" % (len(problemas) - 20))
    print("linhas com tese e SEM evento invalidante (nao abrem observacao) ... %d" % sem_evento)
    print("")
    print("-- PAR-EVENTOS (secao 1 do pre-registro) ---------------------------------")
    print("abertos e ainda em curso ...... %d  (blocos: %d)" % (len(abertas), len(blocos_abertos)))
    print("descartados por janela curta .. %d  (< %d pregoes, estimativa por dias uteis)"
          % (len(curtas), MIN_PREGOES))
    print("FECHADOS e validos ............ %d" % n_atual)
    print("blocos fechados ............... %d  (BLOCO = semana ISO do fim x perna dominante)"
          % len(blocos_fechados))
    print("   no corte severo da robustez (so a moeda) ....... %d"
          % len(blocos_de(fechadas, so_moeda=True)))
    if abertas:
        print("")
        print("   em curso, por evento de fim:")
        porev = {}
        for par, d0, direcao, evento, d_ev, n in sorted(abertas, key=lambda r: r[4]):
            porev.setdefault((d_ev, evento), []).append("%s/%s" % (par, direcao))
        for (d_ev, evento), lista in sorted(porev.items()):
            print("   %s %-5s  %2d: %s" % (d_ev, evento, len(lista), ", ".join(lista)))
    print("")
    print("-- QUANTO FALTA ----------------------------------------------------------")
    print("")
    print("   >>> n atual %d de %d, faltam %d dias <<<" % (n_atual, N_MINIMO, faltam_dias))
    print("")
    print("   blocos %d de %d (as duas condicoes tem de fechar juntas)"
          % (len(blocos_fechados), BLOCOS_MINIMO))
    print("")
    print("-- O QUE ESTE SCRIPT SE RECUSA A FAZER -----------------------------------")
    if hoje < DATA_LEITURA or n_atual < N_MINIMO or len(blocos_fechados) < BLOCOS_MINIMO:
        motivos = []
        if hoje < DATA_LEITURA:
            motivos.append("a data da leitura e %s e faltam %d dias" % (DATA_LEITURA, faltam_dias))
        if n_atual < N_MINIMO:
            motivos.append("o n fechado e %d, abaixo de %d" % (n_atual, N_MINIMO))
        if len(blocos_fechados) < BLOCOS_MINIMO:
            motivos.append("os blocos sao %d, abaixo de %d"
                           % (len(blocos_fechados), BLOCOS_MINIMO))
        print("Nao calculo taxa de acerto, sorteio, percentil nem nada parecido porque " +
              "; ".join(motivos) + ".")
        print("A regra do pre-registro e ESPERAR, nunca olhar antes (secao 5.3).")
        print("A conta so passa a existir dentro deste arquivo depois de %s." % DATA_LEITURA)
    else:
        print("As tres condicoes fecharam. A rotina de leitura ainda NAO foi escrita — ela e")
        print("escrita uma vez so, na data, seguindo as secoes 2, 3, 6 e 7 do pre-registro, e")
        print("grava data/prereg_conviccao_leitura.json, que depois disso e congelado.")
    print("")
    print("Pre-registro: PREREG_CONVICCAO.md (congelado em 2026-09-06)")
    print("Snapshots: append-only. Este script nunca escreve neles.")
    print("=" * 78)

    if problemas:
        print("")
        print("SAINDO COM ERRO: ha %d linha(s) fora do contrato. Amostra torta descoberta em"
              % len(problemas))
        print("dezembro nao tem conserto — nao existe backfill (secao 8).")
        sys.exit(1)


if __name__ == "__main__":
    main()
