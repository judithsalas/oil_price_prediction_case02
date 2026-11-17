import unittest

import pandas as pd

from scripts.entrenar import media_semillas


class TestMediaSemillas(unittest.TestCase):
    def test_puntua_la_prediccion_media_no_la_media_de_errores(self):
        # Dos semillas que fallan en sentidos opuestos: su media acierta
        filas = [{'horizonte': 'corto', 'red': 'gru', 'oculto': 16, 'pliegue': 0,
                  'semilla': s, 'dia': d, 'y': 1.0, 'pred': 1.0 + signo}
                 for s, signo in [(0, 0.5), (1, -0.5)] for d in ('2019-01-02', '2019-01-03')]
        r = media_semillas(pd.DataFrame(filas), ['oculto'])
        self.assertEqual(r.loc[('corto', 'gru', 16), 'mse_val'], 0.0)
        self.assertEqual(r.loc[('corto', 'gru', 16), 'ingenuo_val'], 1.0)


if __name__ == '__main__':
    unittest.main()
