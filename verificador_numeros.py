# -*- coding: utf-8 -*-
"""VERIFICADOR DE NUMEROS — a peca que faltava da camada 2.

O ARQUITETURA_AGENTES.md, secao 6, promete o remedio para o risco numero 1:

    "A IA inventa um numero que ninguem mediu  ->  ela recebe os numeros prontos e e
     proibida de calcular; O VERIFICADOR CONFERE CADA NUMERO CITADO CONTRA A CAMADA 1"

Esse verificador nao existia. Sem ele a proibicao era so texto de prompt: um agente
podia escrever qualquer numero em `numeros_citados` e nada no repositorio notava.
Foi assim que o proprio exemplo do agentes/noticia/PROMPT.md ficou com
`noticias.moedas.USD.n_unicos: 78` quando o arquivo diz 38.

O QUE ELE FAZ
    Le um (ou todos) os `data/agentes/<nome>/ultimo.json`, pega cada chave de
    `numeros_citados` — que por contrato tem a forma `<arquivo>.<caminho>.<campo>` —
    resolve o caminho dentro do JSON da camada 1 e compara o valor.

    Saida por numero: OK / DIVERGE / CAMINHO INEXISTENTE / ARQUIVO INEXISTENTE.

O QUE ELE NAO FAZ
    Nao julga, nao reescreve, nao conserta nada. So confere e sai com codigo 1 se
    houver qualquer numero que nao case. Ele e camada 1 sobre a camada 2.

USO
    python verificador_numeros.py                      # confere todos os agentes
    python verificador_numeros.py --agente noticia     # so um
    python verificador_numeros.py --arquivo caminho.json
    python verificador_numeros.py --estrito            # sai 1 se houver divergencia

MAPA DE PREFIXOS
    O primeiro segmento da chave e o apelido do arquivo da camada 1. O mapa esta em
    PREFIXOS, abaixo, e e deliberadamente EXPLICITO: apelido novo exige linha nova, e
    isso e proposital — um agente nao inventa uma fonte nova sem alguem ver.
"""

import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(RAIZ, "data")

# apelido usado na chave de `numeros_citados`  ->  arquivo da camada 1
PREFIXOS = {
    "noticias": "data/noticias.json",
    "precificacao": "data/precificacao.json",
    "bc_discursos": "data/bc_discursos.json",
    "bis_discursos": "data/bis_discursos.json",
    "bancos_centrais": "data/bancos_centrais.json",
    "sentimento": "data/sentimento.json",
    "geopolitica": "data/geopolitica.json",
    "frescor": "data/frescor.json",
    "calendario_resultado": "data/calendario_resultado.json",
    "eua_leitura": "data/eua_leitura.json",
    "correlacao_juros": "data/correlacao_juros.json",
    "macro_eventos": "data/macro_eventos.json",
    "diferenciais": "data/diferenciais.json",
    "juros_vs_cambio": "data/juros_vs_cambio.json",
    "yields": "data/yields.json",
}

# O vigia e a excecao declarada: ele mede a OPERACAO (idade, execucoes, passos), nao
# o mercado, e a medicao dele mora em data/agentes/vigia/medicao.json — nao em um JSON
# de coletor. As chaves dele nao seguem o padrao <arquivo>.<caminho> de proposito.
AGENTES_ISENTOS = {"vigia"}

_cache = {}


def carrega(rel):
    if rel not in _cache:
        p = os.path.join(RAIZ, rel.replace("/", os.sep))
        if not os.path.exists(p):
            _cache[rel] = None
        else:
            with open(p, encoding="utf-8") as f:
                _cache[rel] = json.load(f)
    return _cache[rel]


def desce(obj, partes):
    """Anda o caminho. Aceita indice de lista ('itens.0.peso')."""
    atual = obj
    for parte in partes:
        if isinstance(atual, dict):
            if parte not in atual:
                return (False, None)
            atual = atual[parte]
        elif isinstance(atual, list):
            try:
                atual = atual[int(parte)]
            except (ValueError, IndexError):
                return (False, None)
        else:
            return (False, None)
    return (True, atual)


def iguais(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return a == b


def confere_saida(caminho_saida):
    """Devolve (linhas, n_erros) para um ultimo.json de agente."""
    linhas, erros = [], 0
    with open(caminho_saida, encoding="utf-8") as f:
        saida = json.load(f)

    nome = saida.get("agente", "?")
    if nome in AGENTES_ISENTOS:
        linhas.append("  ISENTO — o agente `%s` mede operacao, nao o mercado; "
                      "a medicao dele mora em medicao.json" % nome)
        return linhas, 0

    for j in saida.get("julgamentos", []):
        chave = j.get("chave", "?")
        for nome_num, valor in (j.get("numeros_citados") or {}).items():
            partes = nome_num.split(".")
            if len(partes) < 2:
                linhas.append("  [FORMA]     %s / %s = %r — a chave tem de ser "
                              "<arquivo>.<caminho>.<campo>" % (chave, nome_num, valor))
                erros += 1
                continue
            rel = PREFIXOS.get(partes[0])
            if rel is None:
                linhas.append("  [PREFIXO]   %s / %s — apelido de arquivo desconhecido "
                              "(nao esta em PREFIXOS)" % (chave, nome_num))
                erros += 1
                continue
            doc = carrega(rel)
            if doc is None:
                linhas.append("  [SEM ARQ]   %s / %s — %s nao existe no repositorio"
                              % (chave, nome_num, rel))
                erros += 1
                continue
            achou, medido = desce(doc, partes[1:])
            if not achou:
                linhas.append("  [INVENTADO] %s / %s = %r — o caminho NAO EXISTE em %s"
                              % (chave, nome_num, valor, rel))
                erros += 1
            elif not iguais(valor, medido):
                linhas.append("  [DIVERGE]   %s / %s: agente escreveu %r, %s diz %r"
                              % (chave, nome_num, valor, rel, medido))
                erros += 1
            else:
                linhas.append("  [ok]        %s / %s = %r" % (chave, nome_num, valor))
    if not linhas:
        linhas.append("  (nenhum numero citado)")
    return linhas, erros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agente", help="so este agente")
    ap.add_argument("--arquivo", help="confere um ultimo.json em caminho livre")
    ap.add_argument("--estrito", action="store_true",
                    help="sai com codigo 1 se houver qualquer numero que nao case")
    a = ap.parse_args()

    alvos = []
    if a.arquivo:
        alvos.append(a.arquivo)
    else:
        base = os.path.join(DATA, "agentes")
        if os.path.isdir(base):
            for nome in sorted(os.listdir(base)):
                if a.agente and nome != a.agente:
                    continue
                p = os.path.join(base, nome, "ultimo.json")
                if os.path.exists(p):
                    alvos.append(p)

    if not alvos:
        print("nenhum ultimo.json encontrado — nada a conferir")
        return 0

    total = 0
    print("=" * 92)
    print("VERIFICADOR DE NUMEROS — cada numero citado pela camada 2 existe na camada 1?")
    print("=" * 92)
    for alvo in alvos:
        print("\n%s" % alvo)
        linhas, erros = confere_saida(alvo)
        for l in linhas:
            print(l)
        total += erros

    print("\n" + "=" * 92)
    if total:
        print("%d NUMERO(S) NAO CONFEREM. Numero citado que nao existe na camada 1 mata o "
              "backtest: o numero de hoje deixa de ser recalculavel." % total)
    else:
        print("todos os numeros citados batem com a camada 1")
    print("=" * 92)

    return 1 if (total and a.estrito) else 0


if __name__ == "__main__":
    sys.exit(main())
