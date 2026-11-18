# DESIGN.md: app de previsión del Brent

Para un comité de dirección o un responsable de compras de energía. Dirección:
**informe financiero en blanco y negro**: tinta sobre papel, sin fotos ni color de
acento. La estructura la hacen el espacio, las líneas finas y la tipografía; las
secciones alternan papel blanco, gris muy claro y negro. El color solo aparece donde
significa algo: subida o bajada del precio y fiabilidad de la previsión. Los tokens viven
en `app/static/estilos.css` como variables CSS; las páginas usan los nombres, nunca
valores sueltos.

## Color

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--fondo` | `#FFFFFF` | `#0B0B0C` | Fondo de página |
| `--fondo-2` | `#F4F4F5` | `#111113` | Sección en tono (¿Acierta?) |
| `--superficie` | `#FFFFFF` | `#111113` | Marcos de gráficos, panel de previsión, tabla |
| `--borde` | `#E1E1E4` | `#2A2A2F` | Líneas finas y rejilla de los gráficos |
| `--texto` | `#0B0B0C` | `#F4F4F2` | Texto, serie histórica, previsión |
| `--texto-suave` | `#5C5F66` | `#A0A0A8` | Texto secundario, ejes, etiquetas |
| `--serie-2` / `--serie-3` | `#8A8A91` / `#C4C4CA` | `#7C7C84` / `#4A4A51` | Segunda serie y barras que no cumplen / bordes del rango |
| `--primario` / `--sobre-primario` | `#0B0B0C` / `#FFFFFF` | `#F4F4F2` / `#0B0B0C` | Botones, marcas del ciclo, etiqueta «en la app» |
| `--tenue` | tinta al 7 % | papel al 10 % | Banda del rango del 80 %, fila elegida, hover |
| `--bien` / `--aviso` / `--mal` | `#17734A` / `#8A5A00` / `#B3261E` | `#4CC38A` / `#E2B341` / `#F2766B` | Fiabilidad; `--bien` y `--mal` también subida y bajada |

La columna «Oscuro» está escrita una sola vez, en la clase `.oscura`, que redefine los
mismos tokens: todo lo que hay dentro se invierte solo, gráficos incluidos. La llevan
siempre la barra, la portada, el ciclo económico, el cierre y el pie; con el sistema en
modo oscuro (`prefers-color-scheme`) la lleva `<html>` y se invierte la página entera
(la pone `index.html` al cargar y `app.js` la cambia si el modo cambia). Contraste:
`--texto` y `--texto-suave` superan 4,5:1 sobre `--fondo`, `--fondo-2` y `--superficie`
en las dos paletas.

## Tipografía

- **Titulares y texto:** IBM Plex Sans (Google Fonts), 400 / 500 / 600 / 700. Titulares
  en 600 con el espaciado entre letras apretado (hasta −0,045em en la portada).
- **Datos:** IBM Plex Mono para etiquetas en mayúsculas (`.etq`, `.antetitulo`),
  variaciones, rangos, tabla, leyendas y ejes de los gráficos. Las cifras grandes van en
  Plex Sans con `font-variant-numeric: tabular-nums`, para que no bailen al contar.

| Token | Tamaño / interlineado | Uso |
|---|---|---|
| `--t-portada` | 44–80 px / 0.98 | Título de la portada |
| `--t-cifra` | 44–64 px / 1 | Precio previsto |
| `--t-h2` | 30–44 px / 1.08 | Título de sección |
| `--t-h3` | 18 / 1.3 | Subtítulos |
| `--t-cuerpo` | 17 / 1.6 | Texto |
| `--t-pequeno` | 14 / 1.5 | Notas, botones, tabla |
| `--t-micro` | 12 / 1.4 | Etiquetas en mono, leyendas |

Los tres primeros crecen con el ancho de la ventana (`clamp`). Párrafos a 68 caracteres
como máximo.

## Espaciado

Escala de 4 px: `--e-1` 4, `--e-2` 8, `--e-3` 12, `--e-4` 16, `--e-5` 24, `--e-6` 32,
`--e-7` 48, `--e-8` 64, `--e-9` 96. Secciones con `--e-9` arriba y abajo (`--e-8` en
móvil). Ancho de contenido 1160 px; márgenes laterales de 16 px en móvil.

## Forma y profundidad

Esquinas rectas: solo los botones tienen radio (`--r-1`, 2 px). Sin sombras ni
degradados, salvo el relleno bajo la línea de la portada. Los bloques se separan con
líneas de 1 px (`--borde`, o `--texto` cuando encabezan una columna).

## Componentes

- **Barra:** fija arriba, siempre negra: marca, enlaces de ancla y último precio. El
  enlace de la sección que se está leyendo queda subrayado (`aria-current`).
- **Portada:** negra. Título, entradilla y dos botones a la izquierda; a la derecha, la
  historia semanal del Brent como una sola línea. Debajo, cuatro cifras separadas por
  líneas finas: último precio y la previsión de cada plazo (enlaces que bajan a la
  previsión con ese plazo elegido).
- **Cabecera de sección:** número y nombre en mono (`01 — Previsión`), título y, si
  hace falta, un párrafo.
- **Selector de horizonte:** tres celdas en un marco de tinta; un bloque negro se desliza
  a la elegida y su texto se invierte. En móvil se oculta el rango. Accesible con teclado
  (flechas) y foco visible (anillo de 2 px `--texto`).
- **Panel de previsión:** un solo marco: a la izquierda el precio previsto en
  `--t-cifra`, la variación, el rango del 80 % y la fiabilidad; a la derecha el gráfico.
- **Etiqueta de fiabilidad:** punto de color (`--bien` / `--aviso` / `--mal`) más texto;
  nunca solo color.
- **Botón primario:** rectángulo de tinta (`--primario`), 48 px de alto. **Secundario:**
  solo borde. Desactivado al 45 % de opacidad.
- **Marco (`.marco`):** `--superficie` con borde `--borde`, para gráficos, bloques y tabla.
- **Columnas (`.columnas`):** tres textos, cada uno bajo una línea de tinta.
- **Tabla:** cifras en mono, cabecera en mayúsculas, fila del modelo de la app en
  `--tenue` con la etiqueta «EN LA APP».

## Gráficos

Sin color, las series se distinguen por trazo y peso:

- **Previsión:** el pasado es una línea continua `--texto`; la previsión, discontinua y
  con el punto final hueco; el rango, una banda `--tenue`.
- **Test:** precio real en `--texto`, previsión en `--serie-2`, precio de hoy (ingenuo)
  punteado en `--texto-suave`.
- **Barras por año:** en `--texto` si ese año cumple (error por debajo de 1, cobertura
  del 80 % o más) y en `--serie-2` si no.
- **Esquema walk-forward:** ajuste `--serie-2`, parada temprana `--serie-3`, validación
  `--texto` y test rayado.
- **Ciclo económico:** marcas numeradas que remiten a la lista de sucesos de debajo.

Cada gráfico va dentro de un `.lienzo` de altura fija (340 px; 260 en móvil): sin ella
Chart.js hace crecer el lienzo en cada redibujado.

## Movimiento

Una sola curva, `--salida` (`cubic-bezier(.16, 1, .3, 1)`): sale rápido y frena al llegar.

- **Portada, al cargar (`.entra`):** las palabras del título suben una tras otra; la
  línea del precio se dibuja de izquierda a derecha y termina en un punto que late; las
  cifras cuentan desde cero.
- **Al entrar en pantalla (`.rev`):** cada bloque sube y aparece; los de un mismo grupo,
  escalonados con `--d`.
- **Gráficos:** en blanco hasta que se ven; entonces las líneas se descubren de izquierda
  a derecha y las barras crecen desde su base. Lo hace el plugin `revelado` de
  `app.js`, no las animaciones de Chart.js.
- **Cambio de plazo:** el bloque del selector se desliza, la cifra cuenta de la anterior
  a la nueva y el gráfico se vuelve a dibujar.

Con `prefers-reduced-motion` no se anima nada: todo aparece en su estado final. Sin
JavaScript, el contenido está visible (las clases `.rev` solo ocultan bajo `.js`).

Al imprimir o guardar en PDF (`@media print`) todo sale en su estado final aunque no se
haya bajado por la página, con los fondos (las secciones negras se imprimen en negro),
los gráficos ajustados al ancho de la hoja y la tabla con sus ocho columnas.

## Imagen e iconos

Sin fotos, iconos decorativos, emojis ni texto con degradado. La única ilustración es el
propio dato: la línea del precio en la portada.
