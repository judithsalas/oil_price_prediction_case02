# Evaluación en test (2021 a hoy). Se ejecuta UNA vez, al final:
#     poetry run python scripts/evaluar.py
# Usa los modelos de models/final (scripts/entrenar.py --final): la predicción
# de cada red es la media de sus semillas. Compara con el ingenuo y con Ridge.
# Guarda docs/resultados/test*.csv y docs/figuras/test_*.png.
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

from petroleo import graficas
from petroleo.datos import RUTA_CSV
from petroleo.entrenamiento import predecir
from petroleo.evaluacion import acierto_direccion, diebold_mariano, ridge
from petroleo.modelos import TIPOS, Recurrente
from petroleo.preproceso import preparar, quitar_outliers, seleccionar

RAIZ = Path(__file__).resolve().parent.parent
MODELOS = RAIZ / 'models' / 'final'
RESULTADOS = RAIZ / 'docs' / 'resultados'
FIGURAS = RAIZ / 'docs' / 'figuras'


def prediccion_red(ruta, X):
    """Media de las predicciones de las semillas guardadas en `ruta`."""
    guardado = torch.load(ruta, weights_only=False)     # fichero propio: incluye el escalador
    red = {k: v for k, v in guardado['hp'].items() if k != 'lr'}
    preds = []
    for pesos in guardado['pesos']:
        modelo = Recurrente(guardado['red'], X.shape[2], **red)
        modelo.load_state_dict(pesos)
        preds.append(predecir(modelo, X))
    return np.mean(preds, axis=0)


def evaluar_horizonte(datos, cfg, nombre_h, h):
    partes, _ = preparar(datos, cfg['ventana'], h, **cfg['particion'])
    X, y, dias = partes['test']
    modelo_ridge, alfa = ridge(partes)
    preds = {'ingenuo': np.zeros_like(y), 'ridge': modelo_ridge.predict(X.reshape(len(X), -1))}
    for tipo in TIPOS:
        preds[tipo] = prediccion_red(MODELOS / f'{tipo}_{nombre_h}.pt', X)

    # Precio de hoy y precio real a h días, para el error en dólares
    brent = seleccionar(quitar_outliers(datos))['brent']
    pos = brent.index.get_indexer(dias)
    hoy, real = brent.to_numpy()[pos], brent.to_numpy()[pos + h]
    assert np.allclose(np.log(real / hoy), y, atol=1e-5), 'precios y objetivo no cuadran'
    sube_train = np.mean(partes['train'][1] > 0) >= 0.5      # dirección más frecuente en train

    filas, por_anio = [], []
    for modelo, pred in preds.items():
        error, error_ingenuo = pred - y, y
        dm, p = diebold_mariano(error, error_ingenuo, h) if modelo != 'ingenuo' else (np.nan, np.nan)
        filas.append({
            'horizonte': nombre_h, 'modelo': modelo, 'muestras': len(y),
            'mse': float(np.mean(error ** 2)),
            'mejora_%': (1 - np.mean(error ** 2) / np.mean(y ** 2)) * 100,
            'dm': dm, 'p_valor': p,
            'mae_dolares': float(np.mean(np.abs(hoy * np.exp(pred) - real))),
            # el ingenuo no da dirección: se compara con "siempre la más frecuente en train"
            'acierto_direccion': (acierto_direccion(pred, y) if modelo != 'ingenuo'
                                  else float(np.mean((y > 0) == sube_train))),
            'alfa_ridge': alfa if modelo == 'ridge' else np.nan,
        })
        anio = pd.Series(error ** 2, index=dias.year).groupby(level=0).mean()
        ingenuo_anio = pd.Series(y ** 2, index=dias.year).groupby(level=0).mean()
        por_anio += [{'horizonte': nombre_h, 'modelo': modelo, 'anio': a, 'ratio': r}
                     for a, r in (anio / ingenuo_anio).items()]
    serie = pd.DataFrame({'horizonte': nombre_h, 'dia': dias, 'fecha_objetivo': brent.index[pos + h],
                          'precio_hoy': hoy, 'precio_real': real,
                          **{f'precio_{m}': hoy * np.exp(p) for m, p in preds.items()}})
    return filas, por_anio, serie


def main():
    cfg = yaml.safe_load((RAIZ / 'configs' / 'experimento.yaml').read_text())
    datos = pd.read_csv(RUTA_CSV, index_col=0, parse_dates=True)
    filas, por_anio, series = [], [], []
    for nombre_h, h in cfg['horizontes'].items():
        f, a, s = evaluar_horizonte(datos, cfg, nombre_h, h)
        filas += f
        por_anio += a
        series.append(s)

    tabla, por_anio, series = pd.DataFrame(filas), pd.DataFrame(por_anio), pd.concat(series)
    tabla.to_csv(RESULTADOS / 'test.csv', index=False)
    por_anio.to_csv(RESULTADOS / 'test_por_anio.csv', index=False)
    series.to_csv(RESULTADOS / 'test_predicciones.csv', index=False)
    graficas.test_por_anio(por_anio, 'Error en test frente al ingenuo, por año',
                           FIGURAS / 'test_por_anio.png')
    graficas.test_series(series, 'Precio real del Brent y previsiones en test',
                         FIGURAS / 'test_series.png')
    pd.set_option('display.width', 200)
    print(tabla.drop(columns='muestras').round(4).to_string(index=False))


if __name__ == '__main__':
    main()
