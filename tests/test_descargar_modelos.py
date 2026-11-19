import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from scripts.descargar_modelos import descargar


class TestDescargar(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.remoto, self.local = Path(tmp.name, 'remoto'), Path(tmp.name, 'local')
        self.remoto.mkdir()
        self.url = self.remoto.as_uri() + '/'       # urlopen también lee file://
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))    # sin los avisos de descarga

    def publicar(self, redes=('rnn', 'lstm', 'gru')):
        for red in redes:
            for h in ('corto', 'medio', 'largo'):
                (self.remoto / f'{red}_{h}.pt').write_text(f'pesos de {red}_{h}')

    def test_baja_los_nueve_modelos_que_faltan(self):
        self.publicar()
        descargar(self.local, self.url)
        self.assertEqual(len(list(self.local.iterdir())), 9)
        self.assertEqual((self.local / 'gru_medio.pt').read_text(), 'pesos de gru_medio')

    def test_no_pisa_un_modelo_que_ya_esta(self):
        self.publicar()
        self.local.mkdir()
        (self.local / 'rnn_corto.pt').write_text('entrenado aquí')
        descargar(self.local, self.url)
        self.assertEqual((self.local / 'rnn_corto.pt').read_text(), 'entrenado aquí')

    def test_si_una_descarga_falla_no_deja_un_modelo_a_medias(self):
        self.publicar(redes=('rnn',))               # faltan los de lstm y gru
        with self.assertRaises(OSError):
            descargar(self.local, self.url)
        self.assertEqual(sorted(p.name for p in self.local.iterdir()),
                         ['rnn_corto.pt', 'rnn_largo.pt', 'rnn_medio.pt'])


if __name__ == '__main__':
    unittest.main()
