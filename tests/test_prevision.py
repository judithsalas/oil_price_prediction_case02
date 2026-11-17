import unittest

from app.prevision import fiabilidad


class TestFiabilidad(unittest.TestCase):
    def test_solo_aporta_valor_si_mejora_de_forma_significativa(self):
        def nivel(mejora, p):
            return fiabilidad({'mejora_test_%': mejora, 'p_valor': p})[0]
        self.assertEqual(nivel(10, 0.01), 'bien')
        self.assertEqual(nivel(10, 0.30), 'aviso')     # mejora, pero puede ser ruido
        self.assertEqual(nivel(-2, 0.16), 'aviso')     # empata con el ingenuo
        self.assertEqual(nivel(-26, 0.16), 'mal')


if __name__ == '__main__':
    unittest.main()
