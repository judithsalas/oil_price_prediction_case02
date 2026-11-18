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
- La tasa 0,0001 da pasos más pequeños y retrasa el sobreajuste. En la rejilla final
  ayuda sobre todo a 252 días (mejora media −21 % frente a −27 % con 0,001) y empata
  en los otros dos; la eligen 4 de las 9 combinaciones finales.

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
- Resumen (`scripts/figuras.py`, sin reentrenar ni volver a evaluar):
  - `historia.png`: precio del Brent con los tramos de train, validación y test y los
    picos del ciclo, numerados como en la app.
  - `walk_forward.png`: esquema de los 3 pliegues (ajuste, parada temprana, validación)
    y del modelo final con su único test.
  - `validacion_vs_test.png`: mejora de cada red en validación y en test; muestra que lo
    elegido en validación no se sostiene.
  - `test_elegido.png`: el modelo de la app en test con su rango del 80 % y la cobertura.
- `v1_niveles/`, `v2_completo/`, `v3_sin_variables/`: figuras de los experimentos
  anteriores (los CSV están en las mismas carpetas de `docs/resultados/`).

Nota: la validación ya no se usa para parar, pero se ha consultado en varios
experimentos (v1 a v4), así que su error sigue siendo algo optimista. La cifra que
cuenta es la de test, que se evalúa una sola vez.

## Historial de experimentos

Un experimento por fila. Mejora frente al ingenuo en validación walk-forward, con la
mejor combinación de cada red (predicción media de las 3 semillas en v2–v4; media de
las semillas en v1). Los CSV y figuras de cada uno están en `docs/resultados/<carpeta>`
y `docs/figuras/<carpeta>` (v4 en la raíz).

| Exp. | Cambio | 5 días (RNN / LSTM / GRU) | 63 días | 252 días | Brecha train-val (63 / 252 d) |
|---|---|---|---|---|---|
| v1 `v1_niveles` | Precios en nivel, parada con val, paciencia 5 | +3,4 / +0,9 / +1,0 | +5,7 / +9,7 / +0,6 | −74 / −27 / −94 | 0,47 / 0,93 |
| v2 `v2_completo` | Bloque completo + volatilidad y nivel | +0,3 / +2,0 / +1,6 | −3,1 / +7,3 / −0,6 | −49 / +0,5 / −42 | 0,05 / 0,13 |
| v3 `v3_sin_variables` | v2 sin volatilidad ni nivel (único cambio) | +0,6 / +1,4 / +1,1 | +5,8 / +10,5 / +9,3 | −24 / −1,1 / −11 | 0,03 / 0,17 |
| v4 (final) | v3 recuperando el primer año de datos | +1,0 / +1,3 / +1,5 | +1,5 / +12,9 / +9,4 | −18 / +6,5 / −6,4 | 0,07 / 0,23 |

- v1 usaba la validación para parar, así que sus cifras son optimistas: v1 y el
  resto no son del todo comparables.
- v2 → v3 es el único experimento de un solo cambio, y decidió quitar las dos
  variables.
- La brecha es la diferencia entre el error relativo de validación y el de train en
  la mejor época. Con la regularización pasó de 0,5–0,9 a menos de 0,25.
- La mejor época sigue llegando pronto (mediana 3–4; un 29 % en la época 1): con
  rentabilidades del petróleo la señal es muy débil y la red empieza a memorizar
  ruido enseguida. Con paciencia 10 las curvas siguen al menos 10 épocas más, así
  que el mínimo se ve y se ve cómo la validación sube después.

### Modelos finales (`models/final/`)

| Horizonte | RNN | LSTM | GRU |
|---|---|---|---|
| 5 días | 16×2, lr 0,001 (1.089 parám.) | 32×2, lr 0,0001 (14.753) | 64×1, lr 0,001 (15.617) |
| 63 días | 16×2, lr 0,001 (1.089) | 32×1, lr 0,001 (6.305) | 64×2, lr 0,0001 (40.577) |
| 252 días | 32×2, lr 0,001 (3.713) | 64×1, lr 0,0001 (20.801) | 16×2, lr 0,0001 (3.233) |

(neuronas × capas, dropout 0,2 en todas.)

## Evaluación en test (`scripts/evaluar.py`)

Test: 2021 hasta hoy. Se evaluó **una sola vez**, con los modelos ya elegidos, y no
se ha cambiado nada después. Cada red predice con la media de sus 3 semillas. Ridge
es una regresión lineal sobre la ventana aplanada, con el mismo objetivo sin tendencia
y alfa elegido en validación.

| Horizonte | Ridge | RNN | LSTM | GRU |
|---|---|---|---|---|
| 5 días | −6,3 % (p 0,04) | −2,1 % (p 0,03) | −3,4 % (p 0,10) | −2,0 % (p 0,17) |
| 63 días | +1,3 % (p 0,90) | +1,1 % (p 0,88) | −26 % (p 0,16) | +1,5 % (p 0,90) |
| 252 días | −11 % (p 0,36) | −39 % (p 0,26) | −55 % (p 0,04) | −48 % (p 0,0005) |

Mejora del error cuadrático frente al ingenuo; p = Diebold-Mariano. Detalle en
`docs/resultados/test.csv` (incluye error en dólares y acierto de dirección) y por
año en `test_por_anio.csv` y `docs/figuras/test_por_anio.png`.

**Conclusión: ningún modelo bate al ingenuo en test.**

- A 5 días todos quedan un 2–6 % peor: el precio de hoy es la mejor previsión.
- A 63 días RNN, GRU y Ridge empatan con el ingenuo (p ≈ 0,9). La LSTM, la mejor en
  validación (+12,9 %), cae a −26 % en test, sobre todo por 2022–2024: es sobreajuste
  a la validación al elegir entre 12 combinaciones, no algo que deba corregirse
  mirando el test.
- A 252 días todas pierden; el modelo más simple (Ridge) es el que menos pierde. En
  2023–2024 las redes predijeron una vuelta al alza tras la bajada de 2022 que no
  llegó.
- El acierto de dirección ronda el 50 % en todos: no saben si el precio subirá o
  bajará.

### Diebold-Mariano: cuánto fiarse del p-valor

El contraste mira si la diferencia de error con el ingenuo es real o ruido. Las
previsiones a h días se solapan, así que la varianza se estima con h−1 retardos y
pesos de Bartlett, más la corrección de Harvey, Leybourne y Newbold. Se comprobó por
simulación con dos modelos iguales cuántas veces da p < 0,05 (debería ser un 5 %):
5,7–7,7 % a 5 y 63 días, pero **12 % a 252 días**. Con 5 años de test solo hay unos 5
periodos de un año independientes, y ningún contraste es fiable. A 252 días un
p < 0,05 no basta para concluir nada.

### Tabla comparativa (`scripts/comparar.py`)

`docs/resultados/comparativa.csv` junta, para cada red y horizonte, lo que pide el
enunciado (MAE, MSE y RMSE sobre el precio en dólares, mejora frente al ingenuo en
validación y test, parámetros y tiempo de entrenamiento), el R² que pidió después el
profesor y la estabilidad entre semillas. No vuelve a evaluar: lee las previsiones de
test ya guardadas.

| | Validación 5 / 63 / 252 d | Test 5 / 63 / 252 d | RMSE test ($) 5 / 63 / 252 d | Parámetros 5 / 63 / 252 d | Segundos por semilla |
|---|---|---|---|---|---|
| Ingenuo | 0 / 0 / 0 | 0 / 0 / 0 | 5,50 / 17,09 / 25,34 | 0 | 0 |
| RNN | +1,0 / +1,5 / −18 | −2,1 / +1,1 / −39 | 5,55 / 17,34 / 30,51 | 1.089 / 1.089 / 3.713 | 3–5 |
| LSTM | +1,3 / **+12,9** / **+6,5** | −3,4 / −26 / −55 | 5,59 / 19,82 / 32,01 | 14.753 / 6.305 / 20.801 | 2–8 |
| GRU | **+1,5** / +9,4 / −6,4 | −2,0 / +1,5 / −48 | 5,53 / 17,39 / 29,96 | 15.617 / 40.577 / 3.233 | 7–20 |

Todas entrenan en segundos en CPU: el coste no decide nada.

**R² y MSE en test**, sobre el precio en dólares. Se añadieron después, a partir de las
mismas previsiones guardadas: no se volvió a evaluar ni cambió ninguna decisión.

| | R² 5 / 63 / 252 d | MSE ($²) 5 / 63 / 252 d |
|---|---|---|
| Ingenuo | 0,88 / −0,19 / −1,46 | 30,2 / 292 / 642 |
| RNN | 0,88 / −0,22 / −2,57 | 30,8 / 301 / 931 |
| LSTM | 0,88 / −0,60 / −2,93 | 31,3 / 393 / 1.024 |
| GRU | 0,88 / −0,23 / −2,44 | 30,6 / 302 / 897 |

- R² = 1 − (error cuadrático de la previsión) / (error de prever siempre la media del
  precio real en test). Vale 1 si acierta siempre, 0 si lo hace como esa media y es
  negativo si lo hace peor.
- **A 5 días el R² es 0,88 para las tres redes y también para el ingenuo.** Un R² alto
  no demuestra aquí que la red prediga: mide que el precio de dentro de una semana se
  parece al de hoy. Por eso la métrica para decidir es la mejora frente al ingenuo y no
  el R².
- **A 63 y 252 días el R² es negativo, también para el ingenuo.** En 2021–2026 el precio
  se movió tanto que la media del periodo, que no se conoce de antemano, habría dado
  menos error que cualquier previsión hecha con meses de antelación.

### Modelo de la app: se elige por validación

En cada horizonte, la red con mayor mejora en validación walk-forward (predicción
media de las 3 semillas): **GRU a 5 días, LSTM a 63 y a 252 días**. Es la regla de
siempre y se aplica aunque en test la LSTM sea la peor: cambiarla ahora por la GRU
sería elegir con el test. Los cuatro repositorios de referencia hacen lo mismo, y a
Rubén y Alejandro también les falló en test la red elegida en validación.

Lo que la app dice con esto (enunciado, punto 5). La etiqueta de cada plazo sale del
test (`fiabilidad` en `app/prevision.py`): "Aporta valor" solo si la red mejora al
ingenuo con p < 0,05; "Orientativa" si no pierde más de un 5 % frente a él; si no, "No
mejora al precio de hoy".

- **1 semana (−2,0 %): "Orientativa: empata con el precio de hoy".** La previsión es
  prácticamente el precio de hoy. Lo útil es el rango.
- **3 meses (−26 %): "No mejora al precio de hoy".** En validación la LSTM mejoraba un
  13 %, pero en test no se sostiene. Vale como escenario, no como previsión.
- **1 año (−55 %): "No mejora al precio de hoy".** Ningún modelo bate al ingenuo en
  test. Solo vale el rango, y es poco fiable (ver abajo).

### Rango de incertidumbre (intervalo del 80 %)

Para cada red y horizonte se toman los percentiles 10 y 90 de sus errores fuera de
muestra en los 3 pliegues walk-forward (2012–2020, 9 años: incluye las caídas de
2014–16 y 2020). El intervalo es la previsión más esos dos percentiles. Con solo la
validación final (2018–2020) a 252 días salía −48 % / +3 %, dominado por la caída de
2020, y se descartó.

Después se midió **una sola vez** cuántas veces el precio real de test cayó dentro,
sin cambiar nada:

| Horizonte | Intervalo (modelo elegido) | Cobertura en test | Ingenuo |
|---|---|---|---|
| 5 días | −5,8 % / +5,2 % | 71 % | 71 % |
| 63 días | −24,5 % / +17,5 % | 74 % | 84 % |
| 252 días | −35,1 % / +20,0 % | 52 % | 70 % |

- Por debajo del 80 % en los tres: 2021–2026 ha sido más volátil que 2012–2020. A
  Alejandro le pasa lo mismo (48–58 % en 2026); Rubén obtiene 79–87 %.
- A 252 días el fallo se concentra en 2021 (8 % dentro: el Brent subió más del 60 % tras
  la pandemia, muy por encima del +20 %) y 2025 (38 %). En 2022–2024 cubre el 67–75 %.
  El intervalo está sesgado a la baja porque los años de calibración tienen dos
  desplomes y ninguna subida tan fuerte.
- La app debe mostrar el rango como "lo habitual", no como un límite, y avisar de que
  a 1 año falla en movimientos excepcionales.

### Comparación con los repositorios de referencia

Mismo enunciado, cuatro protocolos distintos. Cada uno usa su propia métrica y periodo
de test, así que las cifras nuestras se recalcularon en sus mismas condiciones:

| Horizonte | Álvaro (MAE, 2023+) | Rubén (RMSE, 2024+) | Alejandro (RMSE, 2023+) | Pablo (MAE, 2022+) | Nosotros, mismas condiciones |
|---|---|---|---|---|---|
| 5 días | −2,0 % | +0,1 % | −1,8 % | −0,5 % | −1,6 a −2,0 % (MAE 2023+) |
| 63 días | −4,5 % | −9,4 % | −61 % | −9,4 % (RNN) | RNN −7,0 % (MAE 2022+) |
| 252 días | −7,7 % | +6,7 % | −45 % | −19,8 % (RNN) | RNN −22 % (MAE 2022+); +8,5 % (MAE 2023+) |

(Álvaro frente a su "ingenuo con futuros", el equivalente a nuestro ingenuo.)

- Nadie bate al ingenuo de forma significativa. Con la misma red y periodo que Pablo
  los números casi coinciden: el resultado es del problema, no de un fallo propio.
- A 252 días el periodo de test pesa más que el modelo: nuestra RNN pasa de −22 % a
  +8,5 % solo con empezar el test en 2023. Los únicos positivos de las referencias a
  1 año también empiezan en 2023 o 2024.

### Por qué no se usa el "ingenuo con futuros"

Álvaro lo usa porque el spot del Brent de FRED/EIA se publica con unos 7 días de
retraso: su ingenuo normal es el precio de hace una semana, fácil de batir, y el de
futuros estima el de hoy. Aquí se supone que el spot de hoy se conoce, así que nuestro
ingenuo ya es la versión difícil; usar futuros posteriores a t sería una fuga. Además,
a 63 y 252 días harían falta contratos a 3 y 12 meses, que no hay gratis. La app
tampoco estima el precio de hoy con futuros: parte del último spot publicado y enseña
su fecha y los días que tiene (ver "La app"). Tomarlo del futuro más cercano (BZ=F)
queda como mejora posible.

## La app (`app/`, `scripts/exportar_web.py`)

El diseño visual está en `DESIGN.md`. Aquí van las decisiones de fondo.

### Una página, dos formas de servirla

- **En local, con servidor** (`app/servidor.py`, FastAPI): la página pide los datos a
  la API y tiene botones para descargar datos y reentrenar.
- **En Hugging Face, estática:** `scripts/exportar_web.py` vuelca la misma página y un
  `datos.json` con todo ya calculado. Se eligió así porque los Spaces estáticos son
  gratis y los de Docker exigen suscripción. A cambio, la página publicada no calcula
  nada: la actualiza GitHub Actions (`.github/workflows/web.yml`), también en cada
  push a `main`. El mismo workflow sube esa carpeta a Vercel si tiene un token: es otra
  dirección para la misma web, no otro despliegue que mantener.

### Incorporar datos no es reentrenar

Son dos procesos distintos, con ritmos distintos:

- **Cada día laborable se descargan los datos y se recalcula la previsión** con los
  modelos ya entrenados: la red solo recibe la ventana de los últimos 60 días. No se
  entrena nada.
- **El día 1 de cada mes, además, se reentrena** el modelo elegido de cada plazo con
  todos los datos hasta ese día, con la misma combinación de hiperparámetros y las
  mismas 3 semillas; el final de los datos sirve para la parada temprana. No se repite
  la búsqueda de hiperparámetros ni se cambia de red.
- Los modelos reentrenados se guardan aparte (`models/app/`) y los del estudio
  (`models/final/`) no se tocan. Las descargas de la app también van aparte
  (`data/app_dataset.csv`).
- **Lo que no cambia al reentrenar:** el rango y la etiqueta de fiabilidad siguen
  siendo los del estudio. Un modelo reentrenado ya ha visto 2021–2026, así que no se
  puede volver a medir en ese test.
- Una descarga solo sustituye a los datos anteriores si trae todas las series que
  esperan los modelos, y las de FRED se reintentan si el servidor falla: un mal día de
  una fuente no deja la app sin datos.

### Lo que enseña y cómo lo dice

- **El rango va por delante de la cifra central.** Ninguna red mejora con claridad al
  precio de hoy: enseñar la previsión central en grande prometería más de lo que el
  test respalda. La cifra central se muestra, con su variación, pero atenuada.
- **Se llama "rango habitual", no "rango del 80 %" a secas,** y se dice cuánto acertó
  de verdad en test (71 %, 74 % y 52 %).
- **El dato tiene fecha.** El spot se publica con unos 7 días de retraso: la app enseña
  la fecha del último precio y los días que tiene, cuenta los plazos desde ese día y
  avisa si la fecha prevista ya ha llegado.
- **"¿Acierta?"** enseña el modelo de cada plazo en test frente al precio real, con su
  rango, y año a año su error frente al precio de hoy y el acierto del rango.
- El color solo marca la fiabilidad, nunca la subida o la bajada del precio: se leería
  como bueno o malo.

## Relación con los apuntes de la asignatura (06_RNN)

| Decisión | Diapositiva |
|---|---|
| `nn.RNN` / `nn.LSTM` / `nn.GRU` con `batch_first`, último estado `out[:, -1]` y capa `Linear` | 7, 10, 17, 23 |
| Entrada (lote, ventana, variables) | 8 |
| Recorte de gradientes: cota de BPTT, producto de ‖W_hh‖·‖φ'‖ | 4 |
| W_hh ortogonal (norma 1) | 4 y 16 (`recurrent_initializer`) |
| Puerta de olvido a 1 | 16 (`unit_forget_bias`) |
| Dropout entre capas y antes de la salida | 16, 17 |
| L2 | 16 (`kernel_regularizer`, `recurrent_regularizer`) |
| Rentabilidades para que tanh y sigmoides no se saturen | 3, 7 |
| Número de parámetros | 6 |
| Adam | 9, 10, 18 |
| LSTM mejor en horizontes largos en validación (tabla comparativa) | 21 |

Lo que no se usa, y por qué:

- **`stateful=True`:** las ventanas se barajan, así que el estado no puede pasar de
  una muestra a la siguiente.
- **Pérdida en todos los pasos (`return_sequences=True`, L = Σ L_t):** las ventanas
  se solapan casi del todo y daría poca información nueva.
- **Transformers:** el enunciado pide RNN, LSTM y GRU.
- **MSE como pérdida:** se cambia por Huber por los días extremos (sí se usa MSE para
  elegir y comparar).

La tabla de la diapositiva 21 se cumple en validación (la LSTM es la mejor a 63 y 252
días) pero no en test, donde la LSTM es la que más sobreajusta: tiene más parámetros
("puede sobreajustar en datasets pequeños", misma tabla).

## Limitaciones

- **La validación se consultó en cuatro experimentos**, así que su error es
  optimista. Por eso la cifra que cuenta es la de test.
- **Del bloque de mejoras solo se aisló un cambio** (las dos variables). Su efecto
  conjunto está medido (v1 → v4), no el de cada uno por separado.
- **A 252 días hay muy pocos datos independientes**: unos 18 años de train y 5 de
  test. Ninguna conclusión a 1 año es estadísticamente sólida.
- **Batir al ingenuo no es ganar dinero.** Para invertir habría que batir al precio
  de los futuros, después de comisiones; con un acierto de dirección del 50 % no hay
  estrategia posible.
