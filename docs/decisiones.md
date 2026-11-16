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
