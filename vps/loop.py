# -*- coding: utf-8 -*-
"""LOOP — o processo SEMPRE LIGADO da cadeia macro-direction, para rodar numa VPS.

POR QUE EXISTE
    O cron do GitHub Actions promete 15 min e entrega 15 a 35 (ou pula). A fonte (FXStreet)
    entrega o numero em segundos; o RELOGIO e que atrasava. Este arquivo e o relogio novo:
    um processo Python que nunca desliga, roda a MESMA cadeia do workflow
    (.github/workflows/macro_direction.yml), na MESMA ordem, e faz commit + push dos MESMOS
    JSONs. Nada mais.

O QUE ELE FAZ, EM TRES RITMOS
    1. RODADA COMPLETA, a cada 15 min: feed de reserva (Forex Factory) -> fxstreet_calendario
       -> eua_leitor -> bc_discursos -> bancos_centrais -> macro_eventos -> correlacao_juros
       -> noticias -> geopolitica -> sentimento. Cada script roda em subprocesso proprio,
       com timeout, e o erro de um NAO derruba os outros (continue-on-error, como na Action).
       Os caches internos (eua_leitor 60 min, correlacao 20 h, geopolitica 3 h) sao dos
       scripts: aqui ninguem passa --forcar.
    2. FAST LANE, em volta de cada evento HIGH/MEDIUM das 8 moedas: de 12 min antes ate
       10 min depois da hora marcada, roda SO fxstreet_calendario + macro_eventos a cada 5 s,
       ate o campo 'resultado' do evento aparecer no macro_eventos.json. NESSE instante roda
       o sentimento uma vez e publica. Antes do numero sair nao ha commit nenhum: os JSONs
       mudam a cada passada so pelo carimbo de hora, e isso nao e informacao. Ai volta ao
       ritmo normal.
    3. PUBLICACAO: depois de qualquer rodada que mudou um JSON de data/, git add SO dos
       arquivos que o workflow commita, commit, pull --rebase (em conflito de data/*.json a
       versao LOCAL vence) e push. Nunca commita nada fora de data/.

O QUE ELE NUNCA FAZ
    Morrer por erro de script, de rede ou de git — tudo e capturado, registrado em
    vps/logs/ e a volta seguinte continua. Commitar .env, logs ou qualquer arquivo fora
    da lista. Forcar cache.

MODOS
    python vps/loop.py                 o loop de verdade (e o que o systemd roda)
    python vps/loop.py --uma-vez       PASSADA SECA: lista o que faria (scripts, janelas da
                                       fast lane, arquivos que commitaria), sem rodar script
                                       nenhum e sem tocar no git. Serve para testar no Windows.
    python vps/loop.py --uma-rodada    roda a cadeia completa UMA vez, mostra o que mudou,
                                       sem commit e sem push. Serve para validar a VPS antes
                                       de ligar o servico.

So biblioteca padrao (Python 3.12+). Sem pip.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
import time
import urllib.request

# ----------------------------------------------------------------------------- caminhos
AQUI = os.path.dirname(os.path.abspath(__file__))          # .../hci_fund_radar/vps
RAIZ = os.path.dirname(AQUI)                               # .../hci_fund_radar (o clone)
DATA = os.path.join(RAIZ, "data")
LOGS = os.path.join(AQUI, "logs")
ENV_ARQ = os.path.join(AQUI, ".env")
ESTADO_ARQ = os.path.join(LOGS, "estado.json")
PYTHON = sys.executable

# ----------------------------------------------------------------------------- ritmo
INTERVALO_COMPLETA_S = 15 * 60      # rodada completa a cada 15 min
FAST_ANTES_S = 12 * 60              # fast lane abre 12 min antes do evento
FAST_DEPOIS_S = 10 * 60             # e fecha 10 min depois (ou quando o resultado aparece)
FAST_PASSO_S = 5                    # pausa entre passadas da fast lane
ATRASO_MAX_COMPLETA_S = 30 * 60     # fast lane pode segurar a completa, mas nao mais que isto
SONECA_MAX_S = 30                   # granularidade do relogio fora da fast lane

OITO = {"USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"}
IMPACTOS_FAST = {"HIGH", "MEDIUM"}

# ----------------------------------------------------------------------------- a cadeia
# (script, timeout em segundos). Mesma ordem do workflow. Timeouts folgados: cada script tem
# os proprios timeouts de rede (30-45 s por chamada) e o geopolitica tem orcamento de 8 min.
CADEIA_COMPLETA = [
    ("fxstreet_calendario.py", 120),
    ("eua_leitor.py", 180),
    ("bc_discursos.py", 300),
    ("bancos_centrais.py", 120),
    ("macro_eventos.py", 120),
    ("correlacao_juros.py", 420),
    ("noticias.py", 300),
    ("geopolitica.py", 660),
    ("sentimento.py", 180),
]
# Na fast lane so o calendario. O sentimento.py baixa 42 dias da FXStreet por conta propria:
# roda-lo a cada 5 s dobraria as batidas na fonte sem informacao nova. Ele roda UMA vez, quando
# o resultado chega (SENTIMENTO_FAST).
CADEIA_FAST = [
    ("fxstreet_calendario.py", 90),
    ("macro_eventos.py", 90),
]
SENTIMENTO_FAST = ("sentimento.py", 120)

# Exatamente os arquivos do passo "commita se mudou" do workflow. Nada fora de data/.
JSONS_COMMIT = [
    "data/macro_eventos.json",
    "data/bancos_centrais.json",
    "data/calendario_resultado.json",
    "data/eua_leitura.json",
    "data/bc_discursos.json",
    "data/sentimento.json",
    "data/correlacao_juros.json",
    "data/geopolitica.json",
    "data/noticias.json",
    "data/raw/ff_calendar_thisweek.json",
]
assert all(p.startswith("data/") for p in JSONS_COMMIT), "so data/ pode ser commitado"

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
FF_ALVO = os.path.join(DATA, "raw", "ff_calendar_thisweek.json")

GIT_ID = ["-c", "user.name=hci-bot", "-c", "user.email=bot@hokiresearch.com"]

# ----------------------------------------------------------------------------- log
log = logging.getLogger("hci-loop")


def prepara_log() -> None:
    os.makedirs(LOGS, exist_ok=True)
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    # loop.log gira sozinho: 2 MB x 5 arquivos. Nada de disco enchendo.
    arq = logging.handlers.RotatingFileHandler(
        os.path.join(LOGS, "loop.log"), maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    arq.setFormatter(fmt)
    tela = logging.StreamHandler(sys.stdout)   # o journald do systemd guarda isto tambem
    tela.setFormatter(fmt)
    log.handlers.clear()
    log.addHandler(arq)
    log.addHandler(tela)


def grava_saida_script(nome: str, texto: str) -> None:
    """Saida de cada script em vps/logs/<script>.log, com rotacao simples (1 MB -> .1)."""
    try:
        alvo = os.path.join(LOGS, nome.replace(".py", "") + ".log")
        if os.path.exists(alvo) and os.path.getsize(alvo) > 1_000_000:
            shutil.move(alvo, alvo + ".1")     # sobrescreve o .1 anterior
        with open(alvo, "a", encoding="utf-8", errors="replace") as f:
            f.write(texto)
    except Exception as e:                      # log nunca derruba o loop
        log.warning("nao consegui gravar o log de %s: %s", nome, e)


def carrega_env() -> None:
    """vps/.env (BLS_API_KEY=...) — o systemd ja injeta via EnvironmentFile; isto serve para
    rodar na mao. Nunca sobrescreve variavel que ja existe no ambiente."""
    if not os.path.exists(ENV_ARQ):
        return
    try:
        with open(ENV_ARQ, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                k, v = linha.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        log.warning("nao consegui ler %s: %s", ENV_ARQ, e)


# ----------------------------------------------------------------------------- utilidades
def agora() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def sha(caminho: str) -> str | None:
    try:
        with open(caminho, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def fotografa() -> dict:
    return {p: sha(os.path.join(RAIZ, p)) for p in JSONS_COMMIT}


def grava_estado(**campos) -> None:
    """vps/logs/estado.json — um batimento para o dono conferir sem ler log."""
    try:
        est = {}
        if os.path.exists(ESTADO_ARQ):
            with open(ESTADO_ARQ, encoding="utf-8") as f:
                est = json.load(f)
        est.update(campos)
        est["atualizado_em"] = agora().isoformat()
        with open(ESTADO_ARQ + ".tmp", "w", encoding="utf-8") as f:
            json.dump(est, f, ensure_ascii=False, indent=1)
        os.replace(ESTADO_ARQ + ".tmp", ESTADO_ARQ)
    except Exception as e:
        log.warning("estado.json: %s", e)


# ----------------------------------------------------------------------------- scripts
def roda_script(nome: str, timeout_s: int) -> bool:
    """Um script, um subprocesso, um timeout. Nunca levanta excecao: devolve True/False."""
    caminho = os.path.join(RAIZ, nome)
    if not os.path.exists(caminho):
        log.error("%s nao existe em %s — pulado", nome, RAIZ)
        return False
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    t0 = time.monotonic()
    try:
        r = subprocess.run([PYTHON, caminho], cwd=RAIZ, env=env, capture_output=True,
                           timeout=timeout_s)
        dur = time.monotonic() - t0
        saida = (r.stdout or b"").decode("utf-8", "replace") + \
                (r.stderr or b"").decode("utf-8", "replace")
        grava_saida_script(nome, "\n===== %s  rc=%s  %.1fs =====\n%s" %
                           (agora().isoformat(timespec="seconds"), r.returncode, dur, saida))
        if r.returncode == 0:
            log.info("ok   %-24s %5.1fs", nome, dur)
            return True
        # rc 1 = fonte nao respondeu (arquivo anterior preservado); rc 2 = cota do BLS.
        log.warning("FALHA %-22s rc=%s %5.1fs — segue a cadeia (arquivo anterior mantido)",
                    nome, r.returncode, dur)
        return False
    except subprocess.TimeoutExpired as e:
        dur = time.monotonic() - t0
        saida = ((e.stdout or b"").decode("utf-8", "replace") if e.stdout else "") + \
                ((e.stderr or b"").decode("utf-8", "replace") if e.stderr else "")
        grava_saida_script(nome, "\n===== %s  TIMEOUT %ds =====\n%s" %
                           (agora().isoformat(timespec="seconds"), timeout_s, saida))
        log.warning("TIMEOUT %-20s apos %ds — morto, segue a cadeia", nome, timeout_s)
        return False
    except Exception as e:
        log.error("erro inesperado rodando %s: %s", nome, e)
        return False


def baixa_feed_reserva() -> None:
    """O feed semanal do Forex Factory — a RESERVA do calendario. So troca o arquivo se veio
    JSON valido e nao vazio (mesma regra do workflow)."""
    os.makedirs(os.path.dirname(FF_ALVO), exist_ok=True)
    ultimo_erro = None
    for _tentativa in range(3):
        try:
            req = urllib.request.Request(FF_URL, headers={"User-Agent": "hci-fund-radar/vps"})
            with urllib.request.urlopen(req, timeout=60) as r:
                cru = r.read()
            d = json.loads(cru.decode("utf-8"))
            n = len(d if isinstance(d, list) else d.get("events", []))
            if n <= 0:
                log.warning("feed FF veio vazio — mantido o anterior")
                return
            with open(FF_ALVO + ".novo", "wb") as f:
                f.write(cru)
            os.replace(FF_ALVO + ".novo", FF_ALVO)
            log.info("ok   feed de reserva (FF)     %d eventos", n)
            return
        except Exception as e:
            ultimo_erro = e
            time.sleep(2)
    log.warning("feed FF falhou (%s) — mantido o anterior", ultimo_erro)
    try:
        if os.path.exists(FF_ALVO + ".novo"):
            os.remove(FF_ALVO + ".novo")
    except OSError:
        pass


def roda_cadeia(cadeia: list, com_feed: bool) -> None:
    t0 = time.monotonic()
    if com_feed:
        try:
            baixa_feed_reserva()
        except Exception as e:         # cinto e suspensorio
            log.error("feed de reserva: %s", e)
    for nome, timeout_s in cadeia:
        roda_script(nome, timeout_s)
    log.info("cadeia %s terminou em %.0fs", "completa" if com_feed else "fast",
             time.monotonic() - t0)


# ----------------------------------------------------------------------------- fast lane
def parse_utc(s: str) -> dt.datetime | None:
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def le_eventos() -> list:
    try:
        with open(os.path.join(DATA, "macro_eventos.json"), encoding="utf-8") as f:
            return json.load(f).get("eventos", []) or []
    except Exception as e:
        log.warning("macro_eventos.json ilegivel (%s) — sem fast lane nesta volta", e)
        return []


def elegivel(e: dict) -> dt.datetime | None:
    """Devolve a hora do evento se ele merece fast lane: HIGH/MEDIUM, 8 moedas, com hora
    marcada (nao 'dia inteiro'), nao discurso, data confirmada, e ainda sem resultado."""
    if str(e.get("impacto", "")).upper() not in IMPACTOS_FAST:
        return None
    if e.get("moeda") not in OITO:
        return None
    if e.get("resultado") is not None:
        return None
    if e.get("discurso") or e.get("data_a_confirmar"):
        return None       # discurso nunca tem 'resultado'; nao vale 22 min de pancada na fonte
    q = parse_utc(e.get("quando_utc") or "")
    if q is None or (q.hour == 0 and q.minute == 0 and q.second == 0):
        return None       # 00:00:00 = evento de dia inteiro (feriado, reuniao do G20)
    return q


def eventos_fast(ev: list, ref: dt.datetime) -> list:
    """Os eventos que estao na janela AGORA: [-10 min, +12 min] em volta da hora marcada."""
    fora = []
    for e in ev:
        q = elegivel(e)
        if q is None:
            continue
        delta = (q - ref).total_seconds()
        if -FAST_DEPOIS_S <= delta <= FAST_ANTES_S:
            fora.append(e)
    return fora


def proximo_evento_fast(ev: list, ref: dt.datetime) -> dt.datetime | None:
    """Hora do proximo evento elegivel ainda por vir (para o loop dormir ate la)."""
    melhor = None
    for e in ev:
        q = elegivel(e)
        if q is not None and q > ref and (melhor is None or q < melhor):
            melhor = q
    return melhor


def chave(e: dict) -> tuple:
    return (e.get("moeda"), e.get("titulo"), e.get("quando_utc"))


def rotulo(e: dict) -> str:
    return "%s %s %s @%s UTC" % (e.get("moeda"), str(e.get("impacto", "")).upper(),
                                 e.get("titulo"), (e.get("quando_utc") or "")[11:16])


# ----------------------------------------------------------------------------- git
def git(*args, timeout_s: int = 120) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["GIT_EDITOR"] = "true"          # rebase --continue nunca abre editor
    env["GIT_TERMINAL_PROMPT"] = "0"    # nunca pede senha no terminal
    return subprocess.run(["git", *GIT_ID, *args], cwd=RAIZ, env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout_s)


def rebase_em_andamento() -> bool:
    for pasta in ("rebase-merge", "rebase-apply"):
        r = git("rev-parse", "--git-path", pasta)
        p = r.stdout.strip()
        if r.returncode == 0 and p and os.path.exists(os.path.join(RAIZ, p) if not os.path.isabs(p) else p):
            return True
    return False


def saneia_git() -> None:
    """Se o processo morreu (SIGINT, queda) no meio de um rebase, o clone acorda com o rebase
    pela metade e HEAD solto. Commitar em cima disso e a receita para perder tudo. Aborta."""
    if rebase_em_andamento():
        log.warning("rebase pela metade encontrado (queda anterior) — abortando antes de seguir")
        git("rebase", "--abort")


def resolve_conflitos_local_vence() -> bool:
    """No meio de um `pull --rebase`, o commit LOCAL e o que esta sendo reaplicado, e o git
    chama isso de --theirs. Para data/*.json fica a versao local; qualquer outro arquivo em
    conflito aborta (nao deveria existir: so commitamos data/)."""
    for _ in range(5):
        r = git("diff", "--name-only", "--diff-filter=U")
        conflitados = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        if not conflitados:
            return True
        for f in conflitados:
            if not (f.startswith("data/") and f.endswith(".json")):
                log.error("conflito fora de data/*.json (%s) — abortando o rebase", f)
                return False
            git("checkout", "--theirs", "--", f)
            git("add", "--", f)
        r = git("rebase", "--continue")
        if r.returncode == 0:
            return True
    return False


def publica(motivo: str, dry: bool = False) -> bool:
    """git add (so a lista) -> commit se mudou -> pull --rebase (local vence) -> push.
    Nunca levanta excecao. Devolve True se publicou."""
    try:
        existentes = [p for p in JSONS_COMMIT if os.path.exists(os.path.join(RAIZ, p))]
        if dry:
            r = git("status", "--porcelain", "--", *existentes)
            mudados = [l[3:] for l in r.stdout.splitlines() if l.strip()]
            log.info("[seco] git add de %d arquivos; mudados agora: %s",
                     len(existentes), mudados or "nenhum")
            return False
        saneia_git()
        git("add", "--", *existentes)
        if git("diff", "--cached", "--quiet").returncode == 0:
            # nada novo para commitar — mas pode haver commit de uma volta anterior cujo push
            # falhou (deploy key ausente, rede). Se houver, tenta empurrar; senao, sai.
            r = git("rev-list", "--count", "@{u}..HEAD")
            pendentes = int(r.stdout.strip() or 0) if r.returncode == 0 else 0
            if pendentes <= 0:
                log.info("nada mudou — sem commit")
                return False
            log.info("nada mudou, mas ha %d commit(s) local(is) sem push — tentando de novo",
                     pendentes)
        else:
            ts = agora().strftime("%Y-%m-%dT%H:%MZ")
            r = git("commit", "-q", "-m", "macro direction %s (vps, %s)" % (ts, motivo))
            if r.returncode != 0:
                log.error("commit falhou: %s", (r.stderr or r.stdout).strip()[:400])
                return False
        # --autostash: se algum arquivo rastreado que NAO commitamos estiver sujo (ex.: outro
        # arquivo de data/ que um script tocou), ele vai e volta do stash sem quebrar o rebase.
        r = git("pull", "--rebase", "--autostash", "origin", "main", timeout_s=180)
        if r.returncode != 0:
            erro = (r.stderr or r.stdout).strip()[:400]
            if not rebase_em_andamento():
                # nao e conflito: e rede, SSH, deploy key. Nada a resolver aqui.
                log.error("pull falhou (sem conflito): %s", erro)
                log.error("  (se for a primeira vez: a deploy key ja esta no GitHub com WRITE?)")
                return False
            log.warning("pull --rebase parou em conflito: %s", erro)
            if not resolve_conflitos_local_vence():
                git("rebase", "--abort")
                log.error("rebase abortado — o commit fica local e tenta de novo na proxima")
                return False
            log.info("conflito em data/*.json resolvido: versao local venceu")
        r = git("push", "-q", "origin", "main", timeout_s=180)
        if r.returncode != 0:
            log.error("push falhou: %s", (r.stderr or r.stdout).strip()[:400])
            log.error("  (se for a primeira vez: a deploy key ja esta no GitHub com WRITE?)")
            return False
        log.info("publicado no GitHub (%s)", motivo)
        grava_estado(ultimo_push=agora().isoformat(), ultimo_push_motivo=motivo)
        return True
    except Exception as e:
        log.error("publicacao falhou de forma inesperada: %s", e)
        try:
            git("rebase", "--abort")
        except Exception:
            pass
        return False


# ----------------------------------------------------------------------------- modos
def passada_seca() -> int:
    """--uma-vez: mostra o que o loop faria, sem rodar script e sem tocar no git."""
    log.info("PASSADA SECA — nada sera executado, nada sera commitado")
    log.info("raiz do clone : %s", RAIZ)
    log.info("python        : %s (%s)", PYTHON, sys.version.split()[0])
    log.info("BLS_API_KEY   : %s", "presente" if os.environ.get("BLS_API_KEY")
             else "AUSENTE (cota 25/dia)")
    ok = True
    log.info("cadeia completa (a cada %d min):", INTERVALO_COMPLETA_S // 60)
    log.info("   feed de reserva FF -> %s", FF_ALVO)
    for nome, t in CADEIA_COMPLETA:
        existe = os.path.exists(os.path.join(RAIZ, nome))
        ok &= existe
        log.info("   %-24s timeout %4ds  %s", nome, t, "" if existe else "<<< NAO ENCONTRADO")
    log.info("fast lane (a cada %ds; abre %d min ANTES do evento, fecha %d min DEPOIS ou "
             "quando o resultado sai):", FAST_PASSO_S, FAST_ANTES_S // 60, FAST_DEPOIS_S // 60)
    for nome, t in CADEIA_FAST:
        log.info("   %-24s timeout %4ds", nome, t)
    log.info("   %-24s timeout %4ds  (so quando o resultado chega)", *SENTIMENTO_FAST)
    ev = le_eventos()
    ref = agora()
    log.info("macro_eventos.json: %d eventos lidos", len(ev))
    ativos = eventos_fast(ev, ref)
    log.info("na janela AGORA (%s): %s", ref.strftime("%H:%M UTC"),
             "; ".join(rotulo(e) for e in ativos) or "nenhum")
    prox = proximo_evento_fast(ev, ref)
    if prox:
        falta = (prox - ref).total_seconds()
        log.info("proximo evento elegivel: %s (em %.0f min) — fast lane abriria em %.0f min",
                 prox.isoformat(timespec="minutes"), falta / 60,
                 max(0.0, falta - FAST_ANTES_S) / 60)
    else:
        log.info("nenhum evento elegivel por vir no arquivo atual")
    futuros = [e for e in ev if elegivel(e) is not None and elegivel(e) > ref]
    futuros.sort(key=lambda e: e.get("quando_utc") or "")
    for e in futuros[:8]:
        log.info("   por vir: %s", rotulo(e))
    r = git("rev-parse", "--is-inside-work-tree")
    if r.returncode == 0 and r.stdout.strip() == "true":
        b = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        rem = git("remote", "get-url", "origin").stdout.strip()
        log.info("git: branch %s, origin %s", b, rem)
        publica("passada seca", dry=True)
    else:
        log.warning("git: %s nao parece um clone (ou git nao esta no PATH)", RAIZ)
    log.info("PASSADA SECA terminou %s", "sem problemas" if ok else "COM SCRIPT FALTANDO")
    return 0 if ok else 1


def uma_rodada() -> int:
    """--uma-rodada: roda a cadeia completa uma vez e diz o que mudou. Sem git."""
    antes = fotografa()
    roda_cadeia(CADEIA_COMPLETA, com_feed=True)
    depois = fotografa()
    mudou = [p for p in JSONS_COMMIT if antes.get(p) != depois.get(p)]
    log.info("arquivos que mudaram: %s", mudou or "nenhum")
    log.info("(sem commit e sem push neste modo)")
    return 0


def loop_para_sempre() -> None:
    log.info("LOOP ligado — raiz %s — python %s", RAIZ, sys.version.split()[0])
    grava_estado(ligado_em=agora().isoformat())
    try:
        saneia_git()                       # queda no meio de um rebase nao pode virar heranca
    except Exception as e:
        log.warning("saneamento do git na partida: %s", e)
    proxima_completa = agora()             # a primeira rodada e ja
    anunciados = set()                     # eventos ja anunciados no log da fast lane

    while True:
        try:
            ref = agora()
            ev = le_eventos()
            ativos = eventos_fast(ev, ref)
            completa_vencida = ref >= proxima_completa
            muito_atrasada = ref >= proxima_completa + dt.timedelta(seconds=ATRASO_MAX_COMPLETA_S)

            if ativos and not muito_atrasada:
                # ---------------- FAST LANE: so o calendario, a cada 5 s, ate sair o numero
                for e in ativos:
                    if chave(e) not in anunciados:
                        log.info("FAST LANE aberta: %s", rotulo(e))
                        anunciados.add(chave(e))
                roda_cadeia(CADEIA_FAST, com_feed=False)
                # So o RESULTADO justifica commit. Os JSONs mudam a cada passada pelo carimbo
                # de hora; publicar isso seria um push a cada 5 s durante 22 min, sem
                # informacao — e o GitHub Pages limita as builds por hora.
                depois = {chave(x): x.get("resultado") for x in le_eventos()}
                chegaram = [e for e in ativos if depois.get(chave(e)) is not None]
                if chegaram:
                    for e in chegaram:
                        log.info("RESULTADO chegou: %s = %s", rotulo(e), depois[chave(e)])
                    roda_script(*SENTIMENTO_FAST)
                    publica("fast lane: " + "; ".join(rotulo(e) for e in chegaram)[:120])
                grava_estado(ultima_fast=agora().isoformat(),
                             fast_eventos=[rotulo(e) for e in ativos])
                time.sleep(FAST_PASSO_S)
                continue

            if completa_vencida:
                # ---------------- RODADA COMPLETA
                anunciados.clear()
                inicio = agora()
                log.info("RODADA COMPLETA comecando")
                antes = fotografa()
                roda_cadeia(CADEIA_COMPLETA, com_feed=True)
                if fotografa() != antes:
                    publica("rodada completa")
                else:
                    log.info("nada mudou nesta rodada")
                proxima_completa = inicio + dt.timedelta(seconds=INTERVALO_COMPLETA_S)
                if proxima_completa < agora() + dt.timedelta(seconds=60):
                    proxima_completa = agora() + dt.timedelta(seconds=60)
                grava_estado(ultima_completa=agora().isoformat(),
                             proxima_completa=proxima_completa.isoformat())
                continue

            # ---------------- DORMIR ate o que vier primeiro: proxima completa ou proxima janela
            ref = agora()
            espera = (proxima_completa - ref).total_seconds()
            prox = proximo_evento_fast(ev, ref)
            if prox is not None:
                abre = (prox - ref).total_seconds() - FAST_ANTES_S
                espera = min(espera, abre)
            time.sleep(max(1.0, min(SONECA_MAX_S, espera)))

        except KeyboardInterrupt:
            log.info("interrompido pelo teclado — saindo")
            return
        except Exception as e:
            # A LEI: o loop nao morre. Registra, respira 30 s, volta.
            log.exception("erro nao previsto no loop: %s", e)
            time.sleep(30)


def main() -> int:
    prepara_log()
    carrega_env()
    if "--uma-vez" in sys.argv:
        return passada_seca()
    if "--uma-rodada" in sys.argv:
        return uma_rodada()
    loop_para_sempre()
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
