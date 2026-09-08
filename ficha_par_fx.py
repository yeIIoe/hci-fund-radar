# -*- coding: utf-8 -*-
"""
HCI MACRO DIRECTION — FICHA OPERACIONAL POR PAR (FX)
====================================================

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O painel hoje espalha o lado fundamental de um par por cinco arquivos: a leitura da
casa em data/sentimento.json, o que os futuros pagam em data/precificacao.json, o juro
de 2 e 10 anos em data/diferenciais.json, e os julgamentos dos agentes em
data/agentes/*/ultimo.json. Quem quiser montar a fotografia de UM par precisa abrir os
cinco e casar os campos na mao. Este modulo faz esse casamento e nada mais.

A DIVISAO DE TRABALHO, escrita e inegociavel:
  - O sistema entrega DADO e JULGAMENTO.
  - A ENTRADA e do Eduardo, pela analise tecnica dele.
Nada aqui e ordem, sinal de entrada, alvo ou promessa de retorno.

⚠️ A LINHA DURA DESTE ARQUIVO: ELE NAO CALCULA NADA.
Nao existe neste codigo uma soma, uma media, um percentual ou uma comparacao numerica
que produza numero novo. Todo numero impresso e COPIA de um campo nomeado de um dos
arquivos-fonte, e o nome do campo vai junto (bloco `numeros_citados` no JSON, e a
palavra "fonte:" no relatorio). Numero que a fonte nao tem sai como "nao medido" —
nunca estimado. Se um campo mudar de nome na camada 1, a ficha mostra "nao medido" em
vez de inventar: e a falha que a casa prefere.

O QUE SAI, POR PAR COM TESE, na ordem que o dono pediu:
  1. A ACAO em portugues, o estado e a divergencia sobre 100
  2. QUEM DA O MOTIVO — a perna dominante e a participacao dela (lei das duas pernas:
     par nao e ativo, sao duas moedas; se um par e 90% de uma perna so, ele nao e um
     par, e uma aposta naquela moeda)
  3. MESMA APOSTA — os outros pares que compartilham a perna dominante. Dois deles nao
     diversificam, DOBRAM.
  4. ATE QUANDO — o proximo evento invalidante, com data e dias que faltam
  5. QUALIDADE DA EVIDENCIA e as bandeiras (dominancia, direcao fragil, dado atrasado)
  6. O QUE O MERCADO PAGA, quando houver fonte. Onde nao houver: "sem fonte para
     comparar" — cinco dos oito bancos estao nessa situacao, e ISSO E INFORMACAO.
  7. O QUE OS AGENTES JULGARAM sobre as duas pernas, com o trecho, mais a OBJECAO do
     advogado quando houver
  8. O DIFERENCIAL DE JURO de 2 e 10 anos e a variacao em 5 dias — dado EXIBIDO, nunca
     voto (lei declarada no proprio diferenciais.json)

O QUE ESTE ARQUIVO NAO FAZ, de proposito:
  - Nao decide se o mercado "concorda" com a leitura da casa. Essa comparacao ja tem
    dono: o agente `divergencia`. A ficha COPIA o veredito dele e cita a chave. Refazer
    a comparacao aqui seria um segundo juiz sobre a mesma pergunta, com outra regua.
  - Nao converte "ja precificado" nem "nao e sobre juro" para o vocabulario de outro
    agente. Vereditos entram como o agente escreveu.
  - Nao vota. Toda linha de agente carrega vota=false e o selo experimental que o
    proprio agente gravou. Conviccao historica e null ate o backtest de 21/dez.
"""
from __future__ import annotations

import json
import os
import sys
from glob import glob

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "data")
DIR_AGENTES = os.path.join(D, "agentes")
SAIDA_JSON = os.path.join(D, "fichas_par_fx.json")
SAIDA_TXT = os.path.join(D, "fichas_par_fx.txt")

NAO_MEDIDO = "não medido"
SEM_FONTE = "sem fonte para comparar"


# --------------------------------------------------------------------------- leitura
def le(caminho, padrao=None):
    """Le um JSON. Se nao existe ou nao abre, devolve o padrao — nunca inventa."""
    if not os.path.exists(caminho):
        return padrao
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return padrao


def campo(dic, *caminho, padrao=NAO_MEDIDO):
    """Desce por um caminho de chaves. Falta de campo vira 'nao medido', nunca 0."""
    atual = dic
    for k in caminho:
        if not isinstance(atual, dict) or k not in atual:
            return padrao
        atual = atual[k]
    return padrao if atual is None else atual


# --------------------------------------------------------------- 1. carimbos e frescor
def bloco_frescor(sentimento, precificacao, diferenciais, agentes):
    """A IDADE DOS DADOS. Todos os carimbos sao COPIADOS do campo de cada arquivo.

    Nao calculo quantos minutos faz: `atraso_min`, `atraso_texto` e `estado` sao medidos
    por sentimento.py e copiados daqui. Idade em dias uteis dos juros idem —
    diferenciais.json ja traz `idade_du_base` / `idade_du_cotada` por perna.
    """
    fr = campo(sentimento, "frescor", padrao={}) or {}
    carimbos = [
        {
            "arquivo": "data/sentimento.json",
            "papel": "leitura da casa (a tese)",
            "gerado_em": campo(sentimento, "gerado_em"),
            "gerado_em_brt": campo(sentimento, "gerado_em_brt"),
        },
        {
            "arquivo": "data/precificacao.json",
            "papel": "o que os futuros pagam",
            "gerado_em": campo(precificacao, "gerado_em"),
            "gerado_em_brt": NAO_MEDIDO,
        },
        {
            "arquivo": "data/diferenciais.json",
            "papel": "juro de 2 e 10 anos (exibido, nunca voto)",
            "gerado_em": campo(diferenciais, "meta", "generated_at"),
            "gerado_em_brt": NAO_MEDIDO,
        },
    ]
    for nome, dados in sorted(agentes.items()):
        carimbos.append(
            {
                "arquivo": "data/agentes/%s/ultimo.json" % nome,
                "papel": "agente %s (%s)" % (nome, campo(dados, "versao_prompt")),
                "gerado_em": campo(dados, "gerado_em"),
                "gerado_em_brt": NAO_MEDIDO,
            }
        )
    return {
        "carimbos": carimbos,
        "frescor_da_casa": {
            "atraso_min": campo(fr, "atraso_min"),
            "atraso_texto": campo(fr, "atraso_texto"),
            "estado": campo(fr, "estado"),
            "bloqueia_leitura": campo(fr, "bloqueia_leitura"),
            "texto": campo(fr, "texto"),
            "fonte_mais_velha": campo(fr, "fonte_mais_velha"),
        },
        "fonte": "sentimento.frescor (medido por sentimento.py) + campo `gerado_em` de cada arquivo",
    }


# ----------------------------------------------------------- 2. indices auxiliares
def indexa_precificacao(precificacao):
    return campo(precificacao, "moedas", padrao={}) or {}


def indexa_diferenciais(diferenciais):
    por_par = {}
    for item in campo(diferenciais, "pares", padrao=[]) or []:
        if isinstance(item, dict) and item.get("par"):
            por_par[item["par"]] = item
    return por_par


def indexa_agentes():
    """Lista o diretorio em vez de presumir nomes — foi assim que o `vigia` apareceu."""
    saida = {}
    for caminho in sorted(glob(os.path.join(DIR_AGENTES, "*", "ultimo.json"))):
        nome = os.path.basename(os.path.dirname(caminho))
        dados = le(caminho)
        if dados:
            saida[nome] = dados
    return saida


def indexa_objecoes(agentes):
    """Objecoes do advogado, agrupadas por (agente_alvo, chave_alvo).

    So entram as que SAO objecao: `sem objecao` fica de fora do bloco de objecoes, mas
    o placar delas continua contado no cabecalho — ausencia de objecao nao e aprovacao,
    e o proprio advogado escreve isso nos limites dele.
    """
    adv = agentes.get("advogado") or {}
    por_alvo = {}
    for j in campo(adv, "julgamentos", padrao=[]) or []:
        if not isinstance(j, dict):
            continue
        if str(j.get("veredito", "")).strip().lower() == "sem objecao":
            continue
        alvo = j.get("alvo") or {}
        chave = (alvo.get("agente"), alvo.get("chave"))
        por_alvo.setdefault(chave, []).append(
            {
                "chave_da_objecao": j.get("chave"),
                "veredito": campo(j, "veredito"),
                "gravidade": campo(j, "gravidade"),
                "confianca": campo(j, "confianca"),
                "derruba_a_tese": campo(j, "derruba_a_tese", padrao=False),
                "trecho": campo(j, "trecho"),
                "motivo": campo(j, "motivo"),
                "fonte_link": campo(j, "fonte", "link"),
                "fonte_titulo": campo(j, "fonte", "titulo"),
                "o_que_o_site_faz": campo(j, "o_que_o_site_faz"),
                "vota": campo(j, "vota", padrao=False),
                "selo": campo(j, "selo"),
            }
        )
    return por_alvo


# ------------------------------------------------- 3. julgamentos que tocam uma moeda
def julgamentos_da_moeda(agentes, objecoes, moeda):
    """Recolhe o que cada agente julgou sobre UMA moeda.

    A chave e o contrato de cada agente e eles diferem: `noticia` e `divergencia` usam
    a moeda pura ('AUD'); `fala` usa MOEDA/orador ('USD/Waller'). O `geopolitica` usa
    'evento/...' e NAO mapeia para moeda — por isso ele sai num bloco global da rodada,
    nunca colado numa perna. Isto e registro de desvio de contrato, nao correcao: nao
    reescrevo a chave de agente nenhum.
    """
    saida = []
    for nome, dados in sorted(agentes.items()):
        if nome in ("advogado", "vigia", "geopolitica"):
            continue
        for j in campo(dados, "julgamentos", padrao=[]) or []:
            if not isinstance(j, dict):
                continue
            chave = str(j.get("chave") or "")
            if not (chave == moeda or chave.startswith(moeda + "/")):
                continue
            linha = {
                "agente": nome,
                "versao_prompt": campo(dados, "versao_prompt"),
                "chave": chave,
                "veredito": campo(j, "veredito"),
                "confianca": campo(j, "confianca"),
                "trecho": campo(j, "trecho"),
                "fonte_titulo": campo(j, "fonte", "titulo"),
                "fonte_link": campo(j, "fonte", "link"),
                "fonte_quando": campo(j, "fonte", "quando"),
                "vota": campo(j, "vota", padrao=False),
                "selo": campo(j, "selo", padrao="experimental — contexto, não vota"),
                "objecoes_do_advogado": objecoes.get((nome, chave), []),
            }
            saida.append(linha)
    return saida


def veredito_divergencia(agentes, moeda):
    """O 'esta de acordo com a leitura?' JA TEM DONO: o agente `divergencia`.

    Copio o veredito dele e cito a chave. Nao refaco a comparacao aqui: dois juizes com
    reguas diferentes sobre a mesma pergunta e como a casa fabrica contradicao.
    """
    dados = agentes.get("divergencia") or {}
    for j in campo(dados, "julgamentos", padrao=[]) or []:
        if isinstance(j, dict) and j.get("chave") == moeda:
            return {
                "veredito": campo(j, "veredito"),
                "confianca": campo(j, "confianca"),
                "lado_ausente": campo(j, "lado_ausente", padrao=None),
                "destaque": campo(j, "destaque", padrao=None),
                "noticia_concorda_com_hci": campo(j, "noticia_concorda_com_hci"),
                "colunas": campo(j, "colunas", padrao={}),
                "fonte": "data/agentes/divergencia/ultimo.json · julgamentos[%s]" % moeda,
                "versao_prompt": campo(dados, "versao_prompt"),
                "vota": campo(j, "vota", padrao=False),
            }
    return None


# --------------------------------------------------------- 4. o que o mercado paga
def bloco_mercado(precos, agentes, moeda):
    """Precificacao de UMA perna. Sem fonte e informacao, nao buraco a preencher."""
    p = precos.get(moeda)
    if not isinstance(p, dict):
        return {
            "moeda": moeda,
            "tem_fonte": False,
            "texto": SEM_FONTE,
            "motivo": "moeda ausente de data/precificacao.json",
        }
    qualidade = campo(p, "qualidade")
    tem_fonte = str(qualidade).strip().lower() not in ("sem fonte", NAO_MEDIDO)
    bloco = {
        "moeda": moeda,
        "tem_fonte": bool(tem_fonte),
        "banco": campo(p, "sigla"),
        "banco_nome": campo(p, "banco"),
        "taxa_atual": campo(p, "taxa_atual"),
        "proxima_reuniao": campo(p, "proxima"),
        "qualidade": qualidade,
        "direcao_mercado": campo(p, "direcao_mercado"),
        "p_alta": campo(p, "p_alta"),
        "p_manutencao": campo(p, "p_manutencao"),
        "p_corte": campo(p, "p_corte"),
        "implicito_bp": campo(p, "implicito_bp"),
        "metodo": campo(p, "metodo"),
        "fonte": campo(p, "fonte"),
        "motivo_sem_fonte": campo(p, "detalhe", "motivo", padrao=None),
        "texto": None,
    }
    if not tem_fonte:
        bloco["texto"] = SEM_FONTE
    bloco["confronto_com_a_leitura"] = veredito_divergencia(agentes, moeda)
    return bloco


# --------------------------------------------------------- 5. diferencial de juro
def bloco_juro(dif_por_par, par):
    """Juro de 2 e 10 anos + variacao em 5 dias. DADO EXIBIDO, NUNCA VOTO.

    A lei esta escrita no proprio diferenciais.json ('YIELD E DADO DE MERCADO EXIBIDO.
    NAO ENTRA NO SENTIMENTO EM NENHUMA HIPOTESE'). As duas pernas nao sao do mesmo
    instante — cada uma carrega o seu as_of e a sua idade em dias uteis, e os dois vao
    impressos ao lado do numero.
    """
    d = dif_por_par.get(par)
    if not isinstance(d, dict):
        return {"tem_dado": False, "texto": NAO_MEDIDO,
                "motivo": "par ausente de data/diferenciais.json"}
    saida = {"tem_dado": True, "lei": "dado exibido, nunca voto"}
    for rotulo, chave in (("dois_anos", "dois_anos"), ("dez_anos", "dez_anos")):
        b = d.get(chave) or {}
        saida[rotulo] = {
            "diferencial_pp": campo(b, "diferencial_pp"),
            "base_pct": campo(b, "base_pct"),
            "cotada_pct": campo(b, "cotada_pct"),
            "var_5d_bp": campo(b, "var_5d_bp"),
            "as_of_base": campo(b, "as_of_base"),
            "as_of_cotada": campo(b, "as_of_cotada"),
            "idade_du_base": campo(b, "idade_du_base"),
            "idade_du_cotada": campo(b, "idade_du_cotada"),
            "motivo_ausencia": campo(b, "motivo", padrao=None),
        }
    return saida


# --------------------------------------------------------- 6. bandeiras da evidencia
# ⚠️ A ORDEM IMPORTA e a lista de palavras é literal de propósito.
# Erro real cometido na 1ª versão e corrigido aqui: a palavra "idade" casa por SUBSTRING
# dentro de "qualIDADE", e mandava todo alerta de qualidade da evidência para a gaveta de
# "dado atrasado". As chaves de atraso agora são específicas, e `evidencia_fraca` vem antes.
PALAVRAS_DE_BANDEIRA = (
    ("dominancia", ("mesma aposta", "compartilham a perna", "não diversificam")),
    ("direcao_fragil", ("PARÂMETRO NÃO CALIBRADO", "SEM LEITURA", "depende de", "faixa neutra",
                        "FAIXA NEUTRA", "não calibrad")),
    ("evidencia_fraca", ("qualidade da evidência", "elo fraco", "sem fala votando",
                         "dimensão de discurso")),
    ("dado_atrasado", ("atrasad", "defasa", "idade dos dados", "reaproveitad", "cache",
                       "dias úteis", "frescor")),
)


def bandeiras(par):
    """Classifica os ALERTAS que o sentimento.py ja escreveu — nao cria alerta novo.

    ⚠️ PROVISORIO e declarado: a rotulagem e por palavra-chave no texto do alerta. Um
    alerta que nao case com nenhuma familia sai em 'outras', com o texto inteiro — nunca
    e descartado. Rotulo errado aqui nao apaga o alerta, so o coloca na gaveta errada.
    """
    alertas = campo(par, "alertas", padrao=[]) or []
    fam = {nome: [] for nome, _ in PALAVRAS_DE_BANDEIRA}
    fam["outras"] = []
    for a in alertas:
        texto = str(a)
        casou = False
        for nome, chaves in PALAVRAS_DE_BANDEIRA:
            if any(c.lower() in texto.lower() for c in chaves):
                fam[nome].append(texto)
                casou = True
                break
        if not casou:
            fam["outras"].append(texto)
    return {
        "n_alertas": len(alertas),
        "por_familia": {k: v for k, v in fam.items() if v},
        "todos": [str(a) for a in alertas],
        "fonte": "sentimento.json · pares[].alertas (copiados, não gerados aqui)",
        "regua_provisoria": "classificação por palavra-chave; alerta sem família vai para 'outras' com o texto inteiro",
    }


# --------------------------------------------------------------------- 7. a ficha
def monta_ficha(par, precos, dif_por_par, agentes, objecoes):
    base = campo(par, "base")
    cotada = campo(par, "cotada")
    dominante = campo(par, "perna_dominante", padrao={}) or {}

    return {
        "par": campo(par, "par"),
        # 1. a acao, o estado, a divergencia
        "acao": campo(par, "acao"),
        "sinal": campo(par, "sinal"),
        "estado": campo(par, "estado"),
        "divergencia_sobre_100": campo(par, "divergencia"),
        "estado_limitado_por": campo(par, "estado_limitado_por", padrao=None),
        "faixas_provisorias": campo(par, "faixas_provisorias", padrao={}),
        "motivo": campo(par, "motivo"),
        "conviccao_pct": campo(par, "conviccao_pct"),
        "conviccao_historica": campo(par, "conviccao_historica", padrao=None),
        "conviccao_historica_nota": campo(par, "conviccao_historica_nota"),
        # 2. quem da o motivo — a lei das duas pernas
        "quem_da_o_motivo": {
            "perna_dominante": campo(dominante, "moeda"),
            "share_pct": campo(dominante, "share_pct"),
            "perna_motivo": campo(par, "perna_motivo"),
            "leitura_base": {
                "moeda": base,
                "leitura_texto": campo(par, "leitura_base", "leitura_texto"),
                "direcao": campo(par, "leitura_base", "direcao"),
                "qualidade_evidencia": campo(par, "leitura_base", "qualidade_evidencia"),
                "concordancia_texto": campo(par, "leitura_base", "concordancia_texto"),
                "conviccao_pct": campo(par, "leitura_base", "conviccao_pct"),
            },
            "leitura_cotada": {
                "moeda": cotada,
                "leitura_texto": campo(par, "leitura_cotada", "leitura_texto"),
                "direcao": campo(par, "leitura_cotada", "direcao"),
                "qualidade_evidencia": campo(par, "leitura_cotada", "qualidade_evidencia"),
                "concordancia_texto": campo(par, "leitura_cotada", "concordancia_texto"),
                "conviccao_pct": campo(par, "leitura_cotada", "conviccao_pct"),
            },
            "lei": "par não é ativo, são duas moedas: um par 90% de uma perna é uma aposta naquela moeda",
            "fonte": "sentimento.json · pares[].perna_dominante / .leitura_base / .leitura_cotada",
        },
        # 3. mesma aposta
        "mesma_aposta": {
            "pares": campo(par, "mesma_aposta", padrao=[]),
            "aviso": "compartilham a perna dominante: dois deles não diversificam, DOBRAM",
            "fonte": "sentimento.json · pares[].mesma_aposta",
        },
        # 4. ate quando
        "ate_quando": {
            "evento": campo(par, "proximo_evento_invalidante", "evento"),
            "moeda": campo(par, "proximo_evento_invalidante", "moeda"),
            "data": campo(par, "proximo_evento_invalidante", "data"),
            "dias": campo(par, "proximo_evento_invalidante", "dias"),
            "proximo_dado_relevante": {
                "texto": campo(par, "proximo_evento_relevante", "texto"),
                "impacto": campo(par, "proximo_evento_relevante", "impacto"),
                "quando_brt": campo(par, "proximo_evento_relevante", "quando_brt"),
                "dias": campo(par, "proximo_evento_relevante", "dias"),
                "nota": campo(par, "proximo_evento_relevante", "nota"),
            },
            "leitura": "é o que diz por quanto tempo faz sentido PROCURAR a entrada — não é alvo nem prazo de posição",
            "fonte": "sentimento.json · pares[].proximo_evento_invalidante / .proximo_evento_relevante",
        },
        # 5. qualidade da evidencia e bandeiras
        "qualidade_da_evidencia": {
            "nota": campo(par, "qualidade_evidencia"),
            "por_perna": campo(par, "qualidade_por_perna", padrao={}),
            "elo_fraco": campo(par, "qualidade_elo_fraco"),
            "fonte": "sentimento.json · pares[].qualidade_evidencia / .qualidade_por_perna",
        },
        "bandeiras": bandeiras(par),
        # 6. o que o mercado paga
        "o_que_o_mercado_paga": {
            base: bloco_mercado(precos, agentes, base),
            cotada: bloco_mercado(precos, agentes, cotada),
        },
        # 7. o que os agentes julgaram
        "o_que_os_agentes_julgaram": {
            base: julgamentos_da_moeda(agentes, objecoes, base),
            cotada: julgamentos_da_moeda(agentes, objecoes, cotada),
        },
        # 8. diferencial de juro
        "diferencial_de_juro": bloco_juro(dif_por_par, campo(par, "par")),
    }


# ----------------------------------------------------------------- 8. contexto global
def contexto_global(agentes, objecoes):
    """O que existe na rodada e NAO cola numa perna — dito, nunca escondido."""
    geo = agentes.get("geopolitica") or {}
    linhas = []
    for j in campo(geo, "julgamentos", padrao=[]) or []:
        if not isinstance(j, dict):
            continue
        linhas.append(
            {
                "chave": campo(j, "chave"),
                "veredito": campo(j, "veredito"),
                "confianca": campo(j, "confianca"),
                "trecho": campo(j, "trecho"),
                "fonte_link": campo(j, "fonte", "link"),
                "vota": campo(j, "vota", padrao=False),
                "objecoes_do_advogado": objecoes.get(("geopolitica", campo(j, "chave"))) or [],
            }
        )
    orfas = []
    for (agente_alvo, chave_alvo), lista in sorted(objecoes.items(), key=lambda x: str(x[0])):
        if agente_alvo == "geopolitica":
            continue
        orfas.append({"agente_alvo": agente_alvo, "chave_alvo": chave_alvo, "objecoes": lista})
    adv = agentes.get("advogado") or {}
    return {
        "geopolitica": {
            "julgamentos": linhas,
            "nota": "o agente `geopolitica` julga EVENTO, não moeda: as chaves dele não mapeiam para perna, "
                    "então aparecem aqui e nunca coladas num par",
            "vota": campo(geo, "vota", padrao=False),
            "selo": campo(geo, "selo"),
        },
        "objecoes_do_advogado_por_alvo": orfas,
        "advogado_limites": campo(adv, "limites", padrao=[]),
    }


# --------------------------------------------------------------------- 9. relatorio
def linha(c="-", n=100):
    return c * n


def fmt(v):
    return NAO_MEDIDO if v is None else str(v)


def escreve_relatorio(doc):
    L = []
    A = L.append
    cab = doc["cabecalho"]

    A(linha("="))
    A("HCI MACRO DIRECTION — FICHA OPERACIONAL POR PAR (FX)")
    A(linha("="))
    A("")

    # ---- 1. idade dos dados
    A("1) IDADE DOS DADOS (carimbo copiado do campo `gerado_em` de cada arquivo)")
    A(linha())
    for c in cab["idade_dos_dados"]["carimbos"]:
        brt = "" if c["gerado_em_brt"] == NAO_MEDIDO else "   [%s]" % c["gerado_em_brt"]
        A("   %-38s %s%s" % (c["arquivo"], fmt(c["gerado_em"]), brt))
        A("   %-38s %s" % ("", c["papel"]))
    f = cab["idade_dos_dados"]["frescor_da_casa"]
    A("")
    A("   FRESCOR DA CASA (medido por sentimento.py, campo sentimento.frescor):")
    A("      atraso: %s (%s min) · estado: %s · bloqueia_leitura: %s"
      % (fmt(f["atraso_texto"]), fmt(f["atraso_min"]), fmt(f["estado"]), fmt(f["bloqueia_leitura"])))
    if f["fonte_mais_velha"] != NAO_MEDIDO:
        A("      fonte mais velha: %s" % fmt(f["fonte_mais_velha"]))
    A("")

    # ---- 2. quantos pares tem tese
    q = cab["quantos_pares_tem_tese"]
    A("2) QUANTOS PARES TÊM TESE HOJE")
    A(linha())
    A("   %s de %s pares com tese (estado ≠ sem_tese). Sem tese: %s."
      % (q["com_tese"], q["total_de_pares"], q["sem_tese"]))
    A("   Por estado: " + " · ".join("%s %s" % (k, v) for k, v in q["por_estado"].items()))
    A("   Faixas PROVISÓRIAS da divergência: " + fmt(q["faixas_provisorias"]))
    A("   ⚠️ %s" % q["nota_da_escala"])
    A("")

    # ---- 3. aviso
    A("3) AVISO — A DIVISÃO DE TRABALHO")
    A(linha())
    for l in cab["aviso"]:
        A("   " + l)
    A("")

    # ---- contexto global
    ctx = doc["contexto_da_rodada"]
    A(linha("="))
    A("CONTEXTO DA RODADA — o que não cola em nenhuma perna")
    A(linha("="))
    geo = ctx["geopolitica"]
    A("GEOPOLÍTICA (%s):" % fmt(geo.get("selo")))
    A("   " + geo["nota"])
    if not geo["julgamentos"]:
        A("   sem julgamentos nesta rodada.")
    for g in geo["julgamentos"]:
        A("   · %-52s → %s (confiança %s)" % (fmt(g["chave"]), fmt(g["veredito"]), fmt(g["confianca"])))
        A("       trecho: %s" % fmt(g["trecho"]))
    A("")
    A("OBJEÇÕES DO ADVOGADO NESTA RODADA (não derrubam tese; ficam ao lado dela):")
    if not ctx["objecoes_do_advogado_por_alvo"]:
        A("   nenhuma.")
    for o in ctx["objecoes_do_advogado_por_alvo"]:
        for ob in o["objecoes"]:
            A("   · [%s] %s:%s → %s (derruba a tese: %s)"
              % (str(ob["gravidade"]).upper(), fmt(o["agente_alvo"]), fmt(o["chave_alvo"]),
                 fmt(ob["veredito"]), fmt(ob["derruba_a_tese"])))
    A("")

    # ---- fichas
    for i, fi in enumerate(doc["fichas"], 1):
        A(linha("="))
        A("FICHA %d/%d — %s" % (i, len(doc["fichas"]), fi["par"]))
        A(linha("="))

        # 1
        A("1. AÇÃO ......... %s" % fmt(fi["acao"]))
        A("   ESTADO ....... %s   ·   DIVERGÊNCIA %s/100"
          % (fmt(fi["estado"]), fmt(fi["divergencia_sobre_100"])))
        A("   MOTIVO ....... %s" % fmt(fi["motivo"]))
        A("   convicção da leitura: %s%%   ·   convicção histórica: %s (%s)"
          % (fmt(fi["conviccao_pct"]), fmt(fi["conviccao_historica"]),
             fmt(fi["conviccao_historica_nota"])))
        A("")

        # 2
        d = fi["quem_da_o_motivo"]
        A("2. QUEM DÁ O MOTIVO (lei das duas pernas)")
        A("   perna dominante: %s com %s%% da diferença" % (fmt(d["perna_dominante"]), fmt(d["share_pct"])))
        for lado in ("leitura_base", "leitura_cotada"):
            b = d[lado]
            A("      %s: %s (direção %s) · evidência %s/100 · %s"
              % (fmt(b["moeda"]), fmt(b["leitura_texto"]), fmt(b["direcao"]),
                 fmt(b["qualidade_evidencia"]), fmt(b["concordancia_texto"])))
        A("   ⚠️ %s" % d["lei"])
        A("")

        # 3
        m = fi["mesma_aposta"]
        A("3. MESMA APOSTA")
        if m["pares"]:
            A("   %s" % ", ".join(m["pares"]))
            A("   ⚠️ %s" % m["aviso"])
        else:
            A("   nenhum outro par compartilha a perna dominante nesta rodada.")
        A("")

        # 4
        a = fi["ate_quando"]
        A("4. ATÉ QUANDO")
        A("   evento invalidante: %s (%s) em %s — faltam %s dia(s)"
          % (fmt(a["evento"]), fmt(a["moeda"]), fmt(a["data"]), fmt(a["dias"])))
        pdr = a["proximo_dado_relevante"]
        A("   próximo dado relevante: %s · impacto %s" % (fmt(pdr["texto"]), fmt(pdr["impacto"])))
        A("   %s" % a["leitura"])
        A("")

        # 5
        qe = fi["qualidade_da_evidencia"]
        A("5. QUALIDADE DA EVIDÊNCIA E BANDEIRAS")
        A("   nota do par: %s/100   ·   por perna: %s   ·   elo fraco: %s"
          % (fmt(qe["nota"]), fmt(qe["por_perna"]), fmt(qe["elo_fraco"])))
        bd = fi["bandeiras"]
        A("   %s alerta(s) copiados do sentimento.json:" % bd["n_alertas"])
        for familia, itens in bd["por_familia"].items():
            A("   [%s]" % familia.upper())
            for t in itens:
                A("      · %s" % t)
        A("")

        # 6
        A("6. O QUE O MERCADO PAGA")
        for moeda, bloco in fi["o_que_o_mercado_paga"].items():
            if not bloco.get("tem_fonte"):
                A("   %s (%s): %s" % (moeda, fmt(bloco.get("banco")), SEM_FONTE))
                if bloco.get("motivo_sem_fonte"):
                    A("       motivo: %s" % fmt(bloco["motivo_sem_fonte"]))
            else:
                A("   %s (%s) · próxima reunião %s · taxa atual %s · qualidade %s"
                  % (moeda, fmt(bloco["banco"]), fmt(bloco["proxima_reuniao"]),
                     fmt(bloco["taxa_atual"]), fmt(bloco["qualidade"])))
                A("       o mercado paga: %s · p_alta %s · p_manutenção %s · p_corte %s · implícito %s bp"
                  % (fmt(bloco["direcao_mercado"]), fmt(bloco["p_alta"]),
                     fmt(bloco["p_manutencao"]), fmt(bloco["p_corte"]), fmt(bloco["implicito_bp"])))
                A("       fonte: %s" % fmt(bloco["fonte"]))
            conf = bloco.get("confronto_com_a_leitura")
            if conf:
                A("       está de acordo com a leitura? → %s (confiança %s) — veredito do agente `divergencia`, "
                  "copiado, não recalculado aqui" % (fmt(conf["veredito"]), fmt(conf["confianca"])))
                if conf.get("lado_ausente"):
                    A("           lado ausente: %s" % fmt(conf["lado_ausente"]))
            else:
                A("       está de acordo com a leitura? → %s (o agente `divergencia` não julgou esta moeda)"
                  % SEM_FONTE)
        A("")

        # 7
        A("7. O QUE OS AGENTES JULGARAM")
        for moeda, linhas_ag in fi["o_que_os_agentes_julgaram"].items():
            A("   — perna %s —" % moeda)
            if not linhas_ag:
                A("       nenhum agente julgou esta moeda nesta rodada.")
            for j in linhas_ag:
                A("       [%s · %s · chave %s] %s (confiança %s) — vota: %s"
                  % (fmt(j["agente"]), fmt(j["versao_prompt"]), fmt(j["chave"]),
                     fmt(j["veredito"]), fmt(j["confianca"]), fmt(j["vota"])))
                A("           trecho: %s" % fmt(j["trecho"]))
                A("           fonte: %s" % fmt(j["fonte_link"]))
                for ob in j["objecoes_do_advogado"]:
                    A("           ⚖️ OBJEÇÃO DO ADVOGADO [%s] %s (derruba a tese: %s)"
                      % (str(ob["gravidade"]).upper(), fmt(ob["veredito"]), fmt(ob["derruba_a_tese"])))
                    A("               %s" % fmt(ob["motivo"]))
        A("")

        # 8
        A("8. DIFERENCIAL DE JURO (dado exibido, NUNCA voto)")
        jz = fi["diferencial_de_juro"]
        if not jz.get("tem_dado"):
            A("   %s — %s" % (NAO_MEDIDO, fmt(jz.get("motivo"))))
        else:
            for rot, nome in (("dois_anos", "2 anos "), ("dez_anos", "10 anos")):
                b = jz[rot]
                A("   %s: diferencial %s pp (base %s%% x cotada %s%%) · variação em 5 dias %s bp"
                  % (nome, fmt(b["diferencial_pp"]), fmt(b["base_pct"]), fmt(b["cotada_pct"]),
                     fmt(b["var_5d_bp"])))
                A("            as_of base %s (idade %s d.u.) · as_of cotada %s (idade %s d.u.)"
                  % (fmt(b["as_of_base"]), fmt(b["idade_du_base"]),
                     fmt(b["as_of_cotada"]), fmt(b["idade_du_cotada"])))
        A("")

    A(linha("="))
    A("FIM. %s ficha(s). Isto é o lado FUNDAMENTAL. A ENTRADA é do Eduardo, pela técnica dele."
      % len(doc["fichas"]))
    A(linha("="))
    return "\n".join(L)


# --------------------------------------------------------------------------- 10. main
def main():
    sentimento = le(os.path.join(D, "sentimento.json"))
    if not sentimento:
        print("ERRO: data/sentimento.json não pôde ser lido. Sem a leitura da casa não há ficha.")
        return 1
    precificacao = le(os.path.join(D, "precificacao.json"), {})
    diferenciais = le(os.path.join(D, "diferenciais.json"), {})
    agentes = indexa_agentes()
    objecoes = indexa_objecoes(agentes)

    precos = indexa_precificacao(precificacao)
    dif_por_par = indexa_diferenciais(diferenciais)

    pares = campo(sentimento, "pares", padrao=[]) or []
    com_tese = [p for p in pares if str(campo(p, "estado")).strip().lower() != "sem_tese"]
    # ordenacao pela divergencia — campo COPIADO, nao calculado
    com_tese.sort(key=lambda p: (campo(p, "divergencia", padrao=0) or 0), reverse=True)

    por_estado = {}
    for p in pares:
        e = str(campo(p, "estado"))
        por_estado[e] = por_estado.get(e, 0) + 1

    fichas = [monta_ficha(p, precos, dif_por_par, agentes, objecoes) for p in com_tese]

    cabecalho = {
        "idade_dos_dados": bloco_frescor(sentimento, precificacao, diferenciais, agentes),
        "quantos_pares_tem_tese": {
            "com_tese": len(com_tese),
            "sem_tese": len(pares) - len(com_tese),
            "total_de_pares": len(pares),
            "por_estado": por_estado,
            "faixas_provisorias": campo(sentimento, "regua", "faixas_provisorias", padrao={}),
            "nota_da_escala": "as faixas são PROVISÓRIAS e foram desenhadas na escala velha: o teto teórico "
                              "caiu de 1,50 para 1,00 em 05/set, quando a fala parou de votar — a mesma "
                              "diferença econômica sai 50% maior em divergência (fonte: sentimento.json)",
            "fonte": "sentimento.json · pares[].estado (contagem de itens da lista, não medida nova)",
        },
        "aviso": [
            "Isto é o LADO FUNDAMENTAL. A ENTRADA é do Eduardo, pela análise técnica dele.",
            "Nada aqui é ordem, sinal de entrada, alvo ou promessa de retorno.",
            "Nenhum agente vota: todos saem com vota=false e selo experimental. Convicção histórica "
            "é null até o backtest de 21/dez.",
            "Este arquivo não calcula: todo número é cópia de campo nomeado das fontes; o que a fonte "
            "não tem sai como \"não medido\".",
            "Publicação em cenário condicional — pessoa física sem registro na CVM.",
        ],
    }

    doc = {
        "produto": "HCI MACRO DIRECTION — ficha operacional por par (FX)",
        "gerado_por": "ficha_par_fx.py",
        "o_que_este_arquivo_e": "junção somente-leitura de sentimento.json, precificacao.json, "
                                "diferenciais.json e data/agentes/*/ultimo.json. Nenhum cálculo novo.",
        "fontes": [c["arquivo"] for c in cabecalho["idade_dos_dados"]["carimbos"]],
        "cabecalho": cabecalho,
        "contexto_da_rodada": contexto_global(agentes, objecoes),
        "fichas": fichas,
    }

    with open(SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)

    texto = escreve_relatorio(doc)
    with open(SAIDA_TXT, "w", encoding="utf-8") as f:
        f.write(texto)

    print(texto)
    print()
    print("gravado: %s" % SAIDA_JSON)
    print("gravado: %s" % SAIDA_TXT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
