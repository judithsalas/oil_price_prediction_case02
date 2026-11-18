---
language: es
library_name: pytorch
pipeline_tag: time-series-forecasting
tags:
  - rnn
  - lstm
  - gru
  - brent
  - oil-price
---

# Previsión del precio del Brent: RNN, LSTM y GRU

Modelos del Caso de uso III de Aprendizaje automático. Predicen el precio del Brent a
1 semana (5 días hábiles), 3 meses (63) y 1 año (252) a partir de los últimos 60 días de
15 series del mercado.

- **Código, datos y metodología:** <https://github.com/judithsalas/oil_price_prediction_case02>
- **App que los usa:** <https://prevision-brent.vercel.app>

## Qué hay aquí

| Carpeta | Contenido |
|---|---|
| `final/` | Los 9 modelos del estudio: `rnn`, `lstm` y `gru` para `corto`, `medio` y `largo`. Entrenados con datos de 2000 a 2017. |
| `app/` | Los tres modelos de la app reentrenados con todos los datos hasta la fecha. Aparece tras el primer reentrenamiento mensual. |

Cada archivo `.pt` guarda la red (`red`), sus hiperparámetros (`hp`), los pesos de las 3
semillas (`pesos`; la previsión es su media), el escalador de las entradas (`escalador`), la
ventana (`ventana`, 60 días) y el horizonte en días hábiles (`horizonte`).

La app usa la red elegida en validación para cada plazo: **GRU a 1 semana y LSTM a 3 meses
y a 1 año**.

## Cuánto fiarse

Test: 2021–2026, evaluado una sola vez. **Ninguna red mejora al precio de hoy** ("el precio
futuro es el de hoy"), que es la referencia.

| Plazo | Modelo de la app | Mejora frente al precio de hoy | R² (red / precio de hoy) | Acierto del rango del 80 % |
|---|---|---|---|---|
| 1 semana | GRU | −2,0 % | 0,88 / 0,88 | 71 % |
| 3 meses | LSTM | −26 % | −0,60 / −0,19 | 74 % |
| 1 año | LSTM | −55 % | −2,93 / −1,46 | 52 % |

Lo útil es el rango de incertidumbre y saber cuánto fiarse en cada plazo, no la cifra
central. Los modelos de `app/` ya han visto 2021–2026: estas cifras son las de `final/`.

## Cómo usarlos

Hace falta el código del repositorio de GitHub:

```python
import numpy as np
import torch

from petroleo.datos import descargar
from petroleo.preproceso import ultima_ventana
from scripts.evaluar import prediccion_red

ruta = 'final/gru_corto.pt'
guardado = torch.load(ruta, weights_only=False)
X, dia, precio = ultima_ventana(descargar(), guardado['escalador'], guardado['ventana'])
previsto = precio * np.exp(float(prediccion_red(ruta, X)[0]))
```

Los archivos son *pickles* de PyTorch que incluyen un escalador de scikit-learn, por eso se
cargan con `weights_only=False`. Cárgalos solo si te fías de su origen.

Herramienta educativa. No es asesoramiento financiero.
