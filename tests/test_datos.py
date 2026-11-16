import unittest

import numpy as np
import pandas as pd

from petroleo.datos import comprobar_columnas, limpiar


class TestLimpiar(unittest.TestCase):
    def test_no_inventa_precios_del_brent(self):
        dias = pd.to_datetime(['2024-12-24', '2024-12-25', '2024-12-26'])
        datos = pd.DataFrame({'brent': [73.0, np.nan, 74.0],
                              'oro':   [np.nan, 2600.0, np.nan]}, index=dias)

        limpio = limpiar(datos)

        # El 25 (festivo del Brent) desaparece; no se copia el 73.0
        self.assertEqual(list(limpio.index), [dias[0], dias[2]])
        # El oro del festivo sí se propaga al día siguiente
        self.assertEqual(limpio.loc[dias[2], 'oro'], 2600.0)


class TestComprobarColumnas(unittest.TestCase):
    def test_para_si_una_fuente_viene_vacia(self):
        datos = pd.DataFrame({'brent': [73.0, 74.0], 'oro': [np.nan, np.nan]})
        with self.assertRaisesRegex(RuntimeError, 'oro'):
            comprobar_columnas(datos)


if __name__ == '__main__':
    unittest.main()
