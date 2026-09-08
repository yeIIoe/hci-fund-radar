# -*- coding: utf-8 -*-
"""O tratamento da soma e a guarda de direção — conserto de 08/set/2026.

Estes testes existem porque a winsorização por item passou TRÊS DIAS no ar virando a direção
do USD e do GBP, e o único lugar onde isso aparecia era um campo de auditoria que ninguém lia.
Aqui a mesma família de erro fica presa por teste, não por atenção.

Quatro coisas ficam provadas:
  1. a soma publicada é a soma CRUA (nenhum termo cortado) e os quatro campos de auditoria
     saem em todas as moedas do arquivo gerado;
  2. a dominância NUNCA muda a direção — ela derruba a qualidade da evidência e levanta a
     bandeira, e a direção continua sendo a do dado;
  3. a aritmética: winsorizar VIRA o sinal quando os itens grandes estão de um lado só;
     reescalar proporcionalmente NÃO vira, e não mexe na participação (o fator cancela);
  4. a guarda de direção dispara DE VERDADE, ponta a ponta: com um tratamento que muda a
     leitura, a moeda vai para SEM LEITURA com a bandeira escrita.
"""
import datetime as dt
import json
import os
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import sentimento as S  # noqa: E402


class TratamentoDaSomaTest(unittest.TestCase):
    """O que o arquivo gerado tem de mostrar, em todas as moedas."""

    @classmethod
    def setUpClass(cls):
        fn = RAIZ / "data" / "sentimento.json"
        cls.doc = json.loads(fn.read_text(encoding="utf-8")) if fn.exists() else None

    def test_os_quatro_campos_de_auditoria_saem_sempre(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, leitura in self.doc["moedas"].items():
            dd = leitura["dimensoes"]["dados"]
            for campo in ("soma_crua", "soma_tratada", "participacao_maior_item_antes",
                          "participacao_maior_item_depois", "direcao_mudou_pelo_tratamento"):
                self.assertIn(campo, dd, "%s: falta %s" % (moeda, campo))

    def test_sem_tratamento_a_soma_publicada_e_a_crua(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        self.assertEqual("nenhum", S.TRATAMENTO_DA_SOMA)
        for moeda, leitura in self.doc["moedas"].items():
            dd = leitura["dimensoes"]["dados"]
            self.assertEqual(dd["soma_crua"], dd["soma"], moeda)
            self.assertEqual(dd["soma_crua"], dd["soma_tratada"], moeda)
            self.assertEqual(0.0, dd["tratamento_da_soma"]["deslocamento"], moeda)
            self.assertFalse(dd["direcao_mudou_pelo_tratamento"], moeda)
            self.assertFalse(leitura["guarda_de_direcao"]["virou"], moeda)

    def test_dominancia_nao_muda_direcao_e_derruba_a_evidencia(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, leitura in self.doc["moedas"].items():
            dom = leitura["dimensoes"]["dados"]["dominancia"]
            self.assertFalse(dom["muda_a_direcao"], moeda)
            if not dom["alerta"]:
                continue
            # a direção continua a que a soma crua produz
            self.assertEqual(leitura["dimensoes"]["dados"]["direcao_crua"],
                             leitura["dimensoes"]["dados"]["direcao"], moeda)
            q = leitura["qualidade_evidencia"]
            self.assertEqual(100 - dom["share_pct"], q["teto_pela_dominancia"], moeda)
            self.assertLessEqual(q["nota"], 100 - dom["share_pct"], moeda)
            self.assertTrue(dom["texto"], moeda)


class AritmeticaTest(unittest.TestCase):
    """A conta que derrubou a winsorização, rodando."""

    def test_winsorizar_vira_o_sinal_e_reescalar_nao(self):
        p = S.prova_do_tratamento()
        c1 = p["caso_1_forma_do_dolar"]
        self.assertEqual("MANTEM", c1["cru"]["direcao"])
        self.assertEqual("CORTA", c1["winsorizado_4_0"]["direcao"])
        self.assertTrue(c1["winsorizado_4_0"]["virou_a_direcao"])
        self.assertLess(c1["winsorizado_4_0"]["deslocamento"], 0)
        self.assertTrue(c1["reescalado_k_0_5"]["sinal_igual_ao_cru"])
        self.assertFalse(c1["reescalado_k_0_5"]["virou_a_direcao"])

    def test_participacao_e_invariante_a_reescala(self):
        p = S.prova_do_tratamento()
        c2 = p["caso_2_participacao_invariante"]
        self.assertEqual(c2["participacao_crua_pct"], c2["participacao_reescalada_pct"])
        c1 = p["caso_1_forma_do_dolar"]
        self.assertEqual(c1["cru"]["participacao_pct"],
                         c1["reescalado_k_0_5"]["participacao_pct"])

    def test_reescala_desligada_nao_toca_em_nada(self):
        fator, reg = S.reescala_proporcional([-7.9, 0.3, -0.2], teto_participacao_pct=50)
        self.assertEqual(1.0, fator)
        self.assertFalse(reg["ligada"])
        self.assertEqual(94, reg["participacao_medida_pct"])

    def test_reescala_ligada_admite_que_nao_resolve_concentracao(self):
        fator, reg = S.reescala_proporcional([-7.9, 0.3, -0.2], teto_participacao_pct=50,
                                             ligada=True)
        self.assertEqual(1.0, fator)          # nenhum fator comum derruba a participação
        self.assertIn("NENHUM fator comum", reg["resultado"])


class GuardaDeDirecaoTest(unittest.TestCase):
    """A lei estrutural: nenhum tratamento vira a direção em silêncio."""

    def test_a_guarda_dispara_e_escreve_o_motivo(self):
        g = S.guarda_de_direcao("teste", "MANTEM", "CORTA", "winsorizacao")
        self.assertTrue(g["virou"])
        self.assertIn("MUDOU a direcao", g["texto"])
        g2 = S.guarda_de_direcao("teste", "MANTEM", "MANTEM", "nenhum")
        self.assertFalse(g2["virou"])
        self.assertIsNone(g2["texto"])

    def test_ponta_a_ponta_tratamento_que_vira_manda_a_moeda_para_sem_leitura(self):
        """Reproduz o USD de 08/set: soma crua -1,19 (MANTÉM) e winsorizada -8,29 (CORTA).

        Com a winsorização de volta, a leitura sairia 'inclinado ao corte'. A guarda tem de
        pegar isso, levantar a bandeira e suspender a moeda — em vez de publicar a direção que
        veio do método.
        """
        agora = dt.datetime.now(dt.timezone.utc)
        antigo = (agora.date() - dt.timedelta(days=300)).isoformat()
        bancos = {"bancos": {"USD": {"ultima_mudanca_bp": -25, "ultima_mudanca": antigo,
                                     "reunioes": [], "sigla": "Fed"}}}

        real = S.dimensao_dados

        def com_winsorizacao(ev, moeda, agora_):
            d = real(ev, moeda, agora_)
            d["soma_crua"] = -1.19                      # o que os dados dizem
            d["soma"] = d["soma_tratada"] = -8.29       # o que o tratamento dizia
            d["direcao_crua"] = S.direcao_da_soma(-1.19)
            d["direcao"] = S.direcao_da_soma(-8.29)
            d["vota"] = True
            d["direcao_mudou_pelo_tratamento"] = True
            d["bandeira_de_direcao"] = "winsorização mudou MANTEM para CORTA"
            return d

        S.dimensao_dados = com_winsorizacao
        try:
            x = S.le_moeda("USD", [], bancos, None, agora, None, None, [])
        finally:
            S.dimensao_dados = real

        self.assertEqual("MANTEM", x["dimensoes"]["dados"]["direcao_crua"])
        self.assertEqual("CORTA", x["dimensoes"]["dados"]["direcao"])
        self.assertTrue(x["guarda_de_direcao"]["virou"])
        self.assertEqual("sem_leitura", x["leitura"])
        self.assertIn("depende do tratamento", x["leitura_motivo"])
        tipos = [b["tipo"] for b in x["bandeiras"]]
        self.assertIn("direcao_virada_por_tratamento", tipos)

    def test_virar_so_a_dimensao_tambem_suspende(self):
        """O buraco que a refutação de 08/set achou, preso por teste.

        A suspensão olhava SÓ para a leitura da moeda. Um tratamento pode virar a direção da
        DIMENSÃO DE DADOS sem virar a leitura — basta o ciclo carregar o sinal: soma crua
        +6,00 (SOBE) contra soma tratada -6,00 (CORTA), com uma alta de juro recente, saía com
        `direcao_mudou_pelo_tratamento: true`, leitura publicada 'inclinado à alta' e
        '1 de 2 dimensões concordam'. A direção da dimensão publicada era a do MÉTODO e a moeda
        continuava de pé. A lei diz SUSPENDE, e agora suspende nos dois níveis.
        """
        agora = dt.datetime.now(dt.timezone.utc)
        recente = (agora.date() - dt.timedelta(days=5)).isoformat()
        bancos = {"bancos": {"USD": {"ultima_mudanca_bp": +25, "ultima_mudanca": recente,
                                     "reunioes": [], "sigla": "Fed"}}}
        real = S.dimensao_dados

        def com_tratamento_que_vira_a_dimensao(ev, moeda, agora_):
            d = real(ev, moeda, agora_)
            d["soma_crua"] = 6.0
            d["soma"] = d["soma_tratada"] = -6.0
            d["direcao_crua"] = S.direcao_da_soma(6.0)
            d["direcao"] = S.direcao_da_soma(-6.0)
            d["vota"] = True
            d["direcao_mudou_pelo_tratamento"] = True
            d["bandeira_de_direcao"] = "tratamento de teste mudou SOBE para CORTA"
            return d

        S.dimensao_dados = com_tratamento_que_vira_a_dimensao
        try:
            x = S.le_moeda("USD", [], bancos, None, agora, None, None, [])
        finally:
            S.dimensao_dados = real

        # a leitura da moeda NÃO virou (o ciclo em alta segura o sinal)…
        self.assertFalse(x["guarda_de_direcao"]["virou"])
        self.assertEqual("inclinado_alta", x["leitura_crua"])
        # …e mesmo assim a moeda tem de sair suspensa, porque a DIMENSÃO virou
        self.assertEqual("sem_leitura", x["leitura"])
        self.assertIn("dimensão de dados", x["leitura_motivo"])
        marcadas = [b for b in x["bandeiras"] if b.get("muda_a_direcao")]
        self.assertTrue(marcadas)
        self.assertEqual("moeda suspensa em SEM LEITURA", marcadas[0].get("efeito"))


class FaixaNeutraTest(unittest.TestCase):
    """A FAIXA NEUTRA — o mesmo erro por baixo (auditoria de 08/set).

    A winsorização cortava os termos por CIMA; a faixa neutra zera termos por BAIXO. A
    aritmética é a mesma: zerar um termo x desloca a soma em -x. A faixa continua LIGADA
    porque tem tese econômica, mas não pode voltar a ser invisível — é isto que fica preso
    aqui, e não a atenção de quem lê.
    """

    @classmethod
    def setUpClass(cls):
        fn = RAIZ / "data" / "sentimento.json"
        cls.doc = json.loads(fn.read_text(encoding="utf-8")) if fn.exists() else None

    def test_a_faixa_sai_medida_em_todas_as_moedas(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, leitura in self.doc["moedas"].items():
            fx = leitura["dimensoes"]["dados"].get("faixa_neutra")
            self.assertIsNotNone(fx, "%s: falta faixa_neutra" % moeda)
            for campo in ("itens_zerados", "peso_que_os_zerados_teriam", "soma_sem_faixa",
                          "direcao_sem_faixa", "escala", "direcao_depende_da_faixa"):
                self.assertIn(campo, fx, "%s: falta %s" % (moeda, campo))

    def test_o_fator_1_reproduz_a_soma_publicada(self):
        """Se a coluna de fator 1,0 não bater com o que foi publicado, a comparação inteira
        é conversa fiada — é ela que dá sentido às outras três colunas."""
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, leitura in self.doc["moedas"].items():
            dd = leitura["dimensoes"]["dados"]
            um = [e for e in dd["faixa_neutra"]["escala"] if e["fator"] == 1.0]
            self.assertEqual(1, len(um), moeda)
            self.assertAlmostEqual(dd["soma"], um[0]["soma"], places=2, msg=moeda)

    def test_quando_a_direcao_depende_da_faixa_isso_aparece_no_par(self):
        """A lei do dono: o painel nunca esconde. O par é onde a tela lê."""
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        dependem = {m for m, L in self.doc["moedas"].items()
                    if (L["dimensoes"]["dados"].get("faixa_neutra") or {})
                    .get("direcao_depende_da_faixa")}
        for par in self.doc["pares"]:
            pernas = {par["base"], par["cotada"]} & dependem
            if not pernas:
                continue
            texto = " ".join(par.get("alertas") or [])
            for m in pernas:
                self.assertIn("FAIXA NEUTRA", texto, "%s: sem alerta" % par["par"])
                self.assertIn(m, texto, "%s: alerta não nomeia a perna %s" % (par["par"], m))

    def test_zerar_um_termo_desloca_a_soma_para_o_lado_contrario(self):
        """A aritmética, sem depender de dado do dia: a faixa é a winsorização por baixo."""
        medidos = [{"dif": 9.0, "peso": 9, "sinal": 1, "mod": 1.0, "decai": 1.0, "corte": 1.0,
                    "classe": "MUITO_ACIMA", "titulo": "grande", "familia": "x"}]
        # dez itens pequenos, todos do lado de baixo, TODOS dentro da faixa de hoje
        for i in range(10):
            medidos.append({"dif": -0.5, "peso": 2, "sinal": 1, "mod": 1.0, "decai": 1.0,
                            "corte": 1.0, "classe": "EM_LINHA", "titulo": "peq%d" % i,
                            "familia": "x"})
        f = S.mede_faixa_neutra(medidos, "TESTE", 9.0)
        self.assertEqual(10, f["itens_zerados"])
        self.assertEqual(-20.0, f["peso_que_os_zerados_teriam"])
        self.assertEqual(-11.0, f["soma_sem_faixa"])          # 9 - 20
        self.assertTrue(f["direcao_depende_da_faixa"])
        self.assertEqual("SOBE", S.direcao_da_soma(9.0))
        self.assertEqual("CORTA", f["direcao_sem_faixa"])


class RampaDoCicloTest(unittest.TestCase):
    """O piso do ciclo virou RAMPA — conserto 2.2, 08/set/2026.

    O piso de 0,25 era um degrau: aos 240 dias a contribuição caía de 0,0625 para 0,0000 de
    um dia para o outro, e QUATRO das oito moedas estavam logo abaixo dele. Estes testes
    prendem a continuidade sem depender do dado do dia.
    """

    def test_a_rampa_e_continua_no_joelho(self):
        j = S.CICLO_JOELHO_RAMPA
        e = 1e-9
        self.assertAlmostEqual(S.peso_do_ciclo(j - e), S.peso_do_ciclo(j + e), places=7)
        # e o valor no joelho é o próprio joelho: d²/j = j quando d = j
        self.assertAlmostEqual(j, S.peso_do_ciclo(j), places=9)

    def test_a_regra_velha_tinha_degrau_e_a_nova_nao(self):
        j = S.CICLO_JOELHO_RAMPA
        salto_velho = abs(S.peso_do_ciclo_antes(j) - S.peso_do_ciclo_antes(j - 0.001))
        salto_novo = abs(S.peso_do_ciclo(j) - S.peso_do_ciclo(j - 0.001))
        self.assertAlmostEqual(j, salto_velho, places=6)      # o degrau inteiro
        self.assertLess(salto_novo, 0.01)

    def test_acima_do_joelho_nada_muda(self):
        for d in (0.25, 0.3, 0.5, 0.75, 1.0):
            self.assertAlmostEqual(d, S.peso_do_ciclo(d), places=9)
            self.assertAlmostEqual(S.peso_do_ciclo_antes(d), S.peso_do_ciclo(d), places=9)

    def test_a_rampa_e_monotona_e_vai_a_zero(self):
        self.assertEqual(0.0, S.peso_do_ciclo(0.0))
        ant = -1.0
        for i in range(0, 101):
            v = S.peso_do_ciclo(i / 100.0)
            self.assertGreaterEqual(v + 1e-12, ant)
            ant = v

    def test_a_prova_publicada_diz_que_nao_ha_degrau(self):
        t = S.tabela_da_rampa()
        self.assertTrue(t["ha_degrau_antes"])        # o piso não encolhe com a grade fina
        self.assertFalse(t["ha_degrau_depois"])      # a rampa encolhe junto com o passo
        self.assertAlmostEqual(0.0625, t["maior_salto_entre_dois_centesimos_antes"], places=4)

    def test_nenhum_numero_novo_entrou(self):
        """O joelho é o PRÓPRIO número do piso revogado — isto não é calibração."""
        self.assertEqual(0.25, S.CICLO_JOELHO_RAMPA)
        self.assertEqual(S.CICLO_JOELHO_RAMPA, S.CICLO_PISO_VOTO)
        self.assertEqual(0, S.RAMPA_DO_CICLO["numeros_novos"])

    def test_a_direcao_do_ciclo_e_o_fato_e_o_regime_e_a_palavra(self):
        """Movimento antigo: a dimensão declara o FATO com peso pequeno; o regime diz parado."""
        b = {"ultima_mudanca_bp": -25, "ultima_mudanca": "2025-06-19", "reunioes": []}
        agora = dt.datetime(2026, 9, 8, tzinfo=dt.timezone.utc)
        cc = S.dimensao_ciclo(b, agora)
        self.assertEqual("CORTA", cc["direcao"])          # o fato: o último movimento foi corte
        self.assertLess(cc["peso"], S.CICLO_JOELHO_RAMPA)
        self.assertGreater(cc["peso"], 0.0)               # não é mais zero seco
        self.assertFalse(cc["ainda_pesa"])
        regime, _motivo = S.regime_do_banco(cc, None, b)
        self.assertEqual("manutencao", regime)            # a palavra continua honesta


class RobustezDeParametroTest(unittest.TestCase):
    """CONSERTO 2.1 — a direção não pode depender de botão que ninguém calibrou.

    A guarda de direção prende o TRATAMENTO. Isto prende o PARÂMETRO, que é a mesma família de
    erro um andar acima: em 08/set o auditor mostrou que, só girando a MEIA_VIDA, o dólar
    percorria SOBE → MANTÉM → CORTA sem um único dado mudar.
    """

    @classmethod
    def setUpClass(cls):
        fn = RAIZ / "data" / "sentimento.json"
        cls.doc = json.loads(fn.read_text(encoding="utf-8")) if fn.exists() else None

    # ---- a faixa declarada ------------------------------------------------------------
    def test_a_faixa_cobre_os_dois_extremos_defensaveis_e_o_ponto_de_hoje(self):
        pares = {(v["medio"], v["baixo"]) for v in S.GRADE_MODULADOR}
        self.assertIn((0.0, 0.0), pares, "falta o extremo 'só alto conta'")
        self.assertIn((1.0, 1.0), pares, "falta o extremo 'plano'")
        self.assertIn((S.MOD_HOJE["medio"], S.MOD_HOJE["baixo"]), pares,
                      "a grade tem de conter o ponto que está publicado")
        for v in S.GRADE_MODULADOR:            # 0 <= baixo <= medio <= alto = 1
            self.assertLessEqual(v["baixo"], v["medio"])
            self.assertLessEqual(v["medio"], v["alto"])
            self.assertEqual(1.0, v["alto"])
        self.assertEqual(14.0, min(S.GRADE_MEIA_VIDA))
        self.assertEqual(30.0, max(S.GRADE_MEIA_VIDA))
        self.assertIn(float(S.MEIA_VIDA), S.GRADE_MEIA_VIDA)

    def test_a_aritmetica_da_celula(self):
        """Meia-vida e modulador entram exatamente como entram na soma publicada."""
        medidos = [{"forca": 4.0, "idade": 21.0, "chave_mod": "alto"},
                   {"forca": -2.0, "idade": 0.0, "chave_mod": "medio"},
                   {"forca": 10.0, "idade": 0.0, "chave_mod": "baixo"},
                   {"forca": 0.0, "idade": 0.0, "chave_mod": "alto"}]   # EM_LINHA: não entra
        hoje = {"alto": 1.0, "medio": 0.5, "baixo": 0.2}
        # 4,0 com meia-vida 21 e idade 21 = 2,00 · -2,0 x 0,5 = -1,00 · 10 x 0,2 = 2,00
        self.assertEqual(3.0, S.soma_da_dimensao_com(medidos, 21.0, hoje))
        # "só alto conta" apaga os dois últimos: sobra 2,00
        so_alto = {"alto": 1.0, "medio": 0.0, "baixo": 0.0}
        self.assertEqual(2.0, S.soma_da_dimensao_com(medidos, 21.0, so_alto))
        # "plano" põe os três em 1,0: 2,00 - 2,00 + 10,00 = 10,00
        plano = {"alto": 1.0, "medio": 1.0, "baixo": 1.0}
        self.assertEqual(10.0, S.soma_da_dimensao_com(medidos, 21.0, plano))
        # meia-vida 42 dobra o peso do item velho: 4,0 x 0,5^0,5 = 2,83
        self.assertAlmostEqual(2.83 - 1.0 + 2.0, S.soma_da_dimensao_com(medidos, 42.0, hoje),
                               places=2)

    # ---- o que o arquivo publicado tem de mostrar ---------------------------------------
    def test_a_grade_sai_medida_em_todas_as_moedas(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, L in self.doc["moedas"].items():
            rb = L.get("robustez_de_parametro")
            self.assertIsNotNone(rb, "%s: falta robustez_de_parametro" % moeda)
            for campo in ("concordancia_pct", "direcoes_encontradas", "qual_parametro_faz_virar",
                          "vira_pela_meia_vida", "vira_pelo_modulador", "linha_meia_vida",
                          "linha_modulador", "celulas", "corte_pct", "dimensao"):
                self.assertIn(campo, rb, "%s: falta %s" % (moeda, campo))
            self.assertEqual(S.GRADE_CELULAS, rb["celulas"], moeda)

    def test_a_celula_de_hoje_reproduz_o_publicado(self):
        """Se a célula 1× não reproduzir o arquivo, a comparação inteira é conversa fiada."""
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, L in self.doc["moedas"].items():
            rb = L["robustez_de_parametro"]
            self.assertTrue(rb["celula_de_hoje_reproduz_o_publicado"], moeda)
            self.assertEqual(L["dimensoes"]["dados"]["soma"], rb["celula_de_hoje"]["soma"],
                             "%s: a célula de hoje tem de dar a soma publicada" % moeda)

    def test_a_robustez_nunca_muda_a_direcao_so_suspende(self):
        """É medida de CONFIANÇA: ou a leitura fica como estava, ou vai para SEM LEITURA."""
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, L in self.doc["moedas"].items():
            if L["leitura"] != L.get("leitura_antes_da_guarda"):
                self.assertEqual("sem_leitura", L["leitura"],
                                 "%s: a única mudança permitida é suspender" % moeda)

    def test_abaixo_do_corte_a_moeda_fica_sem_leitura(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, L in self.doc["moedas"].items():
            rb = L["robustez_de_parametro"]
            if rb["concordancia_pct"] < S.ROBUSTEZ_CORTE_CONCORDANCIA_PCT:
                self.assertEqual("sem_leitura", L["leitura"],
                                 "%s: concordância %d%% abaixo do corte tem de suspender"
                                 % (moeda, rb["concordancia_pct"]))

    def test_a_evidencia_fica_limitada_pela_concordancia(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, L in self.doc["moedas"].items():
            rb = L["robustez_de_parametro"]
            nota = (L.get("qualidade_evidencia") or {}).get("nota")
            if rb["concordancia_pct"] < 100 and nota is not None:
                self.assertLessEqual(nota, rb["concordancia_pct"],
                                     "%s: a nota não pode passar da concordância" % moeda)

    def test_a_bandeira_aparece_quando_a_grade_discorda(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        for moeda, L in self.doc["moedas"].items():
            rb = L["robustez_de_parametro"]
            tipos = {x.get("tipo") for x in (L.get("bandeiras") or [])}
            self.assertEqual(rb["concordancia_pct"] < 100, "robustez_de_parametro" in tipos,
                             "%s: bandeira e concordância têm de andar juntas" % moeda)

    def test_a_grade_e_barata(self):
        """O orçamento do dono é 10 s na cadeia inteira. Isto tem de ser ruído."""
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        total = sum(L["robustez_de_parametro"]["custo_ms"]
                    for L in self.doc["moedas"].values())
        self.assertLess(total, 1000.0, "a grade custou %.0f ms nas 8 moedas" % total)

    def test_o_par_avisa_quando_uma_perna_e_fragil(self):
        if not self.doc:
            self.skipTest("data/sentimento.json ainda não foi gerado")
        frageis = {m for m, L in self.doc["moedas"].items()
                   if L["robustez_de_parametro"]["bandeira"]}
        if not frageis:
            self.skipTest("nenhuma moeda frágil nesta rodada")
        for r in self.doc["pares"]:
            tem = bool({r["base"], r["cotada"]} & frageis)
            avisa = any("PARÂMETRO NÃO CALIBRADO" in a for a in r["alertas"])
            self.assertEqual(tem, avisa, "%s: alerta e fragilidade têm de andar juntos"
                             % r["par"])


if __name__ == "__main__":
    unittest.main()
