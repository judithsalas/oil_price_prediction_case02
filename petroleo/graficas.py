# =============================================================
#  Gráficas del entrenamiento (PNG en docs/figuras/)
#
#  Errores divididos por el error del modelo ingenuo: 1 = igual que el
#  ingenuo, por debajo de 1 = mejor. Así los tres horizontes se leen igual.
#  Cada red tiene siempre el mismo color.
# =============================================================
import matplotlib

matplotlib.use('Agg')                       # solo guarda ficheros, no abre ventanas
import matplotlib.pyplot as plt             # noqa: E402
from matplotlib.lines import Line2D         # noqa: E402
from matplotlib.ticker import MaxNLocator   # noqa: E402
import numpy as np                          # noqa: E402
import pandas as pd                         # noqa: E402

COLORES = {'rnn': '#2a78d6', 'lstm': '#eb6834', 'gru': '#1baf7a'}
NOMBRES = {'rnn': 'RNN', 'lstm': 'LSTM', 'gru': 'GRU'}
FONDO, TEXTO, TEXTO_2, REJILLA = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
PEOR = -100          # en la rejilla, mejoras peores que esto se pintan en el borde

plt.rcParams.update({
    'figure.facecolor': FONDO, 'axes.facecolor': FONDO, 'savefig.facecolor': FONDO,
    'axes.edgecolor': REJILLA, 'axes.labelcolor': TEXTO_2, 'text.color': TEXTO,
    'xtick.color': TEXTO_2, 'ytick.color': TEXTO_2, 'axes.titlesize': 11,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': REJILLA, 'grid.linewidth': 0.8,
    'font.size': 10,
})


def _leyenda_redes(fig, extra=()):
    marcas = [Line2D([], [], color=COLORES[r], lw=2, label=NOMBRES[r]) for r in COLORES]
    fig.legend(handles=[*marcas, *extra], loc='upper center', ncol=len(marcas) + len(extra),
               frameon=False, bbox_to_anchor=(0.5, 1.0))


def curvas(hist, columna, titulo, ruta):
    """Curvas de aprendizaje: filas = horizonte, columnas = `columna`
    ('pliegue' o 'semilla'). Línea continua = validación de la parada temprana
    (final de train), discontinua = train. El punto marca la mejor época."""
    horizontes, cols = hist['horizonte'].unique(), sorted(hist[columna].unique())
    fig, ejes = plt.subplots(len(horizontes), len(cols), squeeze=False, sharex=True,
                             figsize=(4 * len(cols), 2.8 * len(horizontes)))
    for i, h in enumerate(horizontes):
        for j, c in enumerate(cols):
            ax = ejes[i][j]
            sub = hist[(hist['horizonte'] == h) & (hist[columna] == c)]
            for red, g in sub.groupby('red', sort=False):
                val = g['mse_parada'] / g['ingenuo_parada']
                ax.plot(g['epoca'], val, color=COLORES[red], lw=2)
                ax.scatter(g['epoca'].loc[val.idxmin()], val.min(), s=30,
                           color=COLORES[red], edgecolor=FONDO, zorder=3)
                ax.plot(g['epoca'], g['mse_train'] / g['ingenuo_train'],
                        color=COLORES[red], lw=1.5, ls='--', alpha=0.7)
            ax.axhline(1, color=TEXTO_2, lw=1, ls=':')
            ax.set_ylim(0, 2)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.set_title(f'{h} · {columna} {c + 1 if columna == "pliegue" else c}', loc='left')
            if j == 0:
                ax.set_ylabel('error / ingenuo')
            if i == len(horizontes) - 1:
                ax.set_xlabel('época')
    _leyenda_redes(fig, [Line2D([], [], color=TEXTO_2, lw=2, label='validación (parada)'),
                         Line2D([], [], color=TEXTO_2, lw=1.5, ls='--', label='entrenamiento'),
                         Line2D([], [], color=TEXTO_2, lw=1, ls=':', label='ingenuo = 1')])
    fig.suptitle(titulo, y=1.04, fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def rejilla(tabla, titulo, ruta):
    """Mejora (%) frente al ingenuo de cada combinación de la rejilla."""
    horizontes = tabla['horizonte'].unique()
    fig, ejes = plt.subplots(1, len(horizontes), figsize=(4.5 * len(horizontes), 3.4),
                             squeeze=False)
    for ax, h in zip(ejes[0], horizontes):
        sub = tabla[tabla['horizonte'] == h]
        etiquetas = list(dict.fromkeys(sub['combinacion']))
        suelo = max(sub['mejora'].min() - 5, PEOR)
        for k, (red, g) in enumerate(sub.groupby('red', sort=False)):
            x = [etiquetas.index(c) + (k - 1) * 0.22 for c in g['combinacion']]
            fuera = g['mejora'] < suelo           # muy malos: se pintan en el borde
            ax.scatter(x, g['mejora'].clip(lower=suelo), s=42, color=COLORES[red],
                       edgecolor=FONDO, linewidth=1.5, zorder=3)
            for xi, f in zip(x, fuera):
                if f:
                    ax.annotate('▼', (xi, suelo), ha='center', va='top', fontsize=7,
                                color=TEXTO_2, xytext=(0, -5), textcoords='offset points')
        ax.axhline(0, color=TEXTO_2, lw=1)
        ax.set_ylim(bottom=suelo - 8)
        ax.set_xticks(range(len(etiquetas)), etiquetas, rotation=45, ha='right')
        ax.set_title(h, loc='left')
        ax.set_xlabel('neuronas × capas · tasa de aprendizaje')
    ejes[0][0].set_ylabel('mejora frente al ingenuo (%)')
    _leyenda_redes(fig, [Line2D([], [], color=TEXTO_2, marker='$▼$', lw=0, ms=6,
                                label=f'peor que {PEOR} %')])
    fig.suptitle(titulo, y=1.06, fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def mejora_semillas(tabla, titulo, ruta):
    """Barras = mejora media entre semillas; puntos = cada semilla."""
    horizontes = list(tabla['horizonte'].unique())
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ancho = 0.26
    for k, red in enumerate(COLORES):
        for i, h in enumerate(horizontes):
            m = tabla[(tabla['red'] == red) & (tabla['horizonte'] == h)]['mejora']
            x = i + (k - 1) * ancho
            ax.bar(x, m.mean(), ancho - 0.04, color=COLORES[red], zorder=2)
            ax.scatter([x] * len(m), m, s=16, color=TEXTO, zorder=3)
            # etiqueta siempre por encima: de la barra si es positiva, del 0 si no
            ax.annotate(f'{m.mean():+.1f}', (x, max(m.mean(), m.max(), 0)), ha='center',
                        fontsize=8, color=TEXTO_2, xytext=(0, 4), textcoords='offset points')
    ax.axhline(0, color=TEXTO_2, lw=1)
    ax.set_xticks(range(len(horizontes)), horizontes)
    ax.set_ylabel('mejora frente al ingenuo (%)')
    _leyenda_redes(fig, [Line2D([], [], color=TEXTO, marker='o', lw=0, ms=4,
                                label='cada semilla')])
    fig.suptitle(titulo, y=1.07, fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


REFERENCIAS = {'ingenuo': '#8a8984', 'ridge': '#7b5ea7'}


def test_por_anio(tabla, titulo, ruta):
    """Error de cada modelo dividido por el del ingenuo, año a año (test)."""
    horizontes = list(tabla['horizonte'].unique())
    modelos = ['ridge', *COLORES]
    colores = {**REFERENCIAS, **COLORES}
    fig, ejes = plt.subplots(len(horizontes), 1, figsize=(8, 2.6 * len(horizontes)),
                             squeeze=False, sharex=True)
    ancho = 0.8 / len(modelos)
    for ax, h in zip(ejes[:, 0], horizontes):
        sub = tabla[tabla['horizonte'] == h]
        for k, m in enumerate(modelos):
            g = sub[sub['modelo'] == m]
            ax.bar(g['anio'] + (k - (len(modelos) - 1) / 2) * ancho, g['ratio'], ancho * 0.9,
                   color=colores[m], zorder=2, label=NOMBRES.get(m, m.capitalize()))
        ax.axhline(1, color=TEXTO_2, lw=1, ls=':')
        ax.set_title(h, loc='left')
        ax.set_ylabel('error / ingenuo')
    ejes[0, 0].legend(loc='upper center', ncol=len(modelos), frameon=False,
                      bbox_to_anchor=(0.5, 1.35))
    fig.suptitle(titulo, y=1.03, fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def test_series(series, titulo, ruta):
    """Precio real frente a la previsión de cada modelo, en la fecha prevista."""
    horizontes = list(series['horizonte'].unique())
    fig, ejes = plt.subplots(len(horizontes), 1, figsize=(9, 2.8 * len(horizontes)),
                             squeeze=False, sharex=True)
    for ax, h in zip(ejes[:, 0], horizontes):
        sub = series[series['horizonte'] == h].sort_values('fecha_objetivo')
        x = pd.to_datetime(sub['fecha_objetivo'])
        ax.plot(x, sub['precio_real'], color=TEXTO, lw=1.6, label='real', zorder=3)
        ax.plot(x, sub['precio_ingenuo'], color=REFERENCIAS['ingenuo'], lw=1, ls='--',
                label='ingenuo')
        for red in COLORES:
            ax.plot(x, sub[f'precio_{red}'], color=COLORES[red], lw=1, alpha=0.85,
                    label=NOMBRES[red])
        ax.set_title(h, loc='left')
        ax.set_ylabel('$ por barril')
    ejes[0, 0].legend(loc='upper center', ncol=5, frameon=False, bbox_to_anchor=(0.5, 1.35))
    fig.suptitle(titulo, y=1.03, fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------
# Figuras de resumen (README y presentación): scripts/figuras.py
# ---------------------------------------------------------------
TRAMOS = {'train': ('#e9e8e4', 'entrenamiento'), 'val': ('#dde8f6', 'validación'),
          'test': ('#fbe3d5', 'test')}


def historia(brent, fin_train, fin_val, picos, titulo, ruta):
    """Precio diario con los tramos de train, validación y test, y los picos
    del ciclo numerados como en la app."""
    fin_train, fin_val = pd.Timestamp(fin_train), pd.Timestamp(fin_val)
    fig, ax = plt.subplots(figsize=(10, 3.6))
    limites = [brent.index[0], fin_train, fin_val, brent.index[-1]]
    for (color, nombre), a, b in zip(TRAMOS.values(), limites, limites[1:]):
        ax.axvspan(a, b, color=color, zorder=0, lw=0)
        desde = a.year if a == limites[0] else (a + pd.Timedelta(days=1)).year   # los cortes son el 31/12
        ax.text(a + (b - a) / 2, 1.01, f'{nombre}\n{desde}–{b.year}', transform=ax.get_xaxis_transform(),
                ha='center', va='bottom', fontsize=9, color=TEXTO_2)
    ax.plot(brent.index, brent, color=TEXTO, lw=0.9, zorder=2)
    for i, dia in enumerate(picos, 1):
        d = brent.index[brent.index.get_indexer([pd.Timestamp(dia)], method='nearest')[0]]
        ax.scatter(d, brent[d], s=150, color=COLORES['lstm'], edgecolor=FONDO, zorder=3)
        ax.text(d, brent[d], str(i), ha='center', va='center', fontsize=7.5, color='white',
                fontweight='bold', zorder=4)
    ax.set_ylabel('$ por barril')
    ax.set_xlim(limites[0], limites[-1])
    ax.set_ylim(0, brent.max() * 1.12)
    fig.suptitle(titulo, y=1.08, fontsize=12)
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def esquema_walk_forward(inicio, fin, pliegues, parada, titulo, ruta):
    """Una barra por pliegue: ajuste de pesos, parada temprana (último tramo de
    train) y validación. El último pliegue es el modelo final, que además se
    evalúa una sola vez en test."""
    inicio, fin = pd.Timestamp(inicio), pd.Timestamp(fin)
    colores = {'ajusta los pesos': '#8b93a1', 'parada temprana': '#cfd4dc',
               'validación (elige la combinación)': TEXTO, 'test, una sola vez': COLORES['lstm']}
    fig, ax = plt.subplots(figsize=(10, 2.6))
    filas = [f'Pliegue {i}' for i in range(1, len(pliegues) + 1)] + ['Modelo final']
    for y, (nombre, p) in enumerate(zip(filas, [*pliegues, pliegues[-1]])):
        a, b = pd.Timestamp(p['fin_train']), pd.Timestamp(p['fin_val'])
        corte = inicio + (a - inicio) * (1 - parada)
        tramos = [(inicio, corte), (corte, a), (a, b)] + ([(b, fin)] if nombre == 'Modelo final' else [])
        for (desde, hasta), color in zip(tramos, colores.values()):
            ax.barh(y, hasta - desde, left=desde, height=0.55, color=color, zorder=2)
    ax.set_yticks(range(len(filas)), filas)
    ax.invert_yaxis()
    ax.grid(axis='y', visible=False)
    ax.grid(axis='x', color=REJILLA)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)
    marcas = [plt.Rectangle((0, 0), 1, 1, color=c, label=n) for n, c in colores.items()]
    ax.legend(handles=marcas, loc='upper center', ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.14))
    fig.suptitle(titulo, y=1.0, fontsize=12)
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def validacion_vs_test(tabla, titulo, ruta):
    """Mejora frente al ingenuo de cada red en validación (círculo hueco) y en
    test (círculo lleno). Tabla: horizonte, modelo, mejora_val, mejora_test_%,
    elegido_app."""
    nombres_h = {'corto': '1 semana', 'medio': '3 meses', 'largo': '1 año'}
    filas = tabla[tabla['modelo'].isin(COLORES)].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 0.42 * len(filas) + 1.2))
    for y, f in filas.iterrows():
        val, test, color = f['mejora_val'], f['mejora_test_%'], COLORES[f['modelo']]
        ax.plot([val, test], [y, y], color=REJILLA, lw=3, zorder=1, solid_capstyle='round')
        ax.scatter(val, y, s=60, facecolor=FONDO, edgecolor=color, lw=2, zorder=3)
        ax.scatter(test, y, s=60, color=color, zorder=3)
        ax.text(1.01, y, f'{val:+.1f} %  →  {test:+.1f} %', transform=ax.get_yaxis_transform(),
                va='center', fontsize=9, color=TEXTO if f['elegido_app'] == True else TEXTO_2,
                fontweight='bold' if f['elegido_app'] == True else 'normal')
    etiquetas = [f"{nombres_h[f['horizonte']]} · {NOMBRES[f['modelo']]}" + (' ★' if f['elegido_app'] == True else '')
                 for _, f in filas.iterrows()]
    ax.set_yticks(range(len(filas)), etiquetas)
    for y in range(3, len(filas), 3):
        ax.axhline(y - 0.5, color=REJILLA, lw=1)
    ax.invert_yaxis()
    ax.axvline(0, color=TEXTO_2, lw=1)
    ax.grid(axis='y', visible=False)
    ax.grid(axis='x', color=REJILLA)
    ax.tick_params(axis='y', length=0)
    ax.set_xlabel('mejora frente al ingenuo (%): a la derecha de 0, mejor que el precio de hoy')
    marcas = [Line2D([], [], marker='o', ls='', markerfacecolor=FONDO, markeredgecolor=TEXTO_2, mew=2,
                     label='validación walk-forward (2012–2020)'),
              Line2D([], [], marker='o', ls='', color=TEXTO_2, label='test (2021–2026)'),
              Line2D([], [], ls='', label='★ modelo de la app')]
    ax.legend(handles=marcas, loc='upper center', ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.12))
    fig.suptitle(titulo, y=1.04, fontsize=12)
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)


def test_elegido(series, elegidos, titulo, ruta):
    """Modelo de la app en test: precio real, previsión, ingenuo y rango del 80 %.
    elegidos: {horizonte: (red, bajo, alto, cobertura)}; bajo/alto en log-rentabilidad."""
    nombres_h = {'corto': '1 semana', 'medio': '3 meses', 'largo': '1 año'}
    fig, ejes = plt.subplots(len(elegidos), 1, figsize=(10, 2.9 * len(elegidos)), squeeze=False, sharex=True)
    for ax, (h, (red, bajo, alto, cobertura)) in zip(ejes[:, 0], elegidos.items()):
        sub = series[series['horizonte'] == h].sort_values('fecha_objetivo')
        x, prev = pd.to_datetime(sub['fecha_objetivo']), sub[f'precio_{red}']
        ax.fill_between(x, prev * np.exp(bajo), prev * np.exp(alto), color=COLORES[red], alpha=0.18,
                        lw=0, label='rango del 80 %')
        ax.plot(x, sub['precio_real'], color=TEXTO, lw=1.4, label='precio real', zorder=3)
        ax.plot(x, sub['precio_ingenuo'], color=REFERENCIAS['ingenuo'], lw=1, ls='--', label='ingenuo')
        ax.plot(x, prev, color=COLORES[red], lw=1.3, label=f'previsión ({NOMBRES[red]})')
        ax.set_title(f'{nombres_h[h]} · {NOMBRES[red]} · el precio real cae dentro del rango '
                     f'el {cobertura * 100:.0f} % de las veces', loc='left', fontweight='bold')
        ax.set_ylabel('$ por barril')
        ax.legend(loc='upper left', ncol=4, frameon=False, fontsize=8.5)
    ejes[-1, 0].set_xlabel('fecha que se predice')
    fig.suptitle(titulo, y=1.01, fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches='tight')
    plt.close(fig)
