import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class SentimentoConsistenciaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((ROOT / "data" / "sentimento.json").read_text(encoding="utf-8"))

    def test_direcao_publicada_segue_leitura_final(self):
        esperado = {"inclinado_alta": "SOBE", "inclinado_corte": "CORTA", "sem_leitura": "MANTEM"}
        for moeda, leitura in self.doc["moedas"].items():
            if leitura.get("leitura") not in esperado:
                continue
            self.assertEqual(esperado[leitura["leitura"]], leitura.get("direcao"), moeda)

    def test_concordancia_compara_dimensao_com_direcao_final(self):
        for moeda, leitura in self.doc["moedas"].items():
            formada = leitura.get("leitura") in ("inclinado_alta", "inclinado_corte")
            dimensoes = leitura.get("dimensoes") or {}
            for nome, marcou in (leitura.get("concordam") or {}).items():
                esperado = bool(formada and dimensoes[nome]["direcao"] == leitura["direcao"])
                self.assertEqual(esperado, marcou, "%s/%s" % (moeda, nome))

    def test_sem_leitura_nao_afirma_concordancia_direcional(self):
        for moeda, leitura in self.doc["moedas"].items():
            if leitura.get("leitura") == "sem_leitura":
                self.assertNotIn("concordam", leitura.get("concordancia_texto", ""), moeda)


if __name__ == "__main__":
    unittest.main()
