# Figuras de resumen para el README y la presentación, a partir de resultados ya
# guardados (no entrena ni vuelve a evaluar en test):
#     poetry run python -m scripts.figuras
# Guarda en docs/figuras/: historia.png, walk_forward.png, validacion_vs_test.png
# y test_elegido.png. Necesita data/petroleo_dataset.csv y los CSV de
# docs/resultados (scripts/evaluar.py y scripts/comparar.py).
import pandas as pd
import yaml

from petroleo import graficas
from petroleo.datos import RUTA_CSV
from petroleo.preproceso import PARADA, quitar_outliers, seleccionar
from scripts.evaluar import FIGURAS, RAIZ, RESULTADOS

# Los mismos picos y caídas, en el mismo orden, que EVENTOS en app/static/app.js
PICOS = ['2008-07-03', '2008-12-26', '2014-06-19', '2016-01-20',
         '2020-04-21', '2022-03-08', '2025-12-16', '2026-04-07']


def main():
    cfg = yaml.safe_load((RAIZ / 'configs' / 'experimento.yaml').read_text())
    brent = seleccionar(quitar_outliers(pd.read_csv(RUTA_CSV, index_col=0, parse_dates=True)))['brent']
    comp = pd.read_csv(RESULTADOS / 'comparativa.csv')
    intervalos = pd.read_csv(RESULTADOS / 'intervalos.csv').set_index(['horizonte', 'modelo'])

    graficas.historia(brent, **cfg['particion'], picos=PICOS,
                      titulo='Precio diario del Brent, tramos del estudio y grandes picos y caídas',
                      ruta=FIGURAS / 'historia.png')
    graficas.esquema_walk_forward(brent.index[0], brent.index[-1], cfg['walk_forward'], PARADA,
                                  'Validación walk-forward: tres pliegues y el modelo final',
                                  FIGURAS / 'walk_forward.png')
    graficas.validacion_vs_test(comp, 'Lo elegido en validación no se sostiene en test',
                                FIGURAS / 'validacion_vs_test.png')
    elegidos = {f['horizonte']: (f['modelo'], *intervalos.loc[(f['horizonte'], f['modelo']), ['bajo', 'alto']],
                                 f['cobertura_test'])
                for _, f in comp[comp['elegido_app'] == True].iterrows()}  # noqa: E712
    graficas.test_elegido(pd.read_csv(RESULTADOS / 'test_predicciones.csv'), elegidos,
                          'Modelo de la app en test (2021–2026) con su rango del 80 %',
                          FIGURAS / 'test_elegido.png')
    print(f'Figuras en {FIGURAS}')


if __name__ == '__main__':
    main()
