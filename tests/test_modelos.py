import unittest

import torch

from petroleo.modelos import TIPOS, Recurrente, ingenuo, n_parametros

LOTE, VENTANA, ENTRADAS = 8, 10, 3


class TestRecurrente(unittest.TestCase):
    def test_las_tres_redes_dan_una_prediccion_por_muestra(self):
        x = torch.randn(LOTE, VENTANA, ENTRADAS)
        for tipo in TIPOS:
            self.assertEqual(Recurrente(tipo, ENTRADAS)(x).shape, (LOTE,), tipo)

    def test_lstm_y_gru_tienen_mas_parametros_que_rnn(self):
        n = {t: n_parametros(Recurrente(t, ENTRADAS, oculto=16)) for t in TIPOS}
        self.assertLess(n['rnn'], n['gru'])
        self.assertLess(n['gru'], n['lstm'])

    def test_memoria_ortogonal_y_olvido_de_la_lstm_a_1(self):
        oculto = 16
        for tipo in TIPOS:
            red = Recurrente(tipo, ENTRADAS, oculto=oculto, capas=2).red
            for puerta in red.weight_hh_l1.detach().split(oculto):
                torch.testing.assert_close(puerta @ puerta.T, torch.eye(oculto),
                                           atol=1e-5, rtol=0)
        sesgo = Recurrente('lstm', ENTRADAS, oculto=oculto).red.bias_ih_l0.detach()
        self.assertTrue((sesgo[oculto:2 * oculto] == 1).all())   # puerta f
        self.assertEqual(sesgo[:oculto].abs().sum(), 0)           # puerta i

    def test_aprende_un_patron_sencillo(self):
        # y = media del último día: si no baja el error, algo está roto
        torch.manual_seed(0)
        x = torch.randn(64, VENTANA, ENTRADAS)
        y = x[:, -1].mean(dim=1)
        for tipo in TIPOS:
            modelo = Recurrente(tipo, ENTRADAS, oculto=16)
            opt = torch.optim.Adam(modelo.parameters(), lr=1e-2)
            inicial = torch.mean((modelo(x) - y) ** 2).item()
            for _ in range(100):
                opt.zero_grad()
                perdida = torch.mean((modelo(x) - y) ** 2)
                perdida.backward()
                opt.step()
            self.assertLess(perdida.item(), inicial / 5, tipo)


class TestIngenuo(unittest.TestCase):
    def test_predice_que_el_precio_no_cambia(self):
        self.assertTrue((ingenuo(torch.zeros(5, VENTANA, ENTRADAS)) == 0).all())


if __name__ == '__main__':
    unittest.main()
