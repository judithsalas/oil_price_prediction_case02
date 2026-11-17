# Decisiones del proyecto

## Datos

### No se incluye la cesta de referencia de la OPEP (ORB)

El enunciado la cita como variable externa, pero no hay ninguna fuente diaria que
sea gratuita, sin clave y descargable desde un script:

- **Web de la OPEP** (`opec.org/basket/basketDayArchives.xml`): está detrás de
  Cloudflare y responde `403` a cualquier descarga automática (comprobado el
  16/11/2026).
- **FRED / EIA**: no publican la ORB diaria.
- **Otras fuentes** (Nasdaq Data Link, OilPriceAPI): piden registro o clave de API.
  Our World in Data y el Annual Statistical Bulletin de la OPEP solo tienen datos
  anuales.

Además, la ORB es una media de crudos que cotizan casi igual que el Brent (en
2020-2024 la media anual de la ORB y la del Brent se diferencian en menos de 1,5 $
por barril). Por eso aporta muy poca información que el Brent y el WTI no tengan ya.
Si se quisiera añadir, la opción sería bajar a mano el histórico de la web de la OPEP
y unirlo al CSV.

### Calendario y huecos

Se usan solo los días con precio real del Brent. El resto de series se rellenan con
su último valor (festivos distintos en cada mercado). El Brent nunca se rellena: así
no se inventan precios del objetivo.

## Preprocesado (`petroleo/preproceso.py`)

### Outliers

- **WTI negativo (−36,98 $, 20/04/2020):** se trata como dato faltante y se rellena
  con el día anterior. Fue un fallo puntual por el vencimiento del contrato de
  futuros, no un precio real del crudo. Se aplica a cualquier precio ≤ 0.
- **Máximo de 2008 y picos de 2022 y 2026:** se mantienen. Son movimientos reales
  del mercado y justo lo que la app tiene que explicar.
- **Tipo del BCE negativo (2014–2022):** es real y no se toca.

### Variables

- Se quitan los futuros del Brent (`brent_fut_*`): empiezan en 2007 y obligarían a
  perder 7 años. El Brent spot ya es el objetivo.
- Se quitan las primeras filas incompletas (hasta el 30/08/2000).
- Quedan 15 variables de entrada.

### Entradas como rentabilidades, no como precios

Cada precio entra como log-rentabilidad diaria, `log(x[t] / x[t-1])` (el volumen,
que puede ser 0, como `log(1 + x)`). El VIX y el tipo del BCE entran en nivel porque
ya son estables en el tiempo.

Motivo (apuntes, diapositivas 3, 4 y 7): la RNN calcula
`tanh(W_xh·x_t + W_hh·h_{t-1})`. Con precios en nivel estandarizados con la media de
2000–2017, el Brent de 2022 o 2026 queda fuera del rango visto en train: tanh y las
sigmoides de las puertas se saturan (φ' ≈ 0) y, por la cota de BPTT, el gradiente se
desvanece. Además la red aprende "en qué época estamos" en vez de patrones. Con
rentabilidades, entrada y objetivo están en la misma escala y el nivel del precio da
igual (lo comprueba `test_entradas_no_dependen_del_nivel_del_precio`).

Tras estandarizar, las entradas se recortan a ±5 desviaciones típicas para que un
día extremo (VIX en 2020) no desestabilice el entrenamiento.

### Variables descartadas por experimento: volatilidad y nivel

Se probaron dos variables más, usadas en los repositorios de referencia: la
volatilidad del Brent a 21 días y el precio frente a su media de 252 días. Con un
experimento de un solo cambio (misma rejilla con y sin ellas, ver "Historial de
experimentos") empeoraban: a 63 días las tres redes pasaban de batir al ingenuo a
perder con él, y a 252 días GRU y RNN perdían el doble. Se quitaron. La explicación
más probable es que la red las usaba para apostar por rebotes como el de 2009, que
fallan en años tranquilos como 2012–2013.

### Objetivo: log-rentabilidad, no precio

El modelo predice `log(brent[t+h] / brent[t])`, y el precio se recupera con
`brent[t] · exp(y)`. Así:

- el modelo no depende del nivel del precio (de 20 $ en 2000 a 140 $ en 2008);
- el modelo ingenuo ("precio futuro = precio de hoy") es simplemente `y = 0`.

### Partición temporal

| Partición | Fechas | Para qué |
|---|---|---|
| Train | 2000 – 2017 | Entrenar (incluye 2008 y 2014–2016) |
| Validación | 2018 – 2020 | Elegir hiperparámetros (incluye la pandemia) |
| Test | 2021 – hoy | Comparar las redes (incluye 2022 y 2026) |

- Una muestra solo entra en train o validación si el día que predice (t + h)
  también cae dentro. Así ningún objetivo mira datos de la partición siguiente.
  Al cambiar de partición se pierden h días de muestras: es el precio de no tener
  fugas.
- El escalador (`StandardScaler`) se ajusta solo con los datos de train.
- Ventana de entrada: 60 días hábiles, igual para las tres redes.
- **Parada temprana:** el último 15 % de las muestras de train forma la partición
  `parada`. Las muestras de ajuste cuyo objetivo cae ya dentro de ella se quitan
  (purga de h días). Así la validación no se usa para parar y queda limpia para
  elegir hiperparámetros.

## Modelos (`petroleo/modelos.py`)

### Una sola arquitectura para las tres redes

`Recurrente(tipo, ...)` es la misma red para `rnn`, `lstm` y `gru`: solo cambia la
capa recurrente (`nn.RNN`, `nn.LSTM` o `nn.GRU`). La entrada, el tamaño oculto, el
número de capas y la salida (una capa lineal sobre el estado del último día) son
iguales. Así la comparación mide solo el tipo de memoria.

### Un modelo por horizonte

Se entrena una red distinta para 5, 63 y 252 días. Cada horizonte tiene un número
distinto de muestras válidas (ver partición), y una red que predijera los tres a la
vez tendría que quedarse con las del más largo.

### Número de parámetros

Con el mismo tamaño oculto, la LSTM tiene unas 4 veces más parámetros que la RNN y la
GRU unas 3 veces más (con 64 neuronas y 15 variables: RNN 5.249, GRU 15.617,
LSTM 20.801). No se igualan a mano: las tres reciben la misma rejilla de
hiperparámetros ("presupuesto similar de ajuste") y el número de parámetros va en la
tabla comparativa.

### Inicialización (apuntes, diapositivas 4 y 16)

- **W_hh ortogonal en cada puerta.** La cota de la diapositiva 4 dice que el
  gradiente se desvanece si el producto de normas ‖W_hh‖·‖φ'‖ es menor que 1 y
  explota si es mayor. Una matriz ortogonal tiene norma 1: al empezar, ni una cosa ni
  la otra. Es lo que hace Keras por defecto (`recurrent_initializer='orthogonal'`);
  PyTorch no.
- **Sesgos a 0 y puerta de olvido de la LSTM a 1** (`unit_forget_bias=True` de la
  diapositiva 16, "mejora el aprendizaje en secuencias largas"). Con f = σ(1) ≈ 0,73
  la celda empieza conservando memoria en vez de borrarla. La GRU no tiene puerta de
  olvido, así que solo afecta a la LSTM.

### Regularización (apuntes, diapositiva 16)

- **Dropout 0,2 antes de la capa de salida**, también con 1 capa (como el
  `Dropout(0.2)` antes del `Dense` de los apuntes), y entre capas si hay 2.
- **L2 de 0,0001** sobre los pesos (`weight_decay` de Adam), el equivalente a
  `kernel_regularizer` y `recurrent_regularizer`.

### Modelo ingenuo

`ingenuo(X)` predice una log-rentabilidad de 0, es decir, "el precio futuro es el de
hoy". Es la referencia que las redes tienen que mejorar.

## Entrenamiento (`petroleo/entrenamiento.py`, `scripts/entrenar.py`)

### Walk-forward

Tres pliegues: train crece y la validación son los 3 años siguientes. Nunca se
mezclan fechas y test (2021+) no se usa para nada en esta fase.

| Pliegue | Train | Validación | Qué incluye la validación |
|---|---|---|---|
| 1 | 2000 – 2011 | 2012 – 2014 | Inicio de la caída de 2014 |
| 2 | 2000 – 2014 | 2015 – 2017 | Exceso de oferta 2015–2016 |
| 3 | 2000 – 2017 | 2018 – 2020 | Pandemia |

### Rejilla de hiperparámetros

La misma para las tres redes: 16, 32 o 64 neuronas × 1 o 2 capas × tasa de
aprendizaje 0,001 o 0,0001 = 12 combinaciones. Todo lo demás es fijo: Adam, lotes de
64, dropout 0,2, L2 0,0001, paciencia 10 y como mucho 100 épocas.

- Las 128 neuronas de la primera versión nunca ayudaron y las referencias acaban con
  redes pequeñas: se cambiaron por 16.
- La tasa 0,0001 da pasos más pequeños y retrasa el sobreajuste. Ganó en los tres
  horizontes y la eligen 8 de las 9 combinaciones ganadoras.

### Tres semillas: que la mejora no sea suerte

La semilla fija los pesos iniciales y el orden de las muestras. Con una sola semilla,
una mejora pequeña frente al ingenuo puede ser solo suerte de esa semilla. Por eso:

- La rejilla completa se entrena con 3 semillas (0, 1 y 2), cada una en una ejecución
  aparte (`scripts/entrenar.py --semilla N`).
- La combinación de cada red se elige por el **error de la predicción media de las 3
  semillas** en validación (media de los 3 pliegues), no por una semilla concreta.
  Es la predicción que usa la app, y promediar semillas siempre mejoró la cifra.
- Para cada red y horizonte se mira en cuántas semillas bate al ingenuo y cuánto
  varía la mejora (`docs/figuras/mejora_semillas.png`). Una red solo "aporta valor"
  en un horizonte si mejora al ingenuo con las 3 semillas.

### Objetivo sin tendencia, escalado y pérdida Huber

- **Sin tendencia.** La red aprende `y − media(y_train)` y predice con deriva 0. Sin
  esto aprendía la subida media de 2000–2014 (unos +12 % al año) y la proyectaba al
  futuro: era la causa principal de perder un 100 % frente al ingenuo a 252 días.
- **Escalado.** El objetivo se divide por su desviación típica en train (que la red
  guarda como `escala`). A 5 días las rentabilidades valen unos ±0,03 y darían
  gradientes minúsculos.
- **Huber en vez de MSE.** Los apuntes usan MSE; aquí se usa Huber porque los días
  extremos del petróleo (2008, 2020, 2022) dominarían el MSE. La métrica para elegir y
  comparar sigue siendo el MSE.

### Parada temprana

Al final de cada época se mide el error en la partición `parada` (el final de train).
Se guardan los pesos de la mejor época y se para tras 10 épocas sin mejorar, con un
máximo de 100. Los gradientes se limitan a norma 1 para que la RNN simple no
"explote" (cota de BPTT, diapositiva 4).

Con paciencia 10 las curvas siguen al menos 10 épocas después del mínimo, así que
siempre se ve dónde está y cómo la validación empieza a subir. La diferencia entre
train y validación en la mejor época se guarda en la columna `brecha`.

### Modelo final

Con `scripts/entrenar.py --final`, la combinación elegida de cada red y horizonte se
reentrena con las 3 semillas en la partición final (train 2000–2017, validación
2018–2020). Las 3 redes se guardan juntas en `models/final/<red>_<horizonte>.pt` con
su escalador, y la predicción es la media de las 3: más estable que una sola red. Son
9 ficheros pequeños que se suben al repositorio para que la app funcione sin entrenar.

### Gráficas (`docs/figuras/`)

Errores divididos por el del ingenuo: 1 = igual que el ingenuo, por debajo = mejor.

- `rejilla_s<N>.png`: mejora de cada combinación con la semilla N.
- `curvas_rejilla_s<N>.png`: curvas de aprendizaje (train y validación por época) de
  la mejor combinación de cada red, en cada pliegue.
- `curvas_finales.png`: curvas de los modelos guardados, una columna por semilla.
- `mejora_semillas.png`: mejora media frente al ingenuo y el valor de cada semilla.

- `test_por_anio.png`: error en test de cada modelo frente al ingenuo, año a año.
- `test_series.png`: precio real del Brent y previsión de cada modelo en test.
- `v1_niveles/`, `v2_completo/`, `v3_sin_variables/`: figuras de los experimentos
  anteriores (los CSV están en las mismas carpetas de `docs/resultados/`).

Nota: la validación ya no se usa para parar, pero se ha consultado en varios
experimentos (v1 a v4), así que su error sigue siendo algo optimista. La cifra que
cuenta es la de test, que se evalúa una sola vez.
