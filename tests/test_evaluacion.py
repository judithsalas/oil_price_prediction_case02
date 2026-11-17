import unittest

import numpy as np

from petroleo.evaluacion import acierto_direccion, diebold_mariano, ridge


class TestDieboldMariano(unittest.TestCase):
    def test_detecta_un_modelo_claramente_mejor(self):
        g = np.random.default_rng(0)
        bueno, malo = g.normal(0, 1, 500), g.normal(0, 2, 500)
        dm, p = diebold_mariano(bueno, malo, h=1)
        self.assertLess(dm, 0)
        self.assertLess(p, 0.01)

    def test_con_modelos_iguales_se_equivoca_un_5_por_ciento(self):
        # Si H0 es cierta, p < 0,05 debe salir en ~5 % de las muestras
        g = np.random.default_rng(1)
        p = [diebold_mariano(*g.normal(0, 1, (2, 300)), h=1)[1] for _ in range(1000)]
        self.assertAlmostEqual(np.mean(np.array(p) < 0.05), 0.05, delta=0.02)

    def test_el_solapamiento_resta_confianza(self):
        # Mismos errores: con h grande la varianza crece y el p-valor también
        g = np.random.default_rng(2)
        a = np.repeat(g.normal(0, 1, 50), 20)      # errores muy autocorrelados
        b = np.repeat(g.normal(0, 1.3, 50), 20)
        self.assertGreater(diebold_mariano(a, b, h=20)[1], diebold_mariano(a, b, h=1)[1])


class TestRidge(unittest.TestCase):
    def test_elige_alfa_en_val_y_aprende_una_relacion_lineal(self):
        g = np.random.default_rng(0)

        def parte(n):
            X = g.normal(size=(n, 5, 2)).astype(np.float32)
            return X, X[:, -1, 0] + 0.01 * g.normal(size=n)

        partes = {'train': parte(300), 'parada': parte(50), 'val': parte(100)}
        modelo, alfa = ridge(partes)
        Xv, yv = partes['val']
        self.assertLess(np.mean((modelo.predict(Xv.reshape(100, -1)) - yv) ** 2), 0.01)
        self.assertLessEqual(alfa, 10)


class TestDireccion(unittest.TestCase):
    def test_cuenta_aciertos_de_signo(self):
        self.assertEqual(acierto_direccion(np.array([1, -1, 1, 1]),
                                           np.array([2, -3, -1, 5])), 0.75)


if __name__ == '__main__':
    unittest.main()
