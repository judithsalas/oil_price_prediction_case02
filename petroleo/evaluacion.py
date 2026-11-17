# =============================================================
#  Evaluación en test: ¿la red bate de verdad al ingenuo?
#
#  - Diebold-Mariano: ¿la diferencia de error con el ingenuo es real o ruido?
#  - Ridge: un modelo lineal sencillo como segunda referencia.
#  - Acierto de dirección: ¿acierta si el Brent sube o baja?
# =============================================================
import numpy as np
from scipy import stats
from sklearn.linear_model import Ridge

ALFAS = [0.1, 1, 10, 100, 1000, 10000]


def diebold_mariano(error_a, error_b, h):
    """Contraste de Diebold-Mariano (con la corrección de Harvey, Leybourne y
    Newbold) de H0: los dos modelos tienen el mismo error cuadrático.

    error_a, error_b: errores de cada modelo, en orden temporal.
    h: horizonte. Las previsiones a h días se solapan, así que la varianza
    se estima con las autocovarianzas hasta el retardo h-1, con pesos de
    Bartlett (Newey-West): con pesos iguales la varianza puede salir negativa
    a 252 días y el contraste vería diferencias que no existen.
    Devuelve (estadístico, p-valor bilateral). Estadístico < 0: a es mejor.
    """
    d = np.asarray(error_a, float) ** 2 - np.asarray(error_b, float) ** 2
    n, media = len(d), d.mean()
    c = d - media
    varianza = (c @ c + 2 * sum((1 - k / h) * (c[k:] @ c[:-k]) for k in range(1, h))) / n
    dm = media / np.sqrt(varianza / n)
    dm *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)      # corrección HLN
    return float(dm), float(2 * stats.t.sf(abs(dm), df=n - 1))


def ridge(partes):
    """Ridge sobre la ventana aplanada, con el mismo objetivo sin tendencia que
    las redes. Se ajusta con train + parada y alfa se elige en val.
    Devuelve (modelo, alfa)."""
    X = np.concatenate([partes['train'][0], partes['parada'][0]]).reshape(
        -1, partes['train'][0][0].size)
    y = np.concatenate([partes['train'][1], partes['parada'][1]])
    y = y - y.mean()
    Xv, yv = partes['val'][0].reshape(len(partes['val'][0]), -1), partes['val'][1]
    modelos = [Ridge(alpha=a, fit_intercept=False).fit(X, y) for a in ALFAS]
    errores = [np.mean((m.predict(Xv) - yv) ** 2) for m in modelos]
    mejor = int(np.argmin(errores))
    return modelos[mejor], ALFAS[mejor]


def acierto_direccion(pred, y):
    """Fracción de días en que la previsión acierta si el Brent sube o baja."""
    return float(np.mean(np.sign(pred) == np.sign(y)))
