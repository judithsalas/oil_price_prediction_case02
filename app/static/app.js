// Página de la previsión del Brent: pide /api/resumen y lo dibuja.
const EVENTOS = [
  { fecha: '2008-07-03', precio: 144, titulo: 'Máximo histórico',
    texto: 'Demanda récord de China y otros emergentes, oferta justa y un dólar débil: el ciclo mundial estaba en lo más alto.' },
  { fecha: '2008-12-26', precio: 34, titulo: 'Crisis financiera',
    texto: 'La quiebra de Lehman Brothers en septiembre de 2008 hundió la economía y la demanda. El Brent perdió tres cuartas partes de su valor en cinco meses.' },
  { fecha: '2014-06-19', precio: 115, titulo: 'Empieza el exceso de oferta',
    texto: 'El petróleo de esquisto de EE. UU. inunda el mercado y en noviembre de 2014 la OPEP decide no recortar producción para defender su cuota.' },
  { fecha: '2016-01-20', precio: 26, titulo: 'Fondo de la caída 2014–2016',
    texto: 'Con más oferta que demanda y una China que crecía menos, el barril cayó un 77 % en año y medio. La OPEP+ nace a finales de 2016 para recortar.' },
  { fecha: '2020-04-21', precio: 9, titulo: 'Pandemia',
    texto: 'Los confinamientos hundieron el transporte y coincidieron con una guerra de precios entre Arabia Saudí y Rusia. El WTI cotizó en negativo el 20 de abril. El recorte récord de la OPEP+ y la reapertura lo devolvieron a 50 $ en enero de 2021.' },
  { fecha: '2022-03-08', precio: 133, titulo: 'Invasión de Ucrania',
    texto: 'La invasión rusa y las sanciones a uno de los mayores exportadores dispararon el miedo a la escasez, justo cuando la demanda se recuperaba. Después bajó con las subidas de tipos y el temor a una recesión.' },
  { fecha: '2025-12-16', precio: 60, titulo: 'Bajada gradual 2023–2025',
    texto: 'Demanda china más débil, producción récord fuera de la OPEP+ (EE. UU., Brasil, Guyana) y, en 2025, la OPEP+ deshaciendo parte de sus recortes.' },
  { fecha: '2026-04-07', precio: 138, titulo: 'Guerra de Irán y cierre de Ormuz',
    texto: 'La guerra entre EE. UU. e Irán dejó prácticamente cerrado desde el 4 de marzo el estrecho de Ormuz, por donde pasa cerca de una quinta parte del petróleo y el gas del mundo. Qatar declaró fuerza mayor en sus exportaciones y el Brent pasó de unos 70 $ a más de 130 $ en un mes. Siguió muy volátil mientras se estancaban las negociaciones.' },
];

const RIESGOS = {
  corto: 'Una decisión inesperada de la OPEP+, un ataque o conflicto en una zona productora, o un dato económico que sorprenda. A una semana basta una noticia para salirse del rango.',
  medio: 'Las reuniones de la OPEP+ sobre producción, conflictos en Oriente Medio o Rusia, el ritmo de la economía china y los cambios de tipos de interés y del dólar.',
  largo: 'Una recesión mundial o un nuevo ciclo de crecimiento, cambios de política de la OPEP+, guerras, la transición energética. A un año el precio depende sobre todo de hechos que hoy nadie conoce.',
};

const numero = (v, d = 1) => new Intl.NumberFormat('es-ES', { maximumFractionDigits: d, minimumFractionDigits: d }).format(v);
const dolar = { format: (v) => `${numero(v, 2)} $` };
const conSigno = (v, d = 1) => (v > 0 ? '+' : v < 0 ? '−' : '') + numero(Math.abs(v), d);
const fechaLarga = (iso) => new Date(iso + 'T12:00:00').toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
const ms = (iso) => Date.parse(iso + 'T12:00:00');
const color = (nombre) => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
const $ = (id) => document.getElementById(id);

let datos = null;
let actual = 0;
const graficos = {};

function textos(p) {
  const que = `El modelo (${p.red}) prevé que dentro de ${p.nombre}, hacia el ${fechaLarga(p.fecha_objetivo)}, ` +
    `el Brent esté en torno a ${dolar.format(p.previsto)}, un ${conSigno(p.variacion)} % sobre hoy ` +
    `(${dolar.format(p.precio_hoy)}). En 8 de cada 10 casos parecidos del pasado el precio acabó entre ` +
    `${dolar.format(p.bajo)} y ${dolar.format(p.alto)}.`;
  const cobertura = `En 2021–2026 el precio real cayó dentro del rango el ${numero(p.cobertura_test * 100, 0)} % de las veces (el objetivo es el 80 %).`;
  const fiar = {
    bien: `En la prueba con datos de 2021 a 2026 este modelo se equivocó un ${numero(p.mejora_test, 0)} % menos que suponer que el precio no cambia. ${cobertura}`,
    aviso: `En la prueba con datos de 2021 a 2026 acertó prácticamente igual que suponer que el precio no cambia ` +
      `(${numero(Math.abs(p.mejora_test), 0)} % más de error). La cifra central es orientativa; lo útil es el rango. ${cobertura}`,
    mal: `En la prueba con datos de 2021 a 2026 este modelo se equivocó más que suponer que el precio no cambia ` +
      `(${numero(Math.abs(p.mejora_test), 0)} % más de error). Tómalo como un escenario, no como una previsión: la ` +
      `referencia más prudente es el precio de hoy. ${cobertura}`,
  }[p.fiabilidad];
  return { que, fiar, riesgos: RIESGOS[p.horizonte] };
}

function pestanas() {
  const lista = $('pestanas');
  lista.innerHTML = '';
  datos.prevision.forEach((p, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.role = 'tab';
    b.id = `pestana-${p.horizonte}`;
    b.innerHTML = '<span class="h-nombre"></span><span class="h-precio"></span><span class="h-var"></span><span class="h-rango"></span>';
    b.querySelector('.h-nombre').textContent = `A ${p.nombre}`;
    b.querySelector('.h-precio').textContent = dolar.format(p.previsto);
    b.querySelector('.h-var').textContent = `${conSigno(p.variacion)} %`;
    b.querySelector('.h-rango').textContent = `rango ${numero(p.bajo, 0)}–${numero(p.alto, 0)} $`;
    b.setAttribute('aria-controls', 'panel-prevision');
    b.addEventListener('click', () => elegir(i));
    lista.append(b);
  });
  // Flechas para moverse entre pestañas (patrón ARIA de pestañas)
  lista.onkeydown = (e) => {
    const paso = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (!paso) return;
    const n = datos.prevision.length;
    elegir((actual + paso + n) % n);
    lista.children[actual].focus();
  };
}

function elegir(i) {
  actual = i;
  const p = datos.prevision[i];
  [...$('pestanas').children].forEach((b, j) => {
    b.setAttribute('aria-selected', String(j === i));
    b.tabIndex = j === i ? 0 : -1;
  });
  $('panel-prevision').setAttribute('aria-labelledby', `pestana-${p.horizonte}`);
  $('p-cuando').textContent = `Previsión a ${p.nombre} · ${fechaLarga(p.fecha_objetivo)}`;
  $('p-previsto').textContent = dolar.format(p.previsto);
  $('p-variacion').textContent = `${conSigno(p.variacion)} % sobre hoy`;
  $('p-rango').textContent = `${dolar.format(p.bajo)} – ${dolar.format(p.alto)}`;
  $('p-fiabilidad').className = `fiabilidad ${p.fiabilidad}`;
  $('p-fiabilidad').textContent = p.etiqueta;
  $('p-modelo').textContent = `Modelo ${p.red}, media de 3 redes. Entrenado: ${p.entrenado}.`;
  const t = textos(p);
  $('x-que').textContent = t.que;
  $('x-fiar').textContent = t.fiar;
  $('x-riesgos').textContent = t.riesgos;
  graficoPrevision(p);
  graficoTest(p);
}

function ejes(minX, maxX, formato, oscuro = false) {
  const borde = color(oscuro ? '--noche-borde' : '--borde');
  const rejilla = { color: borde };
  const ticks = { color: color(oscuro ? '--sobre-noche-suave' : '--texto-suave'), font: { family: 'Public Sans', size: 12 } };
  return {
    x: { type: 'linear', min: minX, max: maxX, grid: { display: false }, border: { color: borde },
         ticks: { ...ticks, maxTicksLimit: 7, callback: (v) => new Date(v).toLocaleDateString('es-ES', formato) } },
    y: { grid: rejilla, border: { display: false }, ticks: { ...ticks, callback: (v) => `${v} $` } },
  };
}

function base(escalas, extra = {}) {
  return {
    responsive: true, maintainAspectRatio: false, animation: false, parsing: false,
    interaction: { mode: 'nearest', intersect: false, axis: 'x' },
    scales: escalas,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: {
        title: (it) => new Date(it[0].parsed.x).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' }),
        label: (it) => `${it.dataset.label}: ${dolar.format(it.parsed.y)}`,
      } },
      ...extra,
    },
  };
}

function graficoPrevision(p) {
  const hoy = ms(p.fecha_hoy), fin = ms(p.fecha_objetivo);
  // A 1 semana bastan 3 meses de historia; si no, la previsión queda como un punto en el borde
  const desdeHist = p.dias <= 5 ? hoy - 90 * 864e5 : 0;
  const real = datos.historico.diario.map(([d, v]) => ({ x: ms(d), y: v })).filter((q) => q.x >= desdeHist);
  const desde = { x: hoy, y: p.precio_hoy };
  const conjuntos = [
    { label: 'Precio real', data: real, borderColor: color('--serie'), borderWidth: 1.75, pointRadius: 0 },
    { label: 'Rango bajo', data: [desde, { x: fin, y: p.bajo }], borderColor: color('--incertidumbre'), borderWidth: 1,
      pointRadius: 0, fill: '+1', backgroundColor: color('--incertidumbre-fondo') },
    { label: 'Rango alto', data: [desde, { x: fin, y: p.alto }], borderColor: color('--incertidumbre'), borderWidth: 1, pointRadius: 0 },
    { label: 'Previsión', data: [desde, { x: fin, y: p.previsto }], borderColor: color('--primario'), borderWidth: 2.5,
      borderDash: [6, 4], pointRadius: [0, 5], pointBackgroundColor: color('--primario') },
  ];
  graficos.prevision?.destroy();
  graficos.prevision = new Chart($('g-prevision'), {
    type: 'line', data: { datasets: conjuntos },
    options: base(ejes(real[0].x, fin + (fin - hoy) * 0.04, { month: 'short', year: '2-digit' })),
  });
  $('g-prevision').setAttribute('aria-label',
    `Precio reciente del Brent, de ${dolar.format(real[0].y)} a ${dolar.format(p.precio_hoy)}, y previsión a ${p.nombre} ` +
    `de ${dolar.format(p.previsto)} con rango entre ${dolar.format(p.bajo)} y ${dolar.format(p.alto)}.`);
}

function graficoCiclo() {
  const serie = datos.historico.semanal.map(([d, v]) => ({ x: ms(d), y: v }));
  const marcas = Object.fromEntries(EVENTOS.map((e, i) => [`e${i}`, {
    type: 'point', xValue: ms(e.fecha), yValue: e.precio, radius: 11,
    backgroundColor: color('--primario'), borderColor: color('--noche-2'), borderWidth: 2,
  }]));
  const numeros = Object.fromEntries(EVENTOS.map((e, i) => [`n${i}`, {
    type: 'label', xValue: ms(e.fecha), yValue: e.precio, content: String(i + 1),
    color: color('--sobre-primario'), font: { family: 'Public Sans', size: 11, weight: '700' },
  }]));
  graficos.ciclo?.destroy();
  graficos.ciclo = new Chart($('g-ciclo'), {
    type: 'line',
    data: { datasets: [{ label: 'Brent', data: serie, borderColor: color('--sobre-noche'), borderWidth: 1.25, pointRadius: 0,
      fill: 'origin', backgroundColor: color('--incertidumbre-fondo') }] },
    options: base(ejes(serie[0].x, serie.at(-1).x, { year: 'numeric' }, true),
      { annotation: { annotations: { ...marcas, ...numeros } } }),
  });
}

// ---- ¿Acierta? El modelo de la app en test (2021-2026), del plazo elegido ----
function graficoTest(p) {
  const t = datos.test?.[p.horizonte];
  if (!t) return;
  const punto = (k) => t.serie.map((f) => ({ x: ms(f[0]), y: f[k] }));
  $('a-intro').textContent = `Modelo ${t.red} a ${p.nombre}, probado en 2021–2026 con datos que no vio al entrenarse ` +
    '(modelos del estudio). Cambia de plazo arriba para ver los otros dos.';
  graficos.test?.destroy();
  graficos.test = new Chart($('g-test'), {
    type: 'line',
    data: { datasets: [
      { label: 'Rango bajo', data: punto(4), borderWidth: 0, pointRadius: 0, fill: '+1', backgroundColor: color('--incertidumbre-fondo') },
      { label: 'Rango alto', data: punto(5), borderWidth: 0, pointRadius: 0 },
      { label: 'Precio de hoy (ingenuo)', data: punto(3), borderColor: color('--texto-suave'), borderWidth: 1, borderDash: [4, 3], pointRadius: 0 },
      { label: 'Previsión', data: punto(2), borderColor: color('--primario'), borderWidth: 1.5, pointRadius: 0 },
      { label: 'Precio real', data: punto(1), borderColor: color('--serie'), borderWidth: 1.75, pointRadius: 0 },
    ] },
    options: base(ejes(ms(t.serie[0][0]), ms(t.serie.at(-1)[0]), { year: 'numeric' })),
  });
  const anios = t.por_anio.map((a) => String(a.anio));
  const barras = (id, valores, linea, formato, etiqueta) => {
    graficos[id]?.destroy();
    graficos[id] = new Chart($(id), {
      type: 'bar',
      data: { labels: anios, datasets: [{ label: etiqueta, data: valores, backgroundColor: color('--primario'), borderRadius: 4 }] },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        scales: {
          x: { grid: { display: false }, ticks: { color: color('--texto-suave') } },
          y: { beginAtZero: true, grid: { color: color('--borde') }, border: { display: false },
               ticks: { color: color('--texto-suave'), callback: formato } },
        },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (it) => `${etiqueta}: ${formato(it.parsed.y)}` } },
          annotation: { annotations: { ref: { type: 'line', yMin: linea, yMax: linea, borderColor: color('--texto'), borderWidth: 1.5, borderDash: [5, 4] } } },
        },
      },
    });
  };
  barras('g-anio', t.por_anio.map((a) => a.error_vs_ingenuo), 1, (v) => numero(v, 1), 'Error / ingenuo');
  barras('g-cobertura', t.por_anio.map((a) => a.cobertura * 100), 80, (v) => `${numero(v, 0)} %`, 'Dentro del rango');
}

// ---- Comparativa: esquema walk-forward y validación frente a test ----
function esquema() {
  const v = datos.validacion;
  const ini = ms(v.inicio), fin = ms(datos.prevision[0].fecha_hoy);
  const pct = (iso) => ((ms(iso) - ini) / (fin - ini)) * 100;
  const PARADA = 0.15;    // último 15 % de train (petroleo/preproceso.py)
  const filas = [...v.walk_forward.map((p, i) => ({ nombre: `Pliegue ${i + 1}`, ...p })),
                 { nombre: 'Modelo final', ...v.particion, test: true }];
  $('esquema').innerHTML = '';
  for (const f of filas) {
    const a = pct(f.fin_train), b = pct(f.fin_val), corte = a * (1 - PARADA);
    const tramos = [['t-ajuste', 0, corte], ['t-parada', corte, a], ['t-valida', a, b], ...(f.test ? [['t-test', b, 100]] : [])];
    const fila = document.createElement('div');
    fila.className = 'esquema-fila';
    fila.innerHTML = `<span></span><div class="esquema-barra" role="img"></div>`;
    fila.firstChild.textContent = f.nombre;
    fila.lastChild.setAttribute('aria-label', `Entrena hasta ${f.fin_train.slice(0, 4)}, valida hasta ${f.fin_val.slice(0, 4)}` +
      (f.test ? ' y se prueba una vez en 2021–2026' : ''));
    for (const [cls, x0, x1] of tramos) {
      const s = document.createElement('span');
      s.className = cls;
      s.style.left = `${x0}%`;
      s.style.width = `${x1 - x0}%`;
      fila.lastChild.append(s);
    }
    $('esquema').append(fila);
  }
  const ejesTxt = document.createElement('div');
  ejesTxt.className = 'esquema-ejes';
  ejesTxt.innerHTML = `<span>${v.inicio.slice(0, 4)}</span><span>${datos.prevision[0].fecha_hoy.slice(0, 4)}</span>`;
  $('esquema').append(ejesTxt);
}

function pesas() {
  const nombres = { corto: '1 semana', medio: '3 meses', largo: '1 año' };
  const redes = { rnn: 'RNN', lstm: 'LSTM', gru: 'GRU' };
  const colores = { rnn: '#2A78D6', lstm: color('--primario'), gru: '#1BAF7A' };
  const filas = datos.comparativa.filter((f) => redes[f.modelo]);
  const vals = filas.flatMap((f) => [f.mejora_val, f['mejora_test_%']]);
  const min = Math.floor(Math.min(...vals, 0) / 10) * 10, max = Math.ceil(Math.max(...vals, 0) / 10) * 10;
  const x = (v) => ((v - min) / (max - min)) * 100;
  $('pesas').innerHTML = '';
  let anterior = null;
  for (const f of filas) {
    const val = f.mejora_val, test = f['mejora_test_%'];
    const fila = document.createElement('div');
    fila.className = `pesa${anterior && anterior !== f.horizonte ? ' grupo' : ''}${f.elegido_app ? ' app' : ''}`;
    fila.style.setProperty('--color', colores[f.modelo]);
    fila.innerHTML = `<span></span><div class="pesa-pista" role="img"><span class="pesa-cero"></span><span class="pesa-linea"></span>` +
      `<span class="pesa-punto"></span><span class="pesa-punto lleno"></span></div><span class="pesa-num"></span>`;
    fila.children[0].textContent = `${nombres[f.horizonte]} · ${redes[f.modelo]}${f.elegido_app ? ' ★' : ''}`;
    const pista = fila.children[1];
    pista.setAttribute('aria-label', `Validación ${conSigno(val)} %, test ${conSigno(test)} %`);
    pista.children[0].style.left = `${x(0)}%`;
    pista.children[1].style.left = `${Math.min(x(val), x(test))}%`;
    pista.children[1].style.width = `${Math.abs(x(val) - x(test))}%`;
    pista.children[2].style.left = `${x(val)}%`;
    pista.children[3].style.left = `${x(test)}%`;
    fila.children[2].textContent = `${conSigno(val)} → ${conSigno(test)} %`;
    $('pesas').append(fila);
    anterior = f.horizonte;
  }
  const eje = document.createElement('div');
  eje.className = 'pesas-eje';
  eje.innerHTML = `<span></span><div><span>${min} %</span><span>+${max} %</span></div><span></span>`;
  $('pesas').append(eje);
}

function eventos() {
  $('eventos').innerHTML = '';
  for (const e of EVENTOS) {
    const li = document.createElement('li');
    li.innerHTML = `<span class="fecha"></span><h3></h3><p></p>`;
    li.querySelector('.fecha').textContent = `${fechaLarga(e.fecha)} · ${e.precio} $`;
    li.querySelector('h3').textContent = e.titulo;
    const p = li.querySelector('p');
    p.textContent = e.texto;
    $('eventos').append(li);
  }
}

function tabla() {
  const nombres = { corto: '1 semana', medio: '3 meses', largo: '1 año' };
  const redes = { ingenuo: 'Precio de hoy (ingenuo)', rnn: 'RNN simple', lstm: 'LSTM', gru: 'GRU' };
  const pct = (v) => (v == null ? '—' : `${conSigno(v)} %`);
  let html = `<caption class="oculto">MAE, RMSE, mejora frente al ingenuo, parámetros y tiempo de entrenamiento por red y horizonte</caption>
    <thead><tr><th scope="col">Modelo</th><th scope="col">Mejora validación</th><th scope="col">Mejora test</th>
    <th scope="col">MAE test</th><th scope="col">RMSE test</th><th scope="col">Rango del 80 % acierta</th>
    <th scope="col">Parámetros</th><th scope="col">Entrenamiento</th></tr></thead><tbody>`;
  for (const h of Object.keys(nombres)) {
    html += `<tr class="grupo"><th colspan="8" scope="colgroup">${nombres[h]}</th></tr>`;
    for (const f of datos.comparativa.filter((f) => f.horizonte === h && redes[f.modelo])) {
      const ingenuo = f.modelo === 'ingenuo';
      html += `<tr class="${f.elegido_app ? 'elegido' : ''}">
        <th scope="row">${redes[f.modelo]}${f.elegido_app ? '<span class="marca-app">EN LA APP</span>' : ''}</th>
        <td>${ingenuo ? 'referencia' : pct(f.mejora_val)}</td><td>${ingenuo ? 'referencia' : pct(f['mejora_test_%'])}</td>
        <td>${dolar.format(f['mae_$'])}</td><td>${dolar.format(f['rmse_$'])}</td>
        <td>${numero(f.cobertura_test * 100, 0)} %</td>
        <td>${ingenuo ? '0' : numero(f.parametros, 0)}</td><td>${ingenuo ? '—' : `${numero(f.segundos, 0)} s`}</td></tr>`;
    }
  }
  $('tabla').innerHTML = html + '</tbody>';
}

function pintar() {
  const p0 = datos.prevision[0];
  $('precio-hoy').textContent = dolar.format(p0.precio_hoy);
  $('fecha-hoy').textContent = fechaLarga(p0.fecha_hoy);
  pestanas();      // se rehace: las tarjetas muestran la previsión de cada plazo
  elegir(actual);
  graficoCiclo();
}

async function cargar() {
  // Con servidor (en local) se pide la API; en el Space estático, datos.json,
  // que genera GitHub Actions cada día (scripts/exportar_web.py)
  let r = await fetch('api/resumen').catch(() => null);
  const estatico = !r?.ok;
  if (estatico) r = await fetch('datos.json');
  if (!r.ok) throw new Error(`El servidor respondió ${r.status}`);
  datos = await r.json();
  $('modo-servidor').hidden = $('acciones').hidden = estatico;
  $('modo-estatico').hidden = !estatico;
  if (estatico) $('generado').textContent = new Date(datos.generado).toLocaleString('es-ES', { dateStyle: 'long', timeStyle: 'short' });
  pintar();
  eventos();
  tabla();
  esquema();
  pesas();
}

async function tarea(ruta, boton) {
  const estado = $('estado');
  const botones = [$('b-actualizar'), $('b-reentrenar')];
  estado.className = 'estado pequeno';
  const r = await fetch(ruta, { method: 'POST' });
  if (!r.ok) {
    estado.textContent = (await r.json()).detail ?? `Error ${r.status}`;
    estado.classList.add('error');
    return;
  }
  botones.forEach((b) => (b.disabled = true));
  boton.setAttribute('aria-busy', 'true');
  let e;
  try {
    do {
      await new Promise((ok) => setTimeout(ok, 1500));
      e = await (await fetch('api/estado')).json();
      estado.textContent = e.mensaje;
    } while (e.tarea);
  } catch (err) {     // p. ej. el servidor se reinició a mitad de la tarea
    e = { error: `se perdió la conexión con el servidor (${err.message})` };
  } finally {
    botones.forEach((b) => (b.disabled = false));
    boton.removeAttribute('aria-busy');
  }
  if (e.error) {
    estado.textContent = `No se pudo terminar: ${e.error}`;
    estado.classList.add('error');
  } else {
    await cargar();
    estado.textContent = `Hecho. Previsión recalculada con datos hasta el ${fechaLarga(datos.prevision[0].fecha_hoy)}.`;
  }
}

$('b-actualizar').addEventListener('click', (ev) => tarea('api/actualizar', ev.currentTarget));
$('b-reentrenar').addEventListener('click', (ev) => tarea('api/reentrenar', ev.currentTarget));
// Los colores salen de las variables CSS: al cambiar de modo claro/oscuro se redibuja
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => datos && pintar());

cargar().catch((err) => {
  $('estado').textContent = `No se pudo cargar la previsión: ${err.message}`;
  $('estado').classList.add('error');
});
