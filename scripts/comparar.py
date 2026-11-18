# Tabla comparativa de las tres redes (punto 5 del enunciado) e intervalos del 80 %.
#     poetry run python scripts/comparar.py
# No vuelve a evaluar en test: lee las previsiones ya guardadas por
# scripts/evaluar.py. Los intervalos salen de los errores fuera de muestra de la
# validación walk-forward (2012-2020; necesita predicciones_val_s<N>.csv.gz).
# Mide también la cobertura del intervalo en test (sin cambiar nada después).
# Guarda docs/resultados/comparativa.csv e intervalos.csv.
import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.metrics import r2_score

from petroleo.modelos import TIPOS
from scripts.entrenar import media_semillas
from scripts.evaluar import MODELOS, RAIZ, RESULTADOS

NIVEL = 0.8


def intervalo(error, nivel=NIVEL):
    """Percentiles del error (real − previsto) que dejan fuera (1 − nivel) / 2 por cada lado."""
    return np.quantile(error, [(1 - nivel) / 2, (1 + nivel) / 2])


def intervalos(cfg, pred):
    """Intervalo de cada red (y del ingenuo) en log-rentabilidad, desde sus errores
    fuera de muestra en los 3 pliegues walk-forward (2012-2020): la combinación
    elegida, con la predicción media de las semillas, como en la app."""
    filas = []
    for nombre_h in cfg['horizontes']:
        for tipo in TIPOS:
            hp = torch.load(MODELOS / f'{tipo}_{nombre_h}.pt', weights_only=False)['hp']
            elegida = pred[(pred['horizonte'] == nombre_h) & (pred['red'] == tipo)
                           & np.logical_and.reduce([pred[k] == v for k, v in hp.items()])]
            media = elegida.groupby(['pliegue', 'dia'])[['y', 'pred']].mean()
            errores = {tipo: media['y'] - media['pred'], 'ingenuo': media['y']}
            for modelo, error in errores.items():
                if modelo == 'ingenuo' and tipo != list(TIPOS)[0]:
                    continue        # el ingenuo es el mismo para las tres redes
                bajo, alto = intervalo(error)
                filas.append({'horizonte': nombre_h, 'modelo': modelo, 'bajo': bajo,
                              'alto': alto, 'muestras': len(error)})
    return pd.DataFrame(filas)


def errores_en_dolares(real, previsto):
    """Las cuatro métricas clásicas sobre el precio: MAE, MSE, RMSE y R².
    R² = 1 es acertar siempre y R² = 0, hacerlo igual que prever siempre la media del
    periodo; por debajo de 0, peor que esa media."""
    error = previsto - real
    mse = (error ** 2).mean()
    return {'mae_$': error.abs().mean(), 'mse_$2': mse, 'rmse_$': np.sqrt(mse), 'r2': r2_score(real, previsto)}


def comparativa(rangos, pred, hp_cols):
    test = pd.read_csv(RESULTADOS / 'test.csv')
    precios = pd.read_csv(RESULTADOS / 'test_predicciones.csv')
    filas = []
    for (nombre_h, modelo), _ in test.groupby(['horizonte', 'modelo'], sort=False):
        p = precios[precios['horizonte'] == nombre_h]
        fila = {'horizonte': nombre_h, 'modelo': modelo,
                **errores_en_dolares(p['precio_real'], p[f'precio_{modelo}'])}
        rango = rangos[(rangos['horizonte'] == nombre_h) & (rangos['modelo'] == modelo)]
        if len(rango):
            # ¿El precio real cae dentro del intervalo? log(real / previsto) entre bajo y alto
            fuera = np.log(p['precio_real'] / p[f'precio_{modelo}'])
            fila['cobertura_test'] = fuera.between(rango['bajo'].iloc[0], rango['alto'].iloc[0]).mean()
        filas.append(fila)
    tabla = test[['horizonte', 'modelo', 'mejora_%', 'p_valor', 'acierto_direccion']].merge(
        pd.DataFrame(filas)).rename(columns={'mejora_%': 'mejora_test_%'})

    # Estabilidad: cuánto varía la mejora entre semillas y en cuántas bate al ingenuo
    semillas = pd.read_csv(RESULTADOS / 'mejora_semillas.csv').groupby(
        ['horizonte', 'red'], sort=False)['mejora'].agg(
        mejora_val_desv='std', semillas_mejoran=lambda m: f'{(m > 0).sum()}/{len(m)}')
    # Coste: parámetros y tiempo de entrenamiento final (media por semilla)
    final = pd.read_csv(RESULTADOS / 'entrenamiento_final.csv').groupby(
        ['horizonte', 'red'], sort=False)[['segundos', 'epocas']].mean()
    guardados = [torch.load(MODELOS / f'{r}_{h}.pt', weights_only=False) for h, r in final.index]
    final['parametros'] = [g['n_parametros'] for g in guardados]
    # Validación walk-forward de la predicción media de las semillas: la cifra con
    # la que se eligió cada combinación (la misma de decisiones.md)
    conjunto = media_semillas(pred, hp_cols)
    elegidas = conjunto.loc[[(h, r, *(g['hp'][k] for k in hp_cols))
                             for (h, r), g in zip(final.index, guardados)]]
    final.insert(0, 'mejora_val', (1 - elegidas['mse_val'] / elegidas['ingenuo_val']).to_numpy() * 100)
    redes = semillas.join(final).reset_index().rename(columns={'red': 'modelo'})
    # Modelo de la app: la red con mayor mejora en validación en cada horizonte (no se mira test)
    redes['elegido_app'] = redes.index.isin(redes.groupby('horizonte')['mejora_val'].idxmax())

    rangos = rangos.assign(intervalo_80=lambda r: [
        f'{np.expm1(b) * 100:+.1f} % / {np.expm1(a) * 100:+.1f} %' for b, a in zip(r['bajo'], r['alto'])])
    return (tabla.merge(redes, how='left')
            .merge(rangos[['horizonte', 'modelo', 'intervalo_80']], how='left'))


def main():
    cfg = yaml.safe_load((RAIZ / 'configs' / 'experimento.yaml').read_text())
    pred = pd.concat(pd.read_csv(RESULTADOS / f'predicciones_val_s{s}.csv.gz')
                     for s in cfg['semillas'])
    rangos = intervalos(cfg, pred)
    rangos.to_csv(RESULTADOS / 'intervalos.csv', index=False)
    tabla = comparativa(rangos, pred, list(cfg['rejilla']))
    tabla.to_csv(RESULTADOS / 'comparativa.csv', index=False)
    pd.set_option('display.width', 250)
    print(tabla.round(2).to_string(index=False))


if __name__ == '__main__':
    main()
