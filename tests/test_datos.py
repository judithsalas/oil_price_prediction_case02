import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import numpy as np
import pandas as pd

from petroleo.datos import comprobar_columnas, descargar_fred, limpiar


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


class TestDescargarFred(unittest.TestCase):
    def test_reintenta_un_fallo_pasajero_del_servidor(self):
        fallo = HTTPError('url', 502, 'Bad Gateway', None, None)
        tabla = pd.DataFrame({'DCOILBRENTEU': [73.0]}, index=pd.to_datetime(['2024-12-24']))
        with patch('petroleo.datos.pd.read_csv', side_effect=[fallo, tabla]) as leer, \
                patch('petroleo.datos.time.sleep') as esperar:
            serie = descargar_fred('DCOILBRENTEU', '2024-12-31')

        self.assertEqual(leer.call_count, 2)
        esperar.assert_called_once()
        self.assertEqual(serie.name, 'brent')

    def test_no_reintenta_si_la_serie_no_existe(self):
        fallo = HTTPError('url', 404, 'Not Found', None, None)
        with patch('petroleo.datos.pd.read_csv', side_effect=fallo) as leer, \
                patch('petroleo.datos.time.sleep'):
            with self.assertRaises(HTTPError):
                descargar_fred('DCOILBRENTEU', '2024-12-31')

        self.assertEqual(leer.call_count, 1)


if __name__ == '__main__':
    unittest.main()
