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
