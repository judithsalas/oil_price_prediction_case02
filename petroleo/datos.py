# =============================================================
#  Descarga de datos - Caso de uso: precio del petróleo (Brent)
#  Periodo: desde el 1 de enero de 2000 hasta hoy
#
#  Todos los datos son DIARIOS (días hábiles)
#  Fuente general: portal FRED (EIA, BCE, Fed, Cboe), gratis y sin clave
#  Complementaria: Yahoo Finance (futuros y mercados mundiales)
# =============================================================
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError

import pandas as pd

INICIO = '2000-01-01'
RUTA_CSV = Path(__file__).resolve().parent.parent / 'data' / 'petroleo_dataset.csv'

# ---------------------------------------------------------------
# 1) FRED: series diarias (sin clave)
# ---------------------------------------------------------------
SERIES_FRED = {
    'DCOILBRENTEU': 'brent',        # EIA, Brent spot  -> VARIABLE OBJETIVO
    'DCOILWTICO':   'wti',          # EIA, WTI spot
    'DHHNGSP':      'gas_natural',  # EIA, Henry Hub
    'ECBDFR':       'tipo_bce',     # BCE, facilidad de depósito
    'DEXUSEU':      'usd_por_eur',  # dólares por euro
    'DEXCHUS':      'cny_por_usd',  # yuanes por dólar (China)
    'VIXCLS':       'vix',          # volatilidad de los mercados
}


def descargar_fred(serie, fin):
    url = (f'https://fred.stlouisfed.org/graph/fredgraph.csv'
           f'?id={serie}&cosd={INICIO}&coed={fin}')
    # FRED devuelve a ratos un error pasajero del servidor (502): se reintenta antes de rendirse
    for espera in (5, 15, 30, None):
        try:
            s = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.').iloc[:, 0]
            return s.rename(SERIES_FRED[serie])
        except HTTPError as e:
            if espera is None or e.code < 500:      # un 404 (serie mal escrita) no se arregla esperando
                raise
            print(f'  FRED respondió {e.code} con {serie}; reintento en {espera} s')
            time.sleep(espera)


# ---------------------------------------------------------------
# 2) Yahoo Finance: futuros y mercados mundiales (datos diarios)
#    Nota: BZ=F (Brent) solo tiene datos desde ~2007; el resto desde ~2000
# ---------------------------------------------------------------
OTROS_YAHOO = {'HG=F': 'cobre', 'GC=F': 'oro', 'DX-Y.NYB': 'indice_dolar'}


def descargar_ohlcv(ticker, prefijo, fin):
    import yfinance as yf
    df = yf.download(ticker, start=INICIO, end=fin,
                     auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):   # versiones recientes de yfinance
        df.columns = df.columns.get_level_values(0)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    return df.add_prefix(f'{prefijo}_')


def descargar_cierres(tickers, fin):
    import yfinance as yf
    df = yf.download(list(tickers), start=INICIO, end=fin,
                     auto_adjust=False, progress=False)['Close']
    return df.rename(columns=tickers)


# ---------------------------------------------------------------
# 3) Limpieza: alinear con el calendario del Brent
# ---------------------------------------------------------------
def limpiar(datos):
    # Festivos distintos en cada mercado -> se propaga el último valor,
    # pero solo se guardan los días con Brent real (calendario del Brent).
    # Se marca antes del ffill para no inventar precios del objetivo.
    datos = datos.sort_index()
    hay_brent = datos['brent'].notna()
    datos = datos.ffill()[hay_brent]
    datos = datos[datos.index.dayofweek < 5]      # días laborables
    datos = datos.loc[INICIO:]
    datos.index.name = 'Date'
    return datos


def descargar():
    """Descarga FRED + Yahoo hasta hoy y devuelve el DataFrame limpio."""
    fin = datetime.now().strftime('%Y-%m-%d')

    print('Descargando FRED...')
    datos = pd.concat([descargar_fred(s, fin) for s in SERIES_FRED], axis=1)

    print('Descargando Yahoo Finance...')
    yahoo = (descargar_ohlcv('BZ=F', 'brent_fut', fin)
             .join(descargar_ohlcv('CL=F', 'wti_fut', fin), how='outer')
             .join(descargar_cierres(OTROS_YAHOO, fin), how='outer'))
    datos = datos.join(yahoo, how='outer')

    comprobar_columnas(datos)
    return limpiar(datos)


def comprobar_columnas(datos):
    # yfinance no siempre lanza error: si un ticker falla devuelve la columna
    # vacía. Se para aquí para no sobrescribir el CSV con columnas sin datos
    # (el modelo se entrena con todas las columnas).
    vacias = [c for c in datos.columns if datos[c].isna().all()]
    if vacias:
        raise RuntimeError(f'Descarga incompleta, columnas sin datos: {vacias}')


def guardar(datos, ruta=RUTA_CSV):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos.to_csv(ruta)
