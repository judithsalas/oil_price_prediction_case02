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


def preparar(datos, ventana, horizonte, fin_train, fin_val):
    """Devuelve {'train'|'val'|'test': (X, y, fechas)} y el escalador.

    X: (n, ventana, n_columnas) con los últimos `ventana` días hasta t.
    y: log(brent[t+h] / brent[t]).  fechas: el día t de cada muestra.
    Una muestra solo entra en su partición si también el día t+h cae dentro,
    así ningún objetivo de train o val mira datos de la partición siguiente.
    """
    datos = seleccionar(quitar_outliers(datos))
    fechas = datos.index
    fin_train, fin_val = pd.Timestamp(fin_train), pd.Timestamp(fin_val)

    # El escalador solo ve train (fin_train incluido).
    escalador = StandardScaler().fit(datos.loc[:fin_train])
    valores = escalador.transform(datos).astype(np.float32)

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
    partes = {k: (X[m], y[m], dia[m]) for k, m in mascaras.items()}
    return partes, escalador
