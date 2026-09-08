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


if __name__ == "__main__":
    unittest.main()
