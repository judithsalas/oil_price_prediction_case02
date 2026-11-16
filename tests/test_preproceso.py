import unittest

import numpy as np
import pandas as pd

from petroleo.preproceso import preparar, quitar_outliers

FIN_TRAIN, FIN_VAL = '2001-06-29', '2001-12-31'
VENTANA, H = 10, 5


def serie_falsa():
    dias = pd.bdate_range('2000-01-03', '2002-06-28')
    brent = 20 + np.arange(len(dias)) * 0.1
    return pd.DataFrame({'brent': brent, 'wti': brent - 1,
                         'tipo_bce': -0.5}, index=dias)


class TestPreparar(unittest.TestCase):
    def test_ningun_objetivo_sale_de_su_particion(self):
        datos = serie_falsa()
        partes, _ = preparar(datos, VENTANA, H, FIN_TRAIN, FIN_VAL)
        dias = datos.index
        for nombre, fin in [('train', FIN_TRAIN), ('val', FIN_VAL)]:
            ultimo_dia = partes[nombre][2].max()
            objetivo = dias[dias.get_loc(ultimo_dia) + H]
            self.assertLessEqual(objetivo, pd.Timestamp(fin), nombre)
        self.assertGreater(partes['val'][2].min(), pd.Timestamp(FIN_TRAIN))
        self.assertGreater(partes['test'][2].min(), pd.Timestamp(FIN_VAL))

    def test_escalador_no_ve_datos_futuros(self):
        datos = serie_falsa()
        _, esc = preparar(datos, VENTANA, H, FIN_TRAIN, FIN_VAL)
        alterados = datos.copy()
        alterados.loc[alterados.index > FIN_TRAIN, 'brent'] *= 100
        _, esc2 = preparar(alterados, VENTANA, H, FIN_TRAIN, FIN_VAL)
        np.testing.assert_array_equal(esc.mean_, esc2.mean_)

    def test_ventana_y_objetivo_cuadran(self):
        datos = serie_falsa()
        partes, esc = preparar(datos, VENTANA, H, FIN_TRAIN, FIN_VAL)
        X, y, dias = partes['train']
        i = datos.index.get_loc(dias[0])
        # La última fila de la ventana es el día t, sin escalar = brent[t]
        brent_t = X[0, -1, 0] * esc.scale_[0] + esc.mean_[0]
        self.assertAlmostEqual(brent_t, datos['brent'].iloc[i], places=3)
        esperado = np.log(datos['brent'].iloc[i + H] / datos['brent'].iloc[i])
        self.assertAlmostEqual(float(y[0]), esperado, places=5)
        self.assertEqual(X.shape[1:], (VENTANA, 3))


class TestQuitarOutliers(unittest.TestCase):
    def test_wti_negativo_se_rellena_y_tipo_bce_no(self):
        datos = serie_falsa().iloc[:3].copy()
        datos.loc[datos.index[1], 'wti'] = -37.63
        limpio = quitar_outliers(datos)
        self.assertEqual(limpio['wti'].iloc[1], datos['wti'].iloc[0])
        self.assertTrue((limpio['tipo_bce'] == -0.5).all())


if __name__ == '__main__':
    unittest.main()
