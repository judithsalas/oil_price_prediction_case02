# =============================================================
#  Preprocesado: outliers, partición temporal, escalado y ventanas
#
#  Objetivo: log-rentabilidad del Brent a h días hábiles,
#      y = log(brent[t+h] / brent[t])
#  -> precio previsto = brent[t] * exp(y); el modelo ingenuo es y = 0.
# =============================================================
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Columnas de precio que nunca pueden ser <= 0 (el tipo del BCE sí puede).
PRECIOS = ['brent', 'wti', 'wti_fut_Open', 'wti_fut_High', 'wti_fut_Low', 'wti_fut_Close']


def quitar_outliers(datos):
    # WTI negativo del 20/04/2020: fallo puntual por el vencimiento del futuro,
    # no un precio real del crudo -> se trata como dato faltante.
    # Los máximos de 2008, 2022 y 2026 son reales y se mantienen.
    datos = datos.copy()
    cols = [c for c in PRECIOS if c in datos]
    datos[cols] = datos[cols].mask(datos[cols] <= 0).ffill()
    return datos


def seleccionar(datos):
    # Los futuros del Brent (BZ=F) empiezan en 2007: se quitan para no perder
    # 7 años; el Brent spot ya es el objetivo. Luego se quitan las primeras
    # filas incompletas (hasta ago-2000).
    datos = datos.drop(columns=[c for c in datos if c.startswith('brent_fut')])
    return datos.dropna()


# Variables que ya son estables en el tiempo: entran en nivel.
NIVELES = ['tipo_bce', 'vix']


def entradas(datos):
    # El resto pasa a log-rentabilidad diaria, log(x[t] / x[t-1]): un precio en
    # nivel de 2022 queda fuera del rango visto en train y satura tanh/sigmoide.
    # El volumen puede ser 0, por eso log(1 + x).
    x = datos.copy()
    for c in x:
        if c not in NIVELES:
            x[c] = (np.log1p(x[c]) if c.endswith('Volume') else np.log(x[c])).diff()
    return x.iloc[1:]       # la primera fila no tiene día anterior


PARADA = 0.15     # último 15 % de train: solo para la parada temprana
LIMITE = 5.0      # entradas estandarizadas recortadas a ±5 desviaciones


def preparar(datos, ventana, horizonte, fin_train, fin_val):
    """Devuelve {'train'|'parada'|'val'|'test': (X, y, fechas)} y el escalador.

    X: (n, ventana, n_columnas) con las entradas (ver `entradas`) de los
       últimos `ventana` días hasta t.
    y: log(brent[t+h] / brent[t]).  fechas: el día t de cada muestra.
    Una muestra solo entra en su partición si también el día t+h cae dentro,
    así ningún objetivo mira datos de la partición siguiente. 'parada' es el
    final de train y decide cuándo parar; 'val' queda limpia para elegir
    la combinación de hiperparámetros.
    """
    datos = seleccionar(quitar_outliers(datos))
    x = entradas(datos)
    datos = datos.loc[x.index]
    fechas = datos.index
    fin_train, fin_val = pd.Timestamp(fin_train), pd.Timestamp(fin_val)

    # El escalador solo ve train (fin_train incluido).
    escalador = StandardScaler().fit(x.loc[:fin_train])
    valores = np.clip(escalador.transform(x), -LIMITE, LIMITE).astype(np.float32)

    brent = datos['brent'].to_numpy()
    t = np.arange(ventana - 1, len(datos) - horizonte)   # último día de cada ventana
    y = np.log(brent[t + horizonte] / brent[t]).astype(np.float32)
    ventanas = np.lib.stride_tricks.sliding_window_view(valores, ventana, axis=0)
    X = ventanas[t - ventana + 1].transpose(0, 2, 1)     # (n, ventana, columnas)

    dia, objetivo = fechas[t], fechas[t + horizonte]
    mascaras = {
        'train': objetivo <= fin_train,
        'val':   (dia > fin_train) & (objetivo <= fin_val),
        'test':  dia > fin_val,
    }
    # La parada son las últimas muestras de train; de las de ajuste se quitan
    # las que tienen el objetivo ya dentro de la parada (purga de h días).
    inicio = dia[mascaras['train']][int((1 - PARADA) * mascaras['train'].sum())]
    mascaras['parada'] = mascaras['train'] & (dia >= inicio)
    mascaras['train'] = mascaras['train'] & (objetivo < inicio)
    partes = {k: (X[m], y[m], dia[m]) for k, m in mascaras.items()}
    return partes, escalador
