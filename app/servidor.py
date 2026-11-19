# Servidor de la app: sirve la página (app/static) y la API.
#     poetry run uvicorn app.servidor:app --port 7860
# Descargar datos y reentrenar tardan minutos: se hacen en segundo plano, de una
# en una, y la página consulta /api/estado hasta que terminan.
import threading
import traceback
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app import prevision
from scripts.descargar_modelos import descargar as descargar_modelos

descargar_modelos()     # los modelos no están en git: la primera vez se bajan de Hugging Face
app = FastAPI(title='Previsión del Brent')
estado = {'tarea': None, 'mensaje': '', 'error': None}
ocupado = threading.Lock()
cache = {}


def lanzar(nombre, trabajo):
    if not ocupado.acquire(blocking=False):
        raise HTTPException(409, f'Ya hay una tarea en marcha: {estado["tarea"]}')

    def correr():
        estado.update(tarea=nombre, mensaje='Empezando…', error=None)
        try:
            trabajo()
            estado['mensaje'] = 'Terminado'
        except Exception as e:      # se enseña en la página en vez de perderse en el log
            traceback.print_exc()
            estado['error'] = f'{type(e).__name__}: {e}'
        finally:
            cache.clear()
            estado['tarea'] = None
            ocupado.release()
    threading.Thread(target=correr, daemon=True).start()
    return {'ok': True}


def avisar(mensaje):
    estado['mensaje'] = mensaje


@app.get('/api/resumen')
def resumen():
    if 'resumen' not in cache:
        cache['resumen'] = prevision.resumen()
    return cache['resumen']


@app.get('/api/estado')
def ver_estado():
    return estado


@app.post('/api/actualizar')
def actualizar():
    return lanzar('descargar datos', lambda: (avisar('Descargando datos de FRED y Yahoo…'),
                                              prevision.actualizar_datos()))


@app.post('/api/reentrenar')
def reentrenar():
    return lanzar('reentrenar', lambda: prevision.reentrenar(avisar))


app.mount('/', StaticFiles(directory=Path(__file__).parent / 'static', html=True), name='pagina')
