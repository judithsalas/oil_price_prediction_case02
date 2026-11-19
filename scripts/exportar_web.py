# Genera en web/ la web estática que se publica en Vercel: la página de
# app/static más datos.json con la previsión de hoy.
#     poetry run python -m scripts.exportar_web [--reentrenar]
# La ejecuta GitHub Actions (.github/workflows/web.yml): cada día laborable
# descarga datos y recalcula; el día 1 de cada mes, además, reentrena.
import argparse
import json
import shutil
from datetime import datetime, timezone

from app import prevision
from scripts.descargar_modelos import descargar as descargar_modelos
from scripts.evaluar import RAIZ

ESTATICOS = RAIZ / 'app' / 'static'
WEB = RAIZ / 'web'


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--reentrenar', action='store_true', help='reentrena antes de calcular')
    args.add_argument('--sin-descarga', action='store_true', help='usa los datos que ya hay')
    args = args.parse_args()

    descargar_modelos()     # los modelos no están en git: se bajan de Hugging Face
    if not args.sin_descarga:
        prevision.actualizar_datos()
    if args.reentrenar:
        prevision.reentrenar()
    datos = {**prevision.resumen(), 'generado': datetime.now(timezone.utc).isoformat(timespec='minutes')}

    shutil.copytree(ESTATICOS, WEB, dirs_exist_ok=True)
    (WEB / 'datos.json').write_text(json.dumps(datos, default=float, ensure_ascii=False))
    print(f'Web en {WEB}: previsión con datos hasta {datos["prevision"][0]["fecha_hoy"]}')


if __name__ == '__main__':
    main()
