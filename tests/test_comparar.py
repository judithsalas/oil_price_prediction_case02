import unittest

import numpy as np
import pandas as pd

from scripts.comparar import errores_en_dolares, intervalo


class TestIntervalo(unittest.TestCase):
    def test_deja_dentro_el_80_por_ciento_de_los_errores(self):
        error = np.random.default_rng(0).normal(0, 1, 10_000)
        bajo, alto = intervalo(error)
        self.assertAlmostEqual(np.mean((error >= bajo) & (error <= alto)), 0.8, delta=0.001)
        self.assertAlmostEqual(alto, 1.28, delta=0.05)      # percentil 90 de la normal


class TestErroresEnDolares(unittest.TestCase):
    def test_r2_vale_1_si_acierta_y_0_si_preve_siempre_la_media(self):
        real = pd.Series([60.0, 80.0, 100.0])

        perfecto = errores_en_dolares(real, real)
        media = errores_en_dolares(real, pd.Series([80.0, 80.0, 80.0]))

        self.assertEqual((perfecto['r2'], perfecto['mse_$2']), (1.0, 0.0))
        self.assertAlmostEqual(media['r2'], 0.0)
        self.assertAlmostEqual(media['mae_$'], 40 / 3)            # errores de 20, 0 y 20 $
        self.assertAlmostEqual(media['mse_$2'], 800 / 3)
        self.assertAlmostEqual(media['rmse_$'], (800 / 3) ** 0.5)


if __name__ == '__main__':
    unittest.main()
