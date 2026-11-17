import unittest

import numpy as np

from scripts.comparar import intervalo


class TestIntervalo(unittest.TestCase):
    def test_deja_dentro_el_80_por_ciento_de_los_errores(self):
        error = np.random.default_rng(0).normal(0, 1, 10_000)
        bajo, alto = intervalo(error)
        self.assertAlmostEqual(np.mean((error >= bajo) & (error <= alto)), 0.8, delta=0.001)
        self.assertAlmostEqual(alto, 1.28, delta=0.05)      # percentil 90 de la normal


if __name__ == '__main__':
    unittest.main()
