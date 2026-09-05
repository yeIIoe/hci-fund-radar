import datetime as dt
import json
import os
import tempfile
import unittest

import bancos_centrais


class BancosIntegridadeTests(unittest.TestCase):
    def test_rbnz_publicado_atualiza_taxa_e_movimento(self):
        evento = {
            "divulgado": 2.75, "anterior": 2.50, "fonte": "fxstreet",
            "_quando": dt.datetime(2026, 9, 2, 2, tzinfo=dt.timezone.utc),
        }
        out = bancos_centrais.reconcilia_taxa("NZD", bancos_centrais.BANCOS["NZD"], evento)
        self.assertEqual(out["taxa"], 2.75)
        self.assertEqual(out["taxa_texto"], "2,75%")
        self.assertEqual(out["ultima_mudanca"], "2026-09-02")
        self.assertEqual(out["ultima_mudanca_bp"], 25)

    def test_manutencao_nao_apaga_ultimo_movimento(self):
        evento = {
            "divulgado": 2.25, "anterior": 2.25, "fonte": "fxstreet",
            "_quando": dt.datetime(2026, 9, 2, 13, 45, tzinfo=dt.timezone.utc),
        }
        out = bancos_centrais.reconcilia_taxa("CAD", bancos_centrais.BANCOS["CAD"], evento)
        self.assertEqual(out["ultima_decisao_resultado"], "manutencao")
        self.assertEqual(out["ultima_mudanca"], bancos_centrais.BANCOS["CAD"]["ultima_mudanca"])

    def test_resultado_futuro_nao_atualiza_taxa(self):
        doc = {"eventos": [
            {"moeda": "NZD", "titulo": "RBNZ Interest Rate Decision",
             "quando_utc": "2026-09-02T02:00:00+00:00", "divulgado": 2.75},
            {"moeda": "EUR", "titulo": "ECB Rate On Deposit Facility",
             "quando_utc": "2026-09-10T12:15:00+00:00", "divulgado": 2.50},
        ]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as f:
            json.dump(doc, f)
            caminho = f.name
        try:
            agora = dt.datetime(2026, 9, 5, tzinfo=dt.timezone.utc)
            out = bancos_centrais.decisoes_publicadas(agora, caminho)
            self.assertIn("NZD", out)
            self.assertNotIn("EUR", out)
        finally:
            os.unlink(caminho)


if __name__ == "__main__":
    unittest.main()
