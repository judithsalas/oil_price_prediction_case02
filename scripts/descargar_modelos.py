# Descarga de Hugging Face los modelos del estudio que falten en models/final/.
#     poetry run python -m scripts.descargar_modelos
# Los modelos no están en git. La app los descarga sola al arrancar; a mano solo hace
# falta para evaluar (pasos 4 y 5 del README) sin haber entrenado antes.
from urllib.request import urlopen

from petroleo.modelos import TIPOS
from scripts.evaluar import MODELOS

URL = 'https://huggingface.co/judithsalas/prevision-brent/resolve/main/final/'
HORIZONTES = ('corto', 'medio', 'largo')


def descargar(carpeta=MODELOS, url=URL):
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre in (f'{red}_{h}.pt' for red in TIPOS for h in HORIZONTES):
        destino = carpeta / nombre
        if destino.exists():
            continue
        print(f'Descargando {url}{nombre}')
        with urlopen(url + nombre, timeout=60) as respuesta:
            contenido = respuesta.read()
        parcial = destino.with_suffix('.parcial')
        parcial.write_bytes(contenido)
        parcial.replace(destino)      # el .pt solo aparece si se escribió entero


if __name__ == '__main__':
    descargar()
