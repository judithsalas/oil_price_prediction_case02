# Lógica de la app: previsión de hoy, histórico, comparativa, descarga de datos y
# reentrenamiento. El servidor (app/servidor.py) solo la expone.
#
# El modelo de cada horizonte es el elegido en validación (comparativa.csv,
# columna elegido_app). Si se ha reentrenado desde la app, se usan sus pesos de
# models/app/; si no, los del estudio (models/final/).
import json
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import yaml

from petroleo.datos import RUTA_CSV, descargar, guardar
from petroleo.entrenamiento import entrenar
from petroleo.modelos import Recurrente
from petroleo.preproceso import preparar, seleccionar, ultima_ventana
from scripts.evaluar import MODELOS, RAIZ, RESULTADOS, prediccion_red

REENTRENADOS = RAIZ / 'models' / 'app'
NOMBRES = {'corto': '1 semana', 'medio': '3 meses', 'largo': '1 año'}


def configuracion():
    return yaml.safe_load((RAIZ / 'configs' / 'experimento.yaml').read_text())


# La app guarda sus descargas aparte para no tocar el dataset del estudio
RUTA_APP = RUTA_CSV.with_name('app_dataset.csv')


def leer_datos():
    ruta = next((r for r in (RUTA_APP, RUTA_CSV) if r.exists()), None)
    if ruta is None:                    # en Hugging Face el repositorio no trae datos
        actualizar_datos()
        ruta = RUTA_APP
    return pd.read_csv(ruta, index_col=0, parse_dates=True)


def actualizar_datos():
    """Descarga y guarda solo si trae las columnas que esperan los modelos: un fallo
    de Yahoo no debe sustituir a los datos buenos."""
    nuevos = descargar()
    escalador = torch.load(next(MODELOS.glob('*.pt')), weights_only=False)['escalador']
    faltan = set(escalador.feature_names_in_) - set(seleccionar(nuevos).columns)
    if faltan:
        raise ValueError(f'la descarga no trae {", ".join(sorted(faltan))}; se mantienen los datos anteriores')
    guardar(nuevos, RUTA_APP)


def comparativa():
    return pd.read_csv(RESULTADOS / 'comparativa.csv')


def elegidos():
    """{horizonte: fila de comparativa.csv del modelo de la app}"""
    tabla = comparativa()
    return {f['horizonte']: f for _, f in tabla[tabla['elegido_app'] == True].iterrows()}  # noqa: E712


def ruta_modelo(nombre_h, red):
    propia = REENTRENADOS / f'{red}_{nombre_h}.pt'
    return propia if propia.exists() else MODELOS / f'{red}_{nombre_h}.pt'


def fiabilidad(fila):
    """Etiqueta según el test: solo 'aporta valor' si bate al ingenuo con p < 0,05."""
    if fila['mejora_test_%'] > 0 and fila['p_valor'] < 0.05:
        return 'bien', 'Aporta valor frente al precio de hoy'
    if fila['mejora_test_%'] > -5:
        return 'aviso', 'Orientativa: empata con el precio de hoy'
    return 'mal', 'No mejora al precio de hoy'


def prevision(datos):
    intervalos = pd.read_csv(RESULTADOS / 'intervalos.csv').set_index(['horizonte', 'modelo'])
    cfg = configuracion()
    salida = []
    for nombre_h, fila in elegidos().items():
        red, h = fila['modelo'], cfg['horizontes'][nombre_h]
        ruta = ruta_modelo(nombre_h, red)
        guardado = torch.load(ruta, weights_only=False)     # fichero propio
        X, dia, precio = ultima_ventana(datos, guardado['escalador'], guardado['ventana'])
        pred = float(prediccion_red(ruta, X)[0])
        bajo, alto = intervalos.loc[(nombre_h, red), ['bajo', 'alto']]
        nivel, etiqueta = fiabilidad(fila)
        salida.append({
            'horizonte': nombre_h, 'nombre': NOMBRES[nombre_h], 'dias': h, 'red': red.upper(),
            'fecha_hoy': dia.date().isoformat(), 'precio_hoy': precio,
            'fecha_objetivo': (dia + pd.offsets.BDay(h)).date().isoformat(),
            'previsto': precio * np.exp(pred), 'variacion': np.expm1(pred) * 100,
            'bajo': precio * np.exp(pred + bajo), 'alto': precio * np.exp(pred + alto),
            'fiabilidad': nivel, 'etiqueta': etiqueta,
            'mejora_test': fila['mejora_test_%'], 'mejora_val': fila['mejora_val'],
            'cobertura_test': fila['cobertura_test'],
            'entrenado': guardado.get('entrenado', 'estudio (datos 2000-2017)'),
        })
    return salida


def historico(datos):
    """Brent semanal desde 2000 y diario del último año (para no mandar 7.000 puntos)."""
    brent = datos['brent'].dropna()
    semanal = brent.resample('W-FRI').last().dropna()
    diario = brent[brent.index > brent.index[-1] - pd.DateOffset(years=1)]

    def puntos(s):
        return [[d.date().isoformat(), round(float(v), 2)] for d, v in s.items()]
    return {'semanal': puntos(semanal), 'diario': puntos(diario)}


def evaluacion_test():
    """Cómo le fue en test (2021-2026) al modelo de la app de cada horizonte, con
    los modelos del estudio: precio real, previsión, ingenuo y rango del 80 %
    (uno de cada 3 días), y por año de origen el error frente al ingenuo y la
    cobertura del rango. Sale de resultados ya guardados: no evalúa nada."""
    pred = pd.read_csv(RESULTADOS / 'test_predicciones.csv', parse_dates=['dia', 'fecha_objetivo'])
    por_anio = pd.read_csv(RESULTADOS / 'test_por_anio.csv')
    intervalos = pd.read_csv(RESULTADOS / 'intervalos.csv').set_index(['horizonte', 'modelo'])
    salida = {}
    for nombre_h, fila in elegidos().items():
        red = fila['modelo']
        p = pred[pred['horizonte'] == nombre_h].sort_values('fecha_objetivo')
        bajo, alto = intervalos.loc[(nombre_h, red), ['bajo', 'alto']]
        prev = p[f'precio_{red}']
        dentro = np.log(p['precio_real'] / prev).between(bajo, alto)
        cobertura = dentro.groupby(p['dia'].dt.year).mean()
        ratio = por_anio[(por_anio['horizonte'] == nombre_h) & (por_anio['modelo'] == red)]
        serie = p.assign(bajo=prev * np.exp(bajo), alto=prev * np.exp(alto)).iloc[::3]
        salida[nombre_h] = {
            'red': red.upper(),
            'serie': [[f.date().isoformat(), *(round(float(v), 2) for v in vals)] for f, *vals in zip(
                serie['fecha_objetivo'], serie['precio_real'], serie[f'precio_{red}'],
                serie['precio_ingenuo'], serie['bajo'], serie['alto'])],
            'por_anio': [{'anio': int(a), 'error_vs_ingenuo': round(float(r), 3),
                          'cobertura': round(float(cobertura.get(a, np.nan)), 3)}
                         for a, r in zip(ratio['anio'], ratio['ratio'])],
        }
    return salida


def resumen():
    datos, cfg = leer_datos(), configuracion()
    return {'prevision': prevision(datos), 'historico': historico(datos),
            'comparativa': json.loads(comparativa().to_json(orient='records')),
            'test': evaluacion_test(),
            'validacion': {'walk_forward': cfg['walk_forward'], 'particion': cfg['particion'],
                           'inicio': datos.index[0].date().isoformat()}}


def reentrenar(avisar=print):
    """Reentrena el modelo elegido de cada horizonte con todos los datos hasta hoy
    (misma combinación y semillas; el final de train sirve para la parada temprana).
    El intervalo sigue siendo el del estudio."""
    cfg, datos = configuracion(), leer_datos()
    fin = datos.index[-1]
    REENTRENADOS.mkdir(parents=True, exist_ok=True)
    for nombre_h, fila in elegidos().items():
        red, h = fila['modelo'], cfg['horizontes'][nombre_h]
        estudio = torch.load(MODELOS / f'{red}_{nombre_h}.pt', weights_only=False)
        partes, escalador = preparar(datos, cfg['ventana'], h, fin, fin)
        hp = {k: v for k, v in estudio['hp'].items() if k != 'lr'}
        pesos = []
        for semilla in cfg['semillas']:
            avisar(f'Entrenando {red.upper()} a {NOMBRES[nombre_h]}, semilla {semilla + 1} de '
                   f'{len(cfg["semillas"])}')
            torch.manual_seed(semilla)
            modelo = Recurrente(red, partes['train'][0].shape[2], **hp)
            entrenar(modelo, partes['train'], partes['parada'], lr=estudio['hp']['lr'],
                     **cfg['entrenamiento'])
            pesos.append(modelo.state_dict())
        torch.save({**estudio, 'pesos': pesos, 'escalador': escalador,
                    'entrenado': f'{datetime.now():%d/%m/%Y} (datos hasta {fin:%d/%m/%Y})'},
                   REENTRENADOS / f'{red}_{nombre_h}.pt')
