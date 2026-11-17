# Entrena RNN, LSTM y GRU para cada horizonte con walk-forward + rejilla.
#
# Paso 1, una vez por semilla (cada una se ejecuta aparte):
#     poetry run python scripts/entrenar.py --semilla 0
#   Entrena toda la rejilla en los pliegues walk-forward con esa semilla.
#   Cada red para con el final de train ('parada') y se evalúa en val.
#   Guarda en docs/resultados/ rejilla_s<N>.csv, historial_rejilla_s<N>.csv y
#   predicciones_val_s<N>.csv.gz, y las gráficas de esa semilla.
#
# Paso 2, cuando estén todas las semillas del YAML:
#     poetry run python scripts/entrenar.py --final
#   Elige para cada red y horizonte la combinación cuya predicción media de
#   las semillas tiene menor error en val (media de los pliegues), la
#   reentrena con cada semilla en la
#   partición final y guarda models/final/<red>_<horizonte>.pt (una red por
#   semilla; la app usará la media de sus predicciones).
import argparse
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

from petroleo import graficas
from petroleo.datos import RUTA_CSV
from petroleo.entrenamiento import entrenar, predecir
from petroleo.modelos import TIPOS, Recurrente, n_parametros
from petroleo.preproceso import preparar

RAIZ = Path(__file__).resolve().parent.parent
MODELOS = RAIZ / 'models' / 'final'
RESULTADOS = RAIZ / 'docs' / 'resultados'
FIGURAS = RAIZ / 'docs' / 'figuras'


def ingenuo(y):
    return float((y ** 2).mean())            # error de predecir y = 0


def ajustar(cfg, tipo, hp, partes, semilla):
    """Entrena una red: para con 'parada' y se evalúa en 'val'.

    Devuelve (modelo, fila de resultados, filas de historial, predicción en val).
    """
    torch.manual_seed(semilla)
    red = {k: v for k, v in hp.items() if k != 'lr'}
    modelo = Recurrente(tipo, partes['train'][0].shape[2], **red)
    r = entrenar(modelo, partes['train'], partes['parada'], lr=hp['lr'], **cfg['entrenamiento'])
    hist = r.pop('historial')
    pred = predecir(modelo, partes['val'][0])
    fila = {'red': tipo, **hp, 'semilla': semilla, 'mse_parada': r.pop('mse_val'), **r,
            'mse_val': float(np.mean((pred - partes['val'][1]) ** 2)),
            **{f'ingenuo_{k}': ingenuo(partes[k][1]) for k in ('train', 'parada', 'val')}}
    # Diferencia train-validación en la mejor época (errores relativos al ingenuo)
    fila['brecha'] = (fila['mse_parada'] / fila['ingenuo_parada']
                      - fila['mse_train'] / fila['ingenuo_train'])
    historial = [{**fila, 'epoca': e + 1, 'mse_train': a, 'mse_parada': b}
                 for e, (a, b) in enumerate(zip(hist['mse_train'], hist['mse_val']))]
    return modelo, fila, historial, pred


def mejora(tabla, claves):
    """Mejora (%) frente al ingenuo, con los errores medios de los pliegues."""
    g = tabla.groupby(claves, sort=False)[['mse_val', 'ingenuo_val']].mean()
    return ((1 - g['mse_val'] / g['ingenuo_val']) * 100).rename('mejora').reset_index()


def combinacion(t):
    return t['oculto'].astype(str) + '×' + t['capas'].astype(str) + ' · ' + t['lr'].map('{:g}'.format)


def media_semillas(pred, hp_cols):
    """Error de la predicción media de las semillas (lo que usará la app),
    por combinación: media de los pliegues de val. Columnas mse_val, ingenuo_val.

    pred: filas de predicciones_val_s<N>.csv.gz de todas las semillas."""
    claves = ['horizonte', 'red', *hp_cols, 'pliegue']
    media = pred.groupby([*claves, 'dia'], sort=False)[['y', 'pred']].mean()
    errores = pd.DataFrame({'mse_val': (media['pred'] - media['y']) ** 2,
                            'ingenuo_val': media['y'] ** 2})
    return errores.groupby(claves, sort=False).mean().groupby(claves[:-1], sort=False).mean()


def una_semilla(cfg, datos, semilla):
    rejilla = [dict(zip(cfg['rejilla'], v)) for v in product(*cfg['rejilla'].values())]
    filas, historial, predicciones = [], [], []
    for nombre_h, h in cfg['horizontes'].items():
        pliegues = [preparar(datos, cfg['ventana'], h, **p)[0] for p in cfg['walk_forward']]
        for tipo, hp in product(TIPOS, rejilla):
            for i, partes in enumerate(pliegues):
                _, fila, hist, pred = ajustar(cfg, tipo, hp, partes, semilla)
                extra = {'horizonte': nombre_h, 'pliegue': i}
                filas.append({**extra, **fila})
                historial += [{**extra, **f} for f in hist]
                _, y, dias = partes['val']
                predicciones.append(pd.DataFrame({**extra, 'red': tipo, **hp, 'semilla': semilla,
                                                  'dia': dias, 'y': y, 'pred': pred}))
                print(f"{nombre_h:5} {tipo:4} {hp['oculto']:3}x{hp['capas']} lr {hp['lr']:g} "
                      f"pliegue {i + 1}: error/ingenuo {fila['mse_val'] / fila['ingenuo_val']:.3f}  "
                      f"mejor época {fila['mejor_epoca']}/{fila['epocas']} "
                      f"{fila['segundos']:.0f}s", flush=True)

    tabla, historial = pd.DataFrame(filas), pd.DataFrame(historial)
    tabla.to_csv(RESULTADOS / f'rejilla_s{semilla}.csv', index=False)
    historial.to_csv(RESULTADOS / f'historial_rejilla_s{semilla}.csv', index=False)
    pd.concat(predicciones).to_csv(RESULTADOS / f'predicciones_val_s{semilla}.csv.gz', index=False)

    hp_cols = list(cfg['rejilla'])
    por_combinacion = mejora(tabla, ['horizonte', 'red', *hp_cols])
    por_combinacion['combinacion'] = combinacion(por_combinacion)
    graficas.rejilla(por_combinacion, f'Rejilla, semilla {semilla} (media de los 3 pliegues)',
                     FIGURAS / f'rejilla_s{semilla}.png')

    # Curvas de la mejor combinación de cada red con esta semilla
    mejores = por_combinacion.loc[por_combinacion.groupby(['horizonte', 'red'], sort=False)
                                  ['mejora'].idxmax(), ['horizonte', 'red', *hp_cols]]
    graficas.curvas(historial.merge(mejores), 'pliegue',
                    f'Curvas de aprendizaje, semilla {semilla} (mejor combinación de cada red)',
                    FIGURAS / f'curvas_rejilla_s{semilla}.png')
    print('\nMejor combinación de cada red con esta semilla:')
    print(por_combinacion.loc[mejores.index].drop(columns='combinacion')
          .round({'mejora': 1}).to_string(index=False))


def final(cfg, datos):
    faltan = [s for s in cfg['semillas'] if not (RESULTADOS / f'rejilla_s{s}.csv').exists()]
    if faltan:
        raise SystemExit(f'Faltan semillas: ejecuta antes --semilla {faltan[0]}')
    tabla = pd.concat([pd.read_csv(RESULTADOS / f'rejilla_s{s}.csv') for s in cfg['semillas']])
    hp_cols = list(cfg['rejilla'])
    # Se elige por el error de la predicción media de las semillas, no por la media
    # de sus errores: es la predicción que dará la app.
    pred = pd.concat(pd.read_csv(RESULTADOS / f'predicciones_val_s{s}.csv.gz')
                     for s in cfg['semillas'])
    conjunto = media_semillas(pred, hp_cols)
    medias = conjunto['mse_val']

    filas, historial, elegidas = [], [], []
    for nombre_h, h in cfg['horizontes'].items():
        partes, escalador = preparar(datos, cfg['ventana'], h, **cfg['particion'])
        for tipo in TIPOS:
            # idxmin da tipos de numpy: se vuelven al tipo del YAML (int / float)
            hp = {k: type(cfg['rejilla'][k][0])(v)
                  for k, v in zip(hp_cols, medias.loc[(nombre_h, tipo)].idxmin())}
            elegidas.append({'horizonte': nombre_h, 'red': tipo, **hp})
            pesos = []
            for semilla in cfg['semillas']:
                modelo, fila, hist, _ = ajustar(cfg, tipo, hp, partes, semilla)
                pesos.append(modelo.state_dict())
                filas.append({'horizonte': nombre_h, **fila})
                historial += [{'horizonte': nombre_h, **f} for f in hist]
            torch.save({'red': tipo, 'hp': hp, 'semillas': cfg['semillas'], 'pesos': pesos,
                        'escalador': escalador, 'ventana': cfg['ventana'], 'horizonte': h,
                        'n_parametros': n_parametros(modelo)},
                       MODELOS / f'{tipo}_{nombre_h}.pt')
            print(f'-> guardado {tipo}_{nombre_h}.pt {hp}', flush=True)

    pd.DataFrame(filas).to_csv(RESULTADOS / 'entrenamiento_final.csv', index=False)
    historial = pd.DataFrame(historial)
    historial.to_csv(RESULTADOS / 'historial_final.csv', index=False)
    graficas.curvas(historial, 'semilla',
                    'Curvas de aprendizaje de los modelos finales (train 2000-2017, val 2018-2020)',
                    FIGURAS / 'curvas_finales.png')

    # ¿La mejora es real o ruido? Arquitectura elegida, cada semilla por separado
    por_semilla = mejora(tabla.merge(pd.DataFrame(elegidas)), ['horizonte', 'red', 'semilla'])
    por_semilla.to_csv(RESULTADOS / 'mejora_semillas.csv', index=False)
    graficas.mejora_semillas(por_semilla, 'Mejora frente al ingenuo en validación walk-forward',
                             FIGURAS / 'mejora_semillas.png')
    resumen = por_semilla.groupby(['horizonte', 'red'], sort=False)['mejora'].agg(
        media='mean', desviacion='std', peor='min', mejor='max',
        semillas_que_mejoran=lambda m: f'{(m > 0).sum()}/{len(m)}')
    elegido = pd.DataFrame(elegidas).set_index(['horizonte', 'red', *hp_cols])
    resumen['media_semillas'] = (1 - conjunto['mse_val'] / conjunto['ingenuo_val']).loc[
        elegido.index].droplevel(hp_cols) * 100
    resumen['brecha'] = tabla.merge(pd.DataFrame(elegidas)).groupby(
        ['horizonte', 'red'], sort=False)['brecha'].mean()
    print('\nMejora frente al ingenuo (%), arquitectura elegida '
          '(media_semillas = predicción media de las semillas):')
    print(resumen.round(2).to_string())


def main():
    args = argparse.ArgumentParser(description=__doc__)
    modo = args.add_mutually_exclusive_group(required=True)
    modo.add_argument('--semilla', type=int, help='entrena la rejilla con esta semilla')
    modo.add_argument('--final', action='store_true', help='elige y guarda los modelos finales')
    args.add_argument('--config', default=RAIZ / 'configs' / 'experimento.yaml', type=Path)
    args = args.parse_args()

    cfg = yaml.safe_load(args.config.read_text())
    datos = pd.read_csv(RUTA_CSV, index_col=0, parse_dates=True)
    for d in (MODELOS, RESULTADOS, FIGURAS):
        d.mkdir(parents=True, exist_ok=True)

    if args.final:
        final(cfg, datos)
    else:
        una_semilla(cfg, datos, args.semilla)


if __name__ == '__main__':
    main()
