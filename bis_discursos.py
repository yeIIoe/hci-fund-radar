# -*- coding: utf-8 -*-
"""DISCURSOS PELO ARQUIVO DO BIS — a porta que destrava RBA, RBNZ e SNB.

POR QUE ESTE ARQUIVO EXISTE
    O bc_discursos.py bate na porta de cada banco central. Tres portas ficam fechadas, e
    isto esta MEDIDO em data/bc_discursos.json ("status_fontes"):

        AUD  RBA   403 — bloqueia automacao por politica propria      NAO CONECTADO
        NZD  RBNZ  403 — idem                                         NAO CONECTADO
        CHF  SNB   404 — nao publica feed nas rotas conhecidas        NAO CONECTADO

    Consequencia real: AUD, NZD e CHF nunca tiveram UMA fala oficial no painel, e o buraco
    foi tapado com manchete de imprensa — o AUD chegou a exibir "38 discursos" que eram
    manchetes do Google News, com realestate.com.au entre as fontes.

    Em vez de insistir na porta que fecha, este coletor usa o ARQUIVO DO BIS — "Central
    bankers' speeches" (https://www.bis.org/cbspeeches/) — que agrega, com curadoria e para
    uso de pesquisa, os discursos de TODOS os bancos centrais, inclusive os tres bloqueados.

O QUE FOI TESTADO AO VIVO (06/set/2026), rota por rota
    https://www.bis.org/doclist/cbspeeches.rss              200  RDF 1.0, 50 itens, TODOS os bancos
    https://www.bis.org/cbspeeches/index.htm                200  pagina de busca (traz os filtros)
    https://www.bis.org/speeches/central-bank?...           200  busca: keywords, start_date,
                                                                 end_date, person[], topics[], page
    https://www.bis.org/list/cbspeeches/index.rss           404
    https://www.bis.org/doclist/cbspeeches.htm              404
    https://www.bis.org/doclist/all_speeches.rss            404
    https://www.bis.org/doclist/cbspeeches.rss?person=NNN   200 porem IGNORA o parametro (0 itens)

    NAO EXISTE filtro por instituicao. Existe filtro por PESSOA (person[]=id): a pagina de
    busca traz um <select name="person[]"> com 747 oradores, com id e contagem de falas ao
    lado. Testado: person[]=36653 (Adrian Orr) devolve as 32 falas do Governador do RBNZ, 10
    por pagina, em ordem decrescente de data. E preciso. Ja a busca por PALAVRA e imprecisa:
    "Reserve Bank of Australia" trouxe 13 acertos em 30 cartoes — os outros 17 apenas CITAM o
    RBA. Por isso o caminho e: person[] gera os CANDIDATOS, e a INSTITUICAO E CONFERIDA na
    descricao de cada item. Quem manda e a descricao, nunca o id do orador.

    Prova de que a conferencia e necessaria: Anna Breman (id 36749) tem 7 falas no BIS, mas
    so a de 21/abr/2026 e do RBNZ; as outras 6 sao do Sveriges Riksbank, de quando ela era
    vice-governadora la. Essas 6 saem daqui como fora do escopo, nao como fala do RBNZ.

FORMATO DE CADA ITEM DO BIS (medido no RSS e na busca)
    titulo            <title> / class="card-heading"
    orador            <dc:creator> / class="card-author"
    instituicao       NAO vem em campo proprio (<cb:institutionAbbrev> e sempre "BIS"):
                      vem escrita na DESCRICAO — "Speech by Ms Michele Bullock, Governor of
                      the Reserve Bank of Australia, at the Anika Foundation ..."
    data              DUAS datas, e a diferenca importa (veja abaixo)
    link              pagina HTML em /speeches/AAAAMMDD-slug  +  o mesmo slug com .pdf
    resumo            a propria descricao

AS DUAS DATAS — e a DEFASAGEM, que e o limite honesto deste coletor
    data_discurso           quando o dirigente falou. Vem do FIM da descricao ("... Sydney,
                            28 July 2026.").
    data_publicacao_bis     quando o BIS publicou no arquivo. Vem do <dc:date> / card-date.
                            E o que o proprio BIS rotula, de forma confusa, de "Date
                            delivered" na pagina do discurso.

    Medido em 06/set/2026 sobre os itens reais (o numero do dia sai no campo "defasagem_bis"
    do JSON): a mediana geral fica em poucos dias, mas as falas RECENTES chegam com 19 a 31
    dias de atraso — a Bullock de 28/jul/2026 so apareceu no BIS em 17/ago/2026, 20 dias
    depois.

    LIMITE, escrito sem rodeio: ISTO SERVE PARA HISTORICO E CONTEXTO, NAO PARA REACAO NO
    MINUTO. Quem precisa de fala no minuto continua dependendo do site do proprio banco — e
    para RBA, RBNZ e SNB esse caminho segue fechado.

O CORPO DO TEXTO
    A pagina HTML do BIS traz so um RESUMO (~2 mil caracteres). O texto integral esta no PDF
    do proprio BIS (medido: Bullock, 18 paginas, 25.380 caracteres). Este coletor baixa o PDF
    apenas dos itens dentro da janela do sentimento e ate um teto por banco — PDF custa de 2
    a 9 segundos cada. Fora da janela, o item vai para o historico so com metadados, e isso
    fica gravado no proprio item ("corpo_origem"), nunca disfarcado de texto lido.

FILTRO DE ASSUNTO — a MESMA regua, importada, nao copiada
    As listas de exclusao (cedula, aniversario, homenagem, premio, museu, nomeacao) e de
    inclusao (politica monetaria, inflacao, juros, economia, trabalho, estabilidade), o
    limiar de termos fortes no corpo, os marcadores hawkish/dovish e o leitor de falas vem
    IMPORTADOS de bc_discursos.py. Se o dono mudar a regua la, muda aqui junto. Todo descarte
    sai com o motivo escrito em "descartados": nada some em silencio.

SAIDAS
    data/bis_discursos.json            mesmo formato de data/bc_discursos.json (gerado_em,
                                       status_fontes, aviso, marcadores, itens, descartados),
                                       com "procedencia" BIS e as duas datas em cada item.
                                       So a JANELA do sentimento, ja classificada.
    data/bis_discursos_historico.jsonl arquivo APPEND-ONLY, uma linha por fala, com o maximo
                                       de historico que o BIS entrega. Reexecucao nao duplica:
                                       link ja gravado nao volta.

LEIS DA CASA respeitadas
    Nada de probabilidade sem fonte. Campo sem fonte e null COM o motivo escrito. Limiar novo
    sai rotulado PROVISORIO. Se a coleta falhar inteira, sai com codigo 1 e PRESERVA o arquivo
    anterior.
"""
from __future__ import annotations

import datetime as dt
import html as H
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# A REGUA E IMPORTADA, NAO COPIADA: o filtro de assunto, os marcadores e o leitor de falas
# sao literalmente os mesmos do bc_discursos.py. Mudou la, muda aqui.
from bc_discursos import (COMUNICADO_TITULO, DOVISH, EXCLUSAO_ASSUNTO, FORTES_CORPO, HAWKISH,
                          INCLUSAO_ASSUNTO, MIN_FORTES_CORPO, PESO_ORIGEM, POSTURA,
                          PROPORCAO_MINIMA_LEGIVEL, assunto_de, bloco_leitor, chave_titulo,
                          contem, frases_de_postura, proporcao_legivel, sem_acento)
from leitor_falas import vereditos_por_moeda

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "data", "bis_discursos.json")
HISTORICO = os.path.join(AQUI, "data", "bis_discursos_historico.jsonl")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9"}

BASE = "https://www.bis.org"
RSS = BASE + "/doclist/cbspeeches.rss"
BUSCA = BASE + "/speeches/central-bank"
PAGINA_FILTROS = BASE + "/cbspeeches/index.htm"

JANELA_SENTIMENTO = 42     # dias — a janela que o sentimento usa; e o recorte do JSON
MAX_CORPO_POR_BANCO = 8    # PDFs por banco por execucao (custa de 2 a 9 s cada)
PAGINAS_BLOQUEADOS = 10    # paginas de historico por dirigente dos tres bancos bloqueados
PAGINAS_VALIDACAO = 2      # paginas por dirigente dos cinco ja conectados (so p/ validar)
PAUSA = 0.35               # segundos entre requisicoes ao BIS — educacao com o servidor
PDF_MAX_BYTES = 8_000_000

# ------------------------------------------------------------------ quem e de qual instituicao
# "regex" e a AUTORIDADE: casa contra o trecho de FILIACAO da descricao do BIS (o pedaco antes
# do local do evento). "oradores" sao apenas CANDIDATOS — os ids do <select name="person[]">
# da pagina de busca, colhidos em 06/set/2026. Se o BIS renumerar, o casamento por NOME (em
# ids_por_nome) reconstroi os ids sozinho: nenhum id fica congelado no codigo.
BANCOS = {
    "AUD": {"banco": "RBA", "bloqueado_no_site": True,
            "regex": r"Reserve Bank of Australia|\bRBA\b",
            "oradores": ["Michele Bullock", "Andrew Hauser", "Christopher Kent", "Sarah Hunter",
                         "Brad Jones", "Philip Lowe", "Guy Debelle", "Luci Ellis",
                         "Marion Kohler", "Glenn Stevens", "Ric Battellino", "Malcolm Edey"]},
    "NZD": {"banco": "RBNZ", "bloqueado_no_site": True,
            "regex": r"Reserve Bank of New Zealand|\bRBNZ\b|Te P[uū]tea Matua",
            "oradores": ["Anna Breman", "Christian Hawkesby", "Adrian Orr", "Karen Silk",
                         "Simone Robbers", "Geoff Bascand", "Grant Spencer", "Graeme Wheeler",
                         "Alan Bollard", "John McDermott"]},
    "CHF": {"banco": "SNB", "bloqueado_no_site": True,
            "regex": r"Swiss National Bank|\bSNB\b|Banque nationale suisse",
            "oradores": ["Martin Schlegel", "Antoine Martin", "Petra Tschudin", "Thomas Jordan",
                         "Andréa M Maechler", "Fritz Zurbrügg", "Thomas Moser",
                         "Jean-Pierre Danthine", "Philipp Hildebrand", "Jean-Pierre Roth"]},
    "USD": {"banco": "Fed", "bloqueado_no_site": False,
            "regex": r"Federal Reserve",
            "oradores": ["Jerome H Powell", "Christopher J Waller", "Michelle W Bowman",
                         "Philip N Jefferson", "Michael S Barr", "Lisa D Cook",
                         "Adriana D Kugler", "John C Williams", "Lorie K Logan",
                         "Alberto G Musalem", "Stephen I Miran"]},
    "EUR": {"banco": "ECB", "bloqueado_no_site": False,
            # DELIBERADO: so o BCE. Os governadores nacionais da zona do euro (Bundesbank,
            # Banque de France, ...) tambem votam no Conselho e ESTAO no arquivo do BIS, mas
            # inclui-los mudaria o que "EUR" significa em relacao ao bc_discursos.py, que so
            # le o site do BCE. A decisao e do dono; aqui fica registrada, nao tomada.
            "regex": r"European Central Bank|\bECB\b",
            "oradores": ["Christine Lagarde", "Luis de Guindos", "Philip R Lane",
                         "Isabel Schnabel", "Piero Cipollone", "Frank Elderson"]},
    "GBP": {"banco": "BoE", "bloqueado_no_site": False,
            "regex": r"Bank of England",
            "oradores": ["Andrew Bailey", "David Ramsden", "Huw Pill", "Sarah Breeden",
                         "Clare Lombardelli"]},
    "JPY": {"banco": "BoJ", "bloqueado_no_site": False,
            "regex": r"Bank of Japan",
            "oradores": ["Kazuo Ueda", "Ryozo Himino", "Shinichi Uchida", "Seiji Adachi",
                         "Toyoaki Nakamura", "Asahi Noguchi", "Junko Nakagawa",
                         "Hajime Takata", "Naoki Tamura"]},
    "CAD": {"banco": "BoC", "bloqueado_no_site": False,
            "regex": r"Bank of Canada",
            "oradores": ["Tiff Macklem", "Carolyn Rogers", "Sharon Kozicki", "Toni Gravelle",
                         "Rhys R Mendes"]},
}

MESES = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"])}
MESES_CURTO = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


# ------------------------------------------------------------------------------------ rede
def busca_texto(url: str, tentativas: int = 2) -> str:
    """GET com User-Agent de navegador. O BIS responde 200 a automacao — ao contrario do RBA
    e do RBNZ, que devolvem 403 exatamente ao mesmo cabecalho."""
    ultimo = None
    for t in range(tentativas):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:      # noqa: BLE001 — qualquer falha de rede vale nova tentativa
            ultimo = e
            time.sleep(1.0 + t)
    raise ultimo


def busca_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(PDF_MAX_BYTES + 1)


def url_busca(**params) -> str:
    return BUSCA + "?" + urllib.parse.urlencode(params)


# ------------------------------------------------------------------------------- leitura
CARTAO = re.compile(r'<a href="(/speeches/[^"]+)" class="card-link">(.*?)</a>', re.S)


def limpa(t):
    """Tira tag, desfaz entidade HTML e colapsa espaco. None entra, None sai."""
    if t is None:
        return None
    return H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))).strip()


def cartoes_da_busca(html_pagina: str) -> list:
    """Le os cartoes de resultado da busca do BIS.

    Cada cartao traz: tipo (badge), data de publicacao do BIS (card-date), titulo
    (card-heading), descricao (card-description, onde mora a INSTITUICAO) e o autor.
    """
    saida = []
    for m in CARTAO.finditer(html_pagina):
        bloco = m.group(2)

        def campo(padrao, _b=bloco):
            x = re.search(padrao, _b, re.S)
            return limpa(x.group(1)) if x else None

        saida.append({
            "link": BASE + m.group(1),
            "tipo_bis": campo(r'class="badge[^"]*"[^>]*>(.*?)</span>'),
            "data_bis_texto": campo(r'class="card-date fs-sm">(.*?)</span>'),
            "titulo": campo(r'class="card-heading">(.*?)</h5>'),
            "descricao": campo(r'class="card-description">(.*?)</div>'),
            "autor": campo(r'class="fs-sm card-author__link"[^>]*>(.*?)</a>'),
            "fonte_bis": "busca por dirigente (person[])",
        })
    return saida


def itens_do_rss(xml: str) -> list:
    """O RSS do BIS e RDF 1.0. O primeiro <item> do XML e o indice <rdf:Seq>, nao uma fala —
    por isso o item so entra se tiver <dc:date>, que o indice nao tem."""
    saida = []
    for bloco in re.findall(r"<item[^>]*>(.*?)</item>", xml, re.S):
        def campo(tag, _b=bloco):
            x = re.search(r"<%s[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (tag, tag), _b, re.S)
            return limpa(x.group(1)) if x else None

        data = campo("dc:date")
        link = campo("link")
        if not data or not link:
            continue
        saida.append({"link": link, "tipo_bis": "Speech", "data_bis_texto": data,
                      "titulo": campo("title"), "descricao": campo("description"),
                      "autor": campo("dc:creator"),
                      "fonte_bis": "RSS Central bankers' speeches"})
    return saida


# -------------------------------------------------------------------------------- datas
def data_bis_de(texto):
    """Data de PUBLICACAO no arquivo do BIS. Aceita '17 Aug 2026' (busca) e ISO (RSS)."""
    if not texto:
        return None
    t = texto.strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})", t)
    if m and m.group(2).title() in MESES_CURTO:
        try:
            return dt.date(int(m.group(3)), MESES_CURTO[m.group(2).title()], int(m.group(1)))
        except ValueError:
            return None
    return None


def data_discurso_de(descricao):
    """Data em que o dirigente FALOU. O BIS a escreve no fim da descricao, depois do local:
    '..., at the Anika Foundation Fundraising Lunch, Sydney, 28 July 2026.'

    Pega a ULTIMA ocorrencia de 'DD Mes AAAA' — a primeira costuma ser o nome do evento
    ('the 2025-III Inflation Report'). Aceita intervalo ('13-14 May 2026'), ficando com o
    primeiro dia. Devolve None quando nao ha data escrita: quem chama grava o motivo, e a
    data de publicacao do BIS entra no lugar COM o aviso, jamais como se fosse a mesma coisa.
    """
    if not descricao:
        return None
    achados = re.findall(r"(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s+([A-Z][a-z]+)\s+(\d{4})",
                         descricao)
    for dia, mes, ano in reversed(achados):
        if mes in MESES:
            try:
                return dt.date(int(ano), MESES[mes], int(dia))
            except ValueError:
                continue
    return None


# ------------------------------------------------------------------------- instituicao
def trecho_de_filiacao(descricao: str) -> str:
    """O pedaco da descricao que diz DE QUEM o orador e — antes do local do evento.

    POR QUE RECORTAR: a descricao completa cita o evento, e evento cita instituicao. Sem o
    recorte, uma palestra do Fed 'at the Reserve Bank of Australia conference' viraria fala
    do RBA. O corte e no primeiro ', at ' / ', to ' / ', before ' / ', during ' — que no
    padrao do BIS separa QUEM FALA de ONDE FALOU.
    """
    partes = re.split(r",\s+(?:at|to|before|during|in front of)\s+", descricao or "", maxsplit=1)
    return partes[0]


def instituicao_de(descricao):
    """(moeda, motivo). Quem manda e a descricao, nunca o id do orador no BIS.

    Foi assim que as 6 falas da Anna Breman pelo Riksbank ficaram de fora do NZD, mesmo ela
    sendo hoje Governadora do RBNZ e mesmo o id dela sendo o que trouxe os itens.
    """
    if not descricao:
        return None, "sem descricao no item do BIS — instituicao indeterminada"
    filiacao = trecho_de_filiacao(descricao)
    casadas = [m for m, cfg in BANCOS.items() if re.search(cfg["regex"], filiacao, re.I)]
    if len(casadas) == 1:
        return casadas[0], ("filiacao do orador na descricao do BIS: %s"
                            % BANCOS[casadas[0]]["banco"])
    if len(casadas) > 1:
        return None, ("a filiacao cita %d dos bancos acompanhados (%s) — nao da para dizer de "
                      "quem e a fala" % (len(casadas), ", ".join(casadas)))
    fora = re.search(r"(?:Governor|President|Chair(?:man)?|Deputy|Member|Director)[^,]*"
                     r"\bof (?:the )?([A-Z][^,]{3,60})", filiacao)
    return None, ("instituicao fora dos oito bancos acompanhados%s"
                  % (" (%s)" % fora.group(1).strip() if fora else ""))


def orador_de(cartao: dict):
    """Nome do orador. Prefere o campo de autor do BIS; se faltar, le 'Speech by Mr X, ...'."""
    if cartao.get("autor"):
        return cartao["autor"].strip()
    m = re.search(r"\bby\s+(?:Mr|Ms|Mrs|Dr|Sir|Prof(?:essor)?)\.?\s+"
                  r"([A-Z][A-Za-zÀ-ÿ.'\-]+(?:\s+[A-Za-zÀ-ÿ.'\-]+){0,3})",
                  cartao.get("descricao") or "")
    return m.group(1).strip(" .,") if m else None


def e_comunicado(titulo, descricao) -> bool:
    """Comunicado/ata/coletiva tem o mesmo peso do discurso, com rotulo honesto diferente.

    Alem da lista importada do bc_discursos, entra o padrao proprio do SNB — 'Introductory
    remarks by the Governing Board' — que e a coletiva trimestral de politica monetaria e
    seria classificada como discurso comum sem esta linha.
    """
    alvo = ("%s %s" % (titulo or "", descricao or "")).lower()
    if any(contem(k, alvo) for k in COMUNICADO_TITULO):
        return True
    return bool(re.search(r"introductory remarks by the governing board|news conference|"
                          r"press conference|monetary policy assessment", alvo))


# ------------------------------------------------------------------------------- corpo
def texto_do_pdf(url_pdf: str):
    """(texto, motivo). O texto INTEGRAL do discurso so existe no PDF do BIS: a pagina HTML
    traz apenas um resumo de ~2 mil caracteres. Medido: Bullock, 18 paginas, 25.380 chars."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, "pypdf nao instalado nesta maquina — o PDF do BIS nao pode ser lido"
    try:
        bruto = busca_bytes(url_pdf)
    except Exception as e:      # noqa: BLE001
        return None, "PDF nao baixou: %s" % str(e)[:60]
    if len(bruto) > PDF_MAX_BYTES:
        return None, "PDF maior que o teto de %d bytes" % PDF_MAX_BYTES
    try:
        leitor = PdfReader(io.BytesIO(bruto))
        texto = " ".join((p.extract_text() or "") for p in leitor.pages)
        paginas = len(leitor.pages)
    except Exception as e:      # noqa: BLE001
        return None, "PDF nao pode ser lido: %s" % str(e)[:60]
    texto = re.sub(r"\s+", " ", texto).strip()
    if len(texto) < 400:
        return None, "PDF com so %d caracteres extraidos — provavelmente e imagem" % len(texto)
    return texto, "PDF do BIS (%d paginas, texto integral)" % paginas


def texto_da_pagina_bis(url_html: str):
    """(texto, motivo). Rede de seguranca quando o PDF falha: a pagina do BIS traz o resumo.
    Sai rotulado como RESUMO, para ninguem confundir com o discurso inteiro."""
    try:
        html_pagina = busca_texto(url_html)
    except Exception as e:      # noqa: BLE001
        return None, "pagina do BIS nao abriu: %s" % str(e)[:60]
    m = re.search(r"<article[^>]*>(.*?)</article>", html_pagina, re.S)
    corpo = m.group(1) if m else html_pagina
    corpo = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", corpo, flags=re.S)
    texto = limpa(corpo) or ""
    if len(texto) < 200:
        return None, "pagina do BIS sem texto util (%d caracteres)" % len(texto)
    return texto, "RESUMO da pagina do BIS (o integral esta no PDF, que falhou)"


# --------------------------------------------------------------------- ids dos oradores
def ids_por_nome() -> dict:
    """{nome normalizado: (id, rotulo)} lido do <select name="person[]"> da pagina de busca.

    E lido a cada execucao de proposito: se o BIS renumerar os oradores, o casamento por NOME
    reconstroi os ids sozinho — nenhum id fica congelado no codigo.
    """
    html_pagina = busca_texto(PAGINA_FILTROS)
    m = re.search(r'name="person\[\]"[^>]*>(.*?)</select>', html_pagina, re.S)
    if not m:
        return {}
    fora = {}
    for pid, rotulo in re.findall(r'<option value="(\d+)"\s*>(.*?)</option>', m.group(1), re.S):
        rotulo = H.unescape(rotulo).strip()
        nome = re.sub(r"\s*\(\d+\)\s*$", "", rotulo).strip()
        fora[sem_acento(nome).lower()] = (pid, rotulo)
    return fora


def id_do_orador(nome: str, tabela: dict):
    """Casamento EXATO ou por sufixo ('Dr Fritzi Kohler-Geib' casa 'Fritzi Kohler-Geib').

    Nada de casar por pedaco solto: 'Orr' casaria 'DeLisle Worrell' e 'Moser' casaria meio
    mundo. O erro seria silencioso — o item so cairia la na frente, no filtro de instituicao,
    depois de gastar requisicao a toa.
    """
    alvo = sem_acento(nome).lower()
    if alvo in tabela:
        return tabela[alvo]
    for chave, valor in tabela.items():
        if chave.endswith(" " + alvo):
            return valor
    return None


# ------------------------------------------------------------------------------ montagem
def monta_item(cartao: dict, moeda: str, motivo_inst: str, hoje: dt.date) -> dict:
    """Monta o item no formato do bc_discursos.json, com as DUAS datas e a procedencia BIS."""
    banco = BANCOS[moeda]["banco"]
    d_bis = data_bis_de(cartao.get("data_bis_texto"))
    d_fala = data_discurso_de(cartao.get("descricao"))
    if d_fala:
        data_usada = d_fala
        fonte_data = "data escrita na descricao do BIS"
    else:
        data_usada = d_bis
        fonte_data = ("a data do discurso NAO consta da descricao do BIS — usada a data de "
                      "publicacao do BIS, que e POSTERIOR a fala")
    defasagem = (d_bis - d_fala).days if (d_bis and d_fala) else None
    return {
        "moeda": moeda,
        "banco": banco,
        "tipo": ("statement" if e_comunicado(cartao.get("titulo"), cartao.get("descricao"))
                 else "speech"),
        "data": data_usada.isoformat() if data_usada else None,
        "data_discurso": d_fala.isoformat() if d_fala else None,
        "data_publicacao_bis": d_bis.isoformat() if d_bis else None,
        "data_fonte": fonte_data,
        "defasagem_bis_dias": defasagem,
        "idade_dias": (hoje - data_usada).days if data_usada else None,
        "orador": orador_de(cartao) or banco,
        "orador_identificado": orador_de(cartao),
        "titulo": (cartao.get("titulo") or "")[:160],
        "link": cartao["link"],
        "link_pdf": cartao["link"] + ".pdf",
        "resumo_bis": cartao.get("descricao"),
        "procedencia": {
            "agregador": "BIS",
            "arquivo": "Central bankers' speeches",
            "url_arquivo": PAGINA_FILTROS,
            "rota": cartao.get("fonte_bis"),
            "instituicao_motivo": motivo_inst,
            "nota": ("o texto e do proprio banco central, apenas RECOLHIDO pelo BIS, e chega "
                     "com defasagem de publicacao — serve para historico e contexto, nao para "
                     "reacao no minuto"),
        },
    }


def classifica(item: dict, texto, corpo_motivo: str) -> dict:
    """Aplica a regua importada do bc_discursos: assunto, origem, peso, marcadores e frases."""
    base = texto if texto else ("%s %s" % (item.get("titulo") or "", item.get("resumo_bis") or ""))
    a = assunto_de(item.get("titulo") or "", base)
    item["assunto"] = {"veredito": a["veredito"], "temas": a["temas_incluidos"],
                       "termos_fortes_no_corpo": a["termos_fortes_no_corpo"],
                       "motivo": a["motivo"],
                       "avaliado_sobre": ("corpo integral" if texto else
                                          "titulo + resumo do BIS (corpo nao baixado)")}
    if item["tipo"] == "statement":
        origem = "comunicado_ata"
        porque = "comunicado, ata ou coletiva do proprio banco, recolhido pelo BIS"
    elif item.get("orador_identificado"):
        origem = "discurso_oficial"
        porque = ("fala assinada por %s no arquivo do BIS" % item["orador_identificado"])
    else:
        origem = "comunicado_ata"
        porque = "pagina do arquivo do BIS sem orador identificavel"
    item["origem"] = origem
    item["peso"] = PESO_ORIGEM[origem]
    item["origem_motivo"] = porque
    item["corpo_origem"] = corpo_motivo
    item["caracteres"] = len(texto) if texto else None
    if texto:
        item.update(frases_de_postura(texto))
    else:
        item.update({"frases": [], "marcadores_hawkish": 0, "marcadores_dovish": 0,
                     "inclinacao_por_contagem": "none"})
        item["contagem_nota"] = ("corpo nao baixado: a contagem fica em zero por FALTA DE "
                                 "TEXTO, nao por ausencia de postura")
    return item


def linha_historico(item: dict, agora: dt.datetime) -> dict:
    """A linha do arquivo append-only. Fica enxuta: metadado + o veredito de assunto."""
    return {"visto_em": agora.isoformat(), "moeda": item["moeda"], "banco": item["banco"],
            "tipo": item["tipo"], "data": item["data"], "data_discurso": item["data_discurso"],
            "data_publicacao_bis": item["data_publicacao_bis"],
            "defasagem_bis_dias": item["defasagem_bis_dias"], "orador": item["orador"],
            "titulo": item["titulo"], "link": item["link"], "resumo_bis": item["resumo_bis"],
            "assunto": item["assunto"]["veredito"], "assunto_motivo": item["assunto"]["motivo"],
            "origem": item["origem"], "procedencia": "BIS"}


def links_ja_no_historico() -> set:
    """O que ja esta no JSONL. Append-only nao pode virar arquivo com linha repetida."""
    if not os.path.exists(HISTORICO):
        return set()
    vistos = set()
    with io.open(HISTORICO, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                vistos.add(json.loads(linha).get("link"))
            except ValueError:
                continue
    return vistos


def mediana(v: list):
    if not v:
        return None
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


# ---------------------------------------------------------------------------------- main
def main():
    agora = dt.datetime.now(dt.timezone.utc)
    hoje = agora.date()
    so_janela = "--rapido" in sys.argv     # pula o historico: so o RSS
    print("=" * 88)
    print("DISCURSOS PELO ARQUIVO DO BIS — destrava RBA, RBNZ e SNB (as tres portas fechadas)")
    print("=" * 88)

    status = {}
    brutos, vistos_link, vistos_titulo = [], set(), set()

    # ---------------------------------------------------------------- 1) RSS (todos os bancos)
    try:
        itens = itens_do_rss(busca_texto(RSS))
        print("  RSS  %-56s %d itens" % (RSS, len(itens)))
        brutos.extend(itens)
        status["_rss"] = "ok (%d itens)" % len(itens)
    except Exception as e:      # noqa: BLE001
        print("  ! RSS falhou: %s" % str(e)[:70])
        status["_rss"] = "erro: %s" % str(e)[:60]

    # ------------------------------------------------- 2) busca por dirigente (person[]=id)
    tabela_ids, oradores_sem_id = {}, []
    if not so_janela:
        try:
            tabela_ids = ids_por_nome()
            print("  IDS  <select person[]> da pagina de busca: %d oradores" % len(tabela_ids))
            status["_ids_oradores"] = "ok (%d oradores)" % len(tabela_ids)
        except Exception as e:      # noqa: BLE001
            print("  ! lista de oradores falhou: %s" % str(e)[:70])
            status["_ids_oradores"] = "erro: %s" % str(e)[:60]

    for moeda, cfg in BANCOS.items():
        if not tabela_ids:
            break
        limite_paginas = PAGINAS_BLOQUEADOS if cfg["bloqueado_no_site"] else PAGINAS_VALIDACAO
        colhidos = 0
        for nome in cfg["oradores"]:
            achado = id_do_orador(nome, tabela_ids)
            if not achado:
                oradores_sem_id.append({"moeda": moeda, "banco": cfg["banco"], "orador": nome,
                                        "motivo": "nome nao esta no <select person[]> do BIS"})
                continue
            pid, rotulo = achado
            for pagina in range(limite_paginas):
                try:
                    html_pagina = busca_texto(url_busca(**{"person[]": pid, "page": pagina}))
                except Exception as e:      # noqa: BLE001
                    print("  ! %s %s pagina %d: %s" % (cfg["banco"], nome, pagina, str(e)[:50]))
                    break
                cartoes = cartoes_da_busca(html_pagina)
                if not cartoes:
                    break
                for c in cartoes:
                    c["fonte_bis"] = "busca person[]=%s (%s)" % (pid, rotulo)
                brutos.extend(cartoes)
                colhidos += len(cartoes)
                time.sleep(PAUSA)
                if len(cartoes) < 10:
                    break
        print("  BIS  %-4s %-5s %2d oradores  %4d cartoes brutos (ate %d paginas por orador)"
              % (moeda, cfg["banco"], len(cfg["oradores"]), colhidos, limite_paginas))

    if not brutos:
        print("  !! nenhum cartao veio do BIS")
        try:
            anterior = json.load(io.open(SAIDA, encoding="utf-8"))
        except Exception:      # noqa: BLE001
            anterior = None
        if anterior and anterior.get("itens"):
            print("  !! arquivo anterior PRESERVADO (%d itens)" % len(anterior["itens"]))
        sys.exit(1)

    # ---------------------------------------------------- 3) instituicao manda; dedup no meio
    itens, descartados, fora_das_oito = [], [], 0
    for c in brutos:
        if not c.get("link") or c["link"] in vistos_link:
            continue
        vistos_link.add(c["link"])
        d_bis = data_bis_de(c.get("data_bis_texto"))
        # o mesmo discurso as vezes sai em duas paginas do BIS com slugs diferentes: a chave
        # de titulo normalizado + data de publicacao pega o par que o link nao pega
        chave = (chave_titulo(c.get("titulo") or ""), d_bis.isoformat() if d_bis else "")
        if chave in vistos_titulo:
            continue
        vistos_titulo.add(chave)
        moeda, motivo = instituicao_de(c.get("descricao"))
        if not moeda:
            fora_das_oito += 1
            continue
        itens.append(monta_item(c, moeda, motivo, hoje))

    itens.sort(key=lambda x: (x["data"] or "0000-00-00"), reverse=True)

    # ------------------------------------------------ 4) corpo e classificacao (so na janela)
    baixados = {m: 0 for m in BANCOS}
    janela, aprovados = [], []
    for it in itens:
        na_janela = it["idade_dias"] is not None and 0 <= it["idade_dias"] <= JANELA_SENTIMENTO
        texto = None
        if na_janela and baixados[it["moeda"]] < MAX_CORPO_POR_BANCO:
            baixados[it["moeda"]] += 1
            texto, motivo = texto_do_pdf(it["link_pdf"])
            if not texto:
                texto, motivo = texto_da_pagina_bis(it["link"])
            if texto:
                legivel = proporcao_legivel(texto)
                if legivel < PROPORCAO_MINIMA_LEGIVEL:
                    descartados.append({
                        "moeda": it["moeda"], "banco": it["banco"], "data": it["data"],
                        "titulo": it["titulo"], "link": it["link"],
                        "orador_identificado": it["orador_identificado"],
                        "motivo": ("texto nao legivel (%.0f%% de caracteres legiveis, minimo "
                                   "provisorio %.0f%%)"
                                   % (legivel * 100, PROPORCAO_MINIMA_LEGIVEL * 100))})
                    continue
                classifica(it, texto, motivo)
            else:
                classifica(it, None, "corpo nao lido — %s" % motivo)
        elif na_janela:
            classifica(it, None, ("teto de %d corpos por banco atingido nesta execucao"
                                  % MAX_CORPO_POR_BANCO))
        else:
            classifica(it, None, ("fora da janela de %d dias: gravado so com metadados"
                                  % JANELA_SENTIMENTO))

        # filtro de ASSUNTO — a mesma regua do bc_discursos, com o motivo do descarte gravado
        if it["assunto"]["veredito"] == "excluido":
            descartados.append({"moeda": it["moeda"], "banco": it["banco"], "data": it["data"],
                                "titulo": it["titulo"], "link": it["link"],
                                "orador_identificado": it["orador_identificado"],
                                "motivo": it["assunto"]["motivo"]})
            continue
        if it["assunto"]["veredito"] == "neutro" and it["tipo"] != "statement" and na_janela:
            descartados.append({"moeda": it["moeda"], "banco": it["banco"], "data": it["data"],
                                "titulo": it["titulo"], "link": it["link"],
                                "orador_identificado": it["orador_identificado"],
                                "motivo": ("assunto neutro fora de comunicado — %s"
                                           % it["assunto"]["motivo"])})
            continue
        aprovados.append(it)
        if na_janela:
            janela.append(it)

    # ------------------------------------------------------------------- 5) leitor de falas
    # resumo_por_moeda sai com as MESMAS chaves do bc_discursos.json, para o painel e o
    # sentimento lerem os dois arquivos com um so leitor.
    resumo_janela = {}
    for m in sorted(set([i["moeda"] for i in janela] + [d["moeda"] for d in descartados])):
        do_banco = [i for i in janela if i["moeda"] == m]
        d_of = len([i for i in do_banco if i["origem"] == "discurso_oficial"])
        c_at = len([i for i in do_banco if i["origem"] == "comunicado_ata"])
        resumo_janela[m] = {
            "discurso_oficial": d_of, "comunicado_ata": c_at,
            "descartados": len([d for d in descartados if d["moeda"] == m]),
            "itens_que_votam": d_of + c_at,
            "com_orador_identificado": len([i for i in do_banco if i.get("orador_identificado")]),
            "veredito_por_orador": []}
    vereditos = vereditos_por_moeda({"itens": janela}, anotar_itens=True) if janela else {}
    for m in resumo_janela:
        resumo_janela[m]["veredito_por_orador"] = vereditos.get(m, [])

    # ------------------------------------------------------------ 6) medicoes obrigatorias
    contagem_janela = {}
    for m, cfg in BANCOS.items():
        do_banco = [i for i in janela if i["moeda"] == m]
        por_bis = [i for i in aprovados
                   if i["moeda"] == m and i["data_publicacao_bis"]
                   and 0 <= (hoje - dt.date.fromisoformat(i["data_publicacao_bis"])).days
                   <= JANELA_SENTIMENTO]
        contagem_janela[m] = {
            "banco": cfg["banco"],
            "bloqueado_no_site_do_banco": cfg["bloqueado_no_site"],
            "falas_na_janela_pela_data_do_discurso": len(do_banco),
            "falas_na_janela_pela_data_de_publicacao_bis": len(por_bis),
            "discurso_oficial": len([i for i in do_banco if i["origem"] == "discurso_oficial"]),
            "comunicado_ata": len([i for i in do_banco if i["origem"] == "comunicado_ata"]),
            "descartados": len([d for d in descartados if d["moeda"] == m]),
            "com_corpo_integral": len([i for i in do_banco
                                       if (i.get("corpo_origem") or "").startswith("PDF")]),
        }

    cobertura = {}
    for m, cfg in BANCOS.items():
        do_banco = [i for i in aprovados if i["moeda"] == m]
        datas = sorted([i["data"] for i in do_banco if i["data"]])
        cobertura[m] = {"banco": cfg["banco"], "itens": len(do_banco),
                        "primeiro": datas[0] if datas else None,
                        "ultimo": datas[-1] if datas else None,
                        "oradores": len({i["orador"] for i in do_banco}),
                        "paginas_por_orador": (PAGINAS_BLOQUEADOS if cfg["bloqueado_no_site"]
                                               else PAGINAS_VALIDACAO)}

    lags = [i["defasagem_bis_dias"] for i in aprovados
            if i["defasagem_bis_dias"] is not None and 0 <= i["defasagem_bis_dias"] <= 400]
    lags_recentes = [i["defasagem_bis_dias"] for i in aprovados
                     if i["defasagem_bis_dias"] is not None
                     and 0 <= i["defasagem_bis_dias"] <= 400 and i["data"]
                     and (hoje - dt.date.fromisoformat(i["data"])).days <= 365]
    ordenado = sorted(lags)
    defasagem = {
        "medida_em": hoje.isoformat(),
        "n_itens": len(lags),
        "mediana_dias": mediana(lags),
        "minimo_dias": ordenado[0] if ordenado else None,
        "maximo_dias": ordenado[-1] if ordenado else None,
        "p75_dias": ordenado[min(int(len(ordenado) * 0.75), len(ordenado) - 1)] if ordenado else None,
        "mediana_ultimos_365_dias": mediana(lags_recentes),
        "n_ultimos_365_dias": len(lags_recentes),
        "como_foi_medida": ("diferenca, item a item desta execucao, entre a data de publicacao "
                            "do BIS e a data do discurso escrita na propria descricao"),
        "limite": ("o BIS publica com atraso. SERVE PARA HISTORICO E CONTEXTO, NAO PARA REACAO "
                   "NO MINUTO. Fala no minuto so no site do proprio banco — e para RBA, RBNZ e "
                   "SNB esse caminho segue fechado (403, 403 e 404)."),
    }

    status_texto = {}
    for m, cfg in BANCOS.items():
        n = cobertura[m]["itens"]
        janela_n = contagem_janela[m]["falas_na_janela_pela_data_do_discurso"]
        fechado = (" O site do %s segue fechado a automacao (o BIS e o unico caminho)."
                   % cfg["banco"]) if cfg["bloqueado_no_site"] else ""
        if n and janela_n:
            # ha historico E ha fala dentro da janela: o sentimento tem o que ler
            status[m] = ("ok via BIS (%d itens, %s a %s; %d na janela de %d dias)"
                         % (n, cobertura[m]["primeiro"], cobertura[m]["ultimo"], janela_n,
                            JANELA_SENTIMENTO))
            status_texto[m] = ("conectado pelo arquivo do BIS: %d falas de %s a %s, sendo %d "
                               "dentro da janela de %d dias.%s"
                               % (n, cobertura[m]["primeiro"], cobertura[m]["ultimo"], janela_n,
                                  JANELA_SENTIMENTO, fechado))
        elif n:
            # ha historico, mas NENHUMA fala na janela. Dizer so "conectado" seria enganoso:
            # o painel mostraria fonte ligada com zero para somar. O rotulo diz as duas coisas.
            status[m] = ("historico ok via BIS (%d itens ate %s) — SEM fala na janela de %d dias"
                         % (n, cobertura[m]["ultimo"], JANELA_SENTIMENTO))
            status_texto[m] = ("historico conectado pelo arquivo do BIS (%d falas de %s a %s), "
                               "mas NENHUMA dentro da janela de %d dias: nao ha o que somar no "
                               "sentimento hoje.%s"
                               % (n, cobertura[m]["primeiro"], cobertura[m]["ultimo"],
                                  JANELA_SENTIMENTO, fechado))
        else:
            status[m] = "sem itens do %s no arquivo do BIS nesta execucao" % cfg["banco"]
            status_texto[m] = ("nenhuma fala do %s veio do arquivo do BIS nesta execucao"
                               % cfg["banco"])

    # ------------------------------------------------------------- 7) historico append-only
    ja = links_ja_no_historico()
    novos = [i for i in aprovados if i["link"] not in ja]
    os.makedirs(os.path.dirname(HISTORICO), exist_ok=True)
    with io.open(HISTORICO, "a", encoding="utf-8") as f:
        for i in sorted(novos, key=lambda x: x["data"] or ""):
            f.write(json.dumps(linha_historico(i, agora), ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------------- 8) impressao
    print()
    print("  cartoes brutos: %d  ·  fora dos oito bancos: %d  ·  itens: %d  ·  descartados: %d"
          % (len(brutos), fora_das_oito, len(aprovados), len(descartados)))
    print("  historico: +%d linhas novas em %s (total agora: %d)"
          % (len(novos), os.path.basename(HISTORICO), len(ja) + len(novos)))
    print()
    print("  COBERTURA POR BANCO (o que o BIS entregou)")
    print("  %-5s %-6s %6s  %-12s %-12s %s" % ("moeda", "banco", "itens", "primeiro", "ultimo",
                                               "oradores"))
    for m in BANCOS:
        c = cobertura[m]
        print("  %-5s %-6s %6d  %-12s %-12s %d"
              % (m, c["banco"], c["itens"], c["primeiro"] or "-", c["ultimo"] or "-",
                 c["oradores"]))
    print()
    print("  A PERGUNTA QUE DECIDE: falas na janela do sentimento (%d dias)" % JANELA_SENTIMENTO)
    print("  %-5s %-6s %-22s %-22s %s" % ("moeda", "banco", "pela data do discurso",
                                          "pela data do BIS", "com corpo integral"))
    for m in BANCOS:
        c = contagem_janela[m]
        print("  %-5s %-6s %-22d %-22d %d"
              % (m, c["banco"], c["falas_na_janela_pela_data_do_discurso"],
                 c["falas_na_janela_pela_data_de_publicacao_bis"], c["com_corpo_integral"]))
    print()
    print("  DEFASAGEM DO BIS (publicacao - discurso), n=%d: mediana %s dias, p75 %s, maximo %s"
          % (defasagem["n_itens"], defasagem["mediana_dias"], defasagem["p75_dias"],
             defasagem["maximo_dias"]))
    print("  nos ultimos 365 dias (n=%d): mediana %s dias"
          % (defasagem["n_ultimos_365_dias"], defasagem["mediana_ultimos_365_dias"]))
    print("  LIMITE: serve para historico e contexto, NAO para reacao no minuto.")
    print()
    for i in janela[:16]:
        print("  %s %-4s %-16s %-16s h=%d d=%d  %s"
              % (i["data"], i["moeda"], i["origem"], (i["orador_identificado"] or "-")[:16],
                 i["marcadores_hawkish"], i["marcadores_dovish"], i["titulo"][:40]))
    if descartados:
        print()
        print("  DESCARTADOS (motivo gravado, nada some em silencio):")
        for d in descartados[:12]:
            print("   x %s %-4s %-38s  %s" % (d["data"], d["moeda"], (d["titulo"] or "")[:38],
                                              d["motivo"][:62]))
    if oradores_sem_id:
        print()
        print("  ORADORES SEM ID NO BIS (nome mudou, ou nunca teve fala arquivada):")
        for o in oradores_sem_id[:14]:
            print("   ? %-4s %-6s %s" % (o["moeda"], o["banco"], o["orador"]))

    # ------------------------------------------------------------------------ 9) gravacao
    if not aprovados:
        try:
            anterior = json.load(io.open(SAIDA, encoding="utf-8"))
        except Exception:      # noqa: BLE001
            anterior = None
        if anterior and anterior.get("itens"):
            print("  !! nenhuma fala classificada — arquivo anterior PRESERVADO")
            sys.exit(1)

    relatorio = {
        "gerado_em": agora.isoformat(),
        "fonte": {"agregador": "BIS", "arquivo": "Central bankers' speeches",
                  "rss": RSS, "busca": BUSCA, "filtros": PAGINA_FILTROS,
                  "por_que": ("RBA e RBNZ devolvem 403 a automacao e o SNB nao tem feed nas "
                              "rotas conhecidas (404). O BIS agrega os discursos de todos os "
                              "bancos centrais, inclusive os tres, e responde 200."),
                  "como_filtra": ("o BIS NAO tem filtro por instituicao. person[]=id gera os "
                                  "candidatos e a instituicao e conferida na DESCRICAO de cada "
                                  "item — quem manda e a descricao, nunca o id.")},
        "status_fontes": status,
        "status_fontes_texto": status_texto,
        "historico_arquivo": "data/bis_discursos_historico.jsonl",
        "aviso": ("Falas recolhidas do ARQUIVO DO BIS, nao do site de cada banco. O BIS publica "
                  "com defasagem (medida nesta execucao em 'defasagem_bis'): SERVE PARA "
                  "HISTORICO E CONTEXTO, NAO PARA REACAO NO MINUTO. A contagem de marcadores "
                  "hawkish/dovish e EXTRACAO mecanica, indice grosseiro para apontar QUAL texto "
                  "ler — nao e interpretacao. O veredito por orador do leitor_falas e CONTEXTO "
                  "e NAO VOTA."),
        "defasagem_bis": defasagem,
        "janela_dias": JANELA_SENTIMENTO,
        "janela_nota": ("'itens' traz so a janela do sentimento (%d dias), ja classificada com "
                        "o corpo integral do PDF. O historico completo, com metadados, esta em "
                        "data/bis_discursos_historico.jsonl." % JANELA_SENTIMENTO),
        "falas_na_janela": contagem_janela,
        "cobertura_historico": cobertura,
        "hierarquia_pesos": PESO_ORIGEM,
        "hierarquia_nota": ("peso gravado no item para o sentimento aplicar. Este arquivo produz "
                            "discurso_oficial e comunicado_ata — o texto e do proprio banco "
                            "central, apenas recolhido pelo BIS. NAO e imprensa."),
        "filtro_assunto": {"inclusao": INCLUSAO_ASSUNTO, "exclusao": EXCLUSAO_ASSUNTO,
                           "termos_fortes_corpo": FORTES_CORPO,
                           "min_termos_fortes_no_corpo": MIN_FORTES_CORPO,
                           "provisorio": True,
                           "nota": ("regua IMPORTADA de bc_discursos.py, nao copiada. Mudou la, "
                                    "muda aqui. Limiar PROVISORIO, a calibrar pelo backtest.")},
        "resumo_por_moeda": resumo_janela,
        "veredito_por_orador": vereditos,
        "leitor_falas": bloco_leitor(),
        "marcadores": {"hawkish": HAWKISH, "dovish": DOVISH, "postura": POSTURA},
        "oradores_sem_id_no_bis": oradores_sem_id,
        "itens": janela,
        "descartados": descartados,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(relatorio, io.open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("  gravado: %s" % SAIDA)
    print("  gravado: %s" % HISTORICO)


if __name__ == "__main__":
    main()
