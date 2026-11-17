import unittest

import numpy as np
import torch

from petroleo.entrenamiento import entrenar, mse, predecir
from petroleo.modelos import Recurrente


def lote(n, semilla, ruido=False):
    g = np.random.default_rng(semilla)
    X = g.standard_normal((n, 10, 3)).astype(np.float32)
    y = g.standard_normal(n).astype(np.float32) if ruido else X[:, -1].mean(axis=1)
    return X, y


class TestEntrenar(unittest.TestCase):
    def test_deja_los_pesos_de_la_mejor_epoca(self):
        torch.manual_seed(0)
        modelo = Recurrente('gru', 3, oculto=8)
        val = lote(64, 1)
        r = entrenar(modelo, lote(256, 0), val, epocas=10)
        self.assertAlmostEqual(mse(modelo, *val), r['mse_val'], places=6)

    def test_para_pronto_si_validacion_no_mejora(self):
        # y es ruido puro: validación deja de mejorar enseguida
        torch.manual_seed(0)
        modelo = Recurrente('lstm', 3, oculto=8)
        r = entrenar(modelo, lote(256, 0, ruido=True), lote(64, 1, ruido=True),
                     epocas=100, paciencia=3)
        self.assertLess(r['epocas'], 100)
        self.assertEqual(len(r['historial']['mse_val']), r['epocas'])
        self.assertEqual(min(r['historial']['mse_val']), r['mse_val'])


    def test_predice_sin_la_tendencia_de_train(self):
        # y = 0,5 + ruido: la red aprende la desviación y no la subida media
        torch.manual_seed(0)
        (X, ruido), (Xv, ruido_v) = lote(256, 0, ruido=True), lote(64, 1, ruido=True)
        modelo = Recurrente('gru', 3, oculto=8)
        entrenar(modelo, (X, 0.5 + 0.1 * ruido), (Xv, 0.5 + 0.1 * ruido_v), epocas=5)
        self.assertLess(abs(predecir(modelo, X).mean()), 0.1)


if __name__ == '__main__':
    unittest.main()
