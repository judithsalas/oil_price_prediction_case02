# DESIGN.md: app de previsión del Brent

Para un comité de dirección o un responsable de compras de energía. Dirección:
**energía al atardecer**: fotos reales del sector (plataforma, petrolero, refinería) en
la portada y al inicio de cada sección, bandas oscuras color noche, contenido sobre papel
cálido y un naranja crudo como único color de acento (acciones, previsión y rango). Los tokens viven en `app/estilos.css`
como variables CSS; las páginas usan los nombres, nunca valores sueltos.

(Dirección elegida sin consultar sitios de referencia: UXKIN no estaba conectado.)

## Color

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--fondo` | `#F4F2EE` | `#0F151D` | Fondo de página (papel cálido) |
| `--superficie` | `#FFFFFF` | `#17202B` | Tarjetas, gráfico, panel de previsión |
| `--borde` | `#E3DED5` | `#273342` | Bordes y líneas de rejilla |
| `--texto` | `#14181F` | `#EDE9E2` | Texto principal y serie histórica |
| `--texto-suave` | `#5A5F69` | `#A3AAB5` | Texto secundario, ejes, notas |
| `--noche` / `--noche-2` | `#0D1520` / `#152131` | igual | Portada, bandas con foto, sección del ciclo, pie |
| `--sobre-noche` / `-suave` | `#F3EFE8` / `#B7BDC7` | igual | Texto sobre fondo noche |
| `--primario` | `#D9661F` | `#F08A43` | Acento único: botones, enlaces, plazo activo, previsión |
| `--incertidumbre-fondo` | `#D9661F2E` | `#F08A4333` | Banda y caja del rango del 80 % |
| `--bien` / `--aviso` / `--mal` | `#2F7A3E` / `#A16A00` / `#B23A2B` | `#6FBF7F` / `#E5B84B` / `#E8806F` | Fiabilidad |

Contraste: `--texto` y `--texto-suave` superan 4,5:1 sobre `--fondo` y `--superficie`
en los dos modos. El modo oscuro sigue al sistema (`prefers-color-scheme`).

## Tipografía

- **Titulares:** Source Serif 4 (Google Fonts), 600. Da tono de informe.
- **Texto e interfaz:** Public Sans, 400 / 500 / 600.
- **Cifras:** Public Sans con `font-variant-numeric: tabular-nums`, para que los
  precios no bailen.

| Token | Tamaño / interlineado | Uso |
|---|---|---|
| `--t-cifra` | 56 / 1.05 (40 en móvil) | Precio previsto |
| `--t-h1` | 40 / 1.15 (30 en móvil) | Título de la página |
| `--t-h2` | 28 / 1.2 | Título de sección |
| `--t-h3` | 20 / 1.3 | Subtítulos, tarjetas |
| `--t-cuerpo` | 17 / 1.6 | Texto |
| `--t-pequeno` | 14 / 1.5 | Notas, ejes, leyendas |
| `--t-micro` | 12 / 1.4 | Etiquetas de eventos en el gráfico |

Párrafos a 68 caracteres como máximo (`max-width: 68ch`).

## Espaciado

Escala de 4 px: `--e-1` 4, `--e-2` 8, `--e-3` 12, `--e-4` 16, `--e-5` 24, `--e-6` 32,
`--e-7` 48, `--e-8` 64, `--e-9` 96. Secciones separadas por `--e-8` (`--e-7` en
móvil). Ancho de contenido 1120 px; márgenes laterales de 16 px en móvil.

## Forma y profundidad

- Radio: `--r-1` 4 px (pestañas, etiquetas), `--r-2` 8 px (tarjetas, botones).
- Sombra: solo una, `--sombra` `0 1px 2px rgb(0 0 0 / .06)`, en la superficie del
  gráfico y el panel. El resto se separa con bordes.

## Componentes

- **Selector de horizonte:** tres tarjetas-pestaña (1 semana · 3 meses · 1 año) con el
  precio previsto, la variación y el rango de cada plazo; la activa con borde
  `--primario`. En móvil se oculta el rango. Accesibles con teclado (flechas) y foco
  visible (anillo de 2 px `--primario`).
- **Botón primario:** píldora (radio 999 px), fondo `--primario`. Hover
  `--primario-hover`. Desactivado al 45 % de opacidad. **Secundario:** borde y texto del
  color del fondo en que está.
- **Panel de previsión:** precio previsto en `--t-cifra`, variación frente al último
  precio, rango del 80 % en `--incertidumbre` y la etiqueta de fiabilidad.
- **Etiqueta de fiabilidad:** punto de color (`--bien` / `--aviso` / `--mal`) más texto;
  nunca solo color.
- **Gráfico:** histórico en `--texto`, previsión en `--primario`, banda en
  `--incertidumbre-fondo`. Eventos del ciclo como líneas verticales finas `--borde`
  con etiqueta `--t-micro` y detalle al pasar o enfocar.
- **Tarjetas:** `--superficie`, borde `--borde`, radio `--r-2`, sin sombra.
- **Navegación:** barra simple con el nombre y enlaces de ancla. **Pie:** fuentes de
  datos, enlace al repositorio y aviso de que no es asesoramiento financiero.

## Imagen e iconos

Fotos de Unsplash (licencia libre, enlazadas en el pie), siempre bajo un velo oscuro
para que el texto encima tenga contraste: plataforma al atardecer (portada), petrolero
(ciclo económico), refinería de noche (modelos) y refinería al anochecer (cierre). Iconos
de trazo estilo Lucide (1,75 px) en las tres tarjetas de explicación. Sin emojis ni texto
con degradado. Los gráficos van dentro de un `.lienzo` de altura fija (340 px; 260 en
móvil): sin ella Chart.js hace crecer el lienzo en cada redibujado.
