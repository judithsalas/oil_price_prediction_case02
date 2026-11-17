# DESIGN.md: app de previsión del Brent

Para un comité de dirección o un responsable de compras de energía: tiene que
parecer un informe de mercado serio y tranquilo, no un juguete de IA. Dirección:
**editorial financiera**, con papel cálido, tinta oscura, un solo color de acción y
un ámbar reservado para la incertidumbre. Los tokens viven en `app/estilos.css`
como variables CSS; las páginas usan los nombres, nunca valores sueltos.

(Dirección elegida sin consultar sitios de referencia: UXKIN no estaba conectado.)

## Color

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--fondo` | `#FAF8F4` | `#14161A` | Fondo de página (papel cálido) |
| `--superficie` | `#FFFFFF` | `#1C1F24` | Tarjetas, gráfico, panel de previsión |
| `--borde` | `#E4DFD6` | `#2E333A` | Bordes y líneas de rejilla |
| `--texto` | `#1A1A1A` | `#ECE9E3` | Texto principal y serie histórica |
| `--texto-suave` | `#5C5850` | `#A8A39A` | Texto secundario, ejes, notas |
| `--primario` | `#0E5A57` | `#4FB3AC` | Botones, enlaces, pestaña activa, línea de previsión |
| `--primario-hover` | `#0A4542` | `#6CC7C0` | Hover del primario |
| `--incertidumbre` | `#B5650D` | `#E0A458` | Banda del 80 % y su leyenda (único acento) |
| `--incertidumbre-fondo` | `#B5650D26` | `#E0A45833` | Relleno de la banda |
| `--bien` | `#2F7A3E` | `#6FBF7F` | Fiabilidad "aporta valor" |
| `--aviso` | `#9A6A00` | `#E5B84B` | Fiabilidad "orientativa" |
| `--mal` | `#A63A2B` | `#E27D6C` | Fiabilidad "no bate al precio de hoy", errores |

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

- **Selector de horizonte:** tres pestañas (1 semana · 3 meses · 1 año), la activa con
  fondo `--primario` y texto blanco. Accesibles con teclado (flechas) y foco visible
  (anillo de 2 px `--primario` con separación de 2 px).
- **Botón primario:** fondo `--primario`, texto blanco, radio `--r-2`. Hover
  `--primario-hover`. Desactivado al 45 % de opacidad. **Secundario:** borde `--borde`,
  texto `--texto`. **Discreto:** solo texto `--primario`, subrayado al pasar.
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

Sin fotos ni ilustraciones: el gráfico es la imagen. Iconos de trazo de Lucide (1,5 px),
solo donde aclaran algo. Sin degradados, sin emojis, sin texto con degradado.
