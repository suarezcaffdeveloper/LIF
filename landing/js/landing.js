/* ElTablón · landing. Todo lo que anima es una mejora: sin GSAP o con movimiento reducido la página se lee completa. */
(function () {
  'use strict';
  var C = window.ELTABLON || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reducido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual'; // con secciones fijas, restaurar el scroll desarma la página
  var hayGsap = typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined';
  if (hayGsap) gsap.registerPlugin(ScrollTrigger);

  /* ───── Contacto: enlaces armados con config.js ───── */
  var wa = 'https://wa.me/' + (C.WHATSAPP || '') + '?text=' + encodeURIComponent(C.WHATSAPP_MENSAJE || '');
  $$('[data-wa]').forEach(function (a) { a.href = wa; a.target = '_blank'; a.rel = 'noopener'; });
  var asunto = 'Consulta desde la web de ElTablón';
  $$('[data-mail]').forEach(function (a) { a.href = 'mailto:' + (C.EMAIL || '') + '?subject=' + encodeURIComponent(asunto); });
  var anio = $('#anio'); if (anio) anio.textContent = '© ' + new Date().getFullYear();

  /* ───── Cinta de resultados (ficticios) ───── */
  var resultados = [
    ['Unión del Valle', 1, 0, 'Barrio Oeste'], ['Atlético Norte', 1, 2, 'Rápido del Este'], ['Social Ribera', 1, 2, 'Sociedad Fomento'],
    ['Deportivo Sur', 3, 3, 'Sportivo Central'], ['Puerto Unido', 0, 0, 'Club Faro'], ['Independencia FC', 3, 1, 'Juventud Arroyo']
  ];
  var cinta = $('#cinta');
  if (cinta) {
    var un = resultados.map(function (r) {
      return '<span class="tk"><b>' + r[0] + '</b><span class="r">' + r[1] + ' – ' + r[2] + '</span><b>' + r[3] + '</b></span>';
    }).join('');
    cinta.innerHTML = un + un + un + un;
  }

  /* ───── Hero: los diseños rotan en la maqueta ───── */
  var nombres = ['Cancha', 'Reflectores'];
  var vistas = $$('#escenario .laptop .vista'), vistasCelu = $$('#escenario .celu .vista'), etiqueta = $('#etiquetaDiseno');
  var actual = 0;
  function mostrarDiseno(i) {
    actual = i;
    vistas.forEach(function (v, k) { v.classList.toggle('on', k === i); });
    vistasCelu.forEach(function (v, k) { v.classList.toggle('on', k === i); });
    if (etiqueta) etiqueta.textContent = 'Diseño ' + nombres[i];
  }
  if (vistas.length && !reducido) setInterval(function () { mostrarDiseno((actual + 1) % vistas.length); }, 3800);

  /* ───── Titular: se ajusta al ancho disponible con el eje de ancho al máximo ───── */
  var titular = $('#titular');
  function ajustarTitular() {
    if (!titular) return;
    var cont = titular.parentElement, r = document.createRange();
    titular.style.setProperty('--ancho', 150);
    titular.style.fontSize = '100px';
    var movil = window.matchMedia('(max-width: 900px)').matches;
    var piezas = movil ? $$('.w', titular) : $$('.linea', titular);
    var mayor = 0;
    piezas.forEach(function (p) { r.selectNodeContents(p); mayor = Math.max(mayor, r.getBoundingClientRect().width); });
    if (!mayor) return;
    var tam = 100 * (cont.clientWidth / mayor) * 0.985;
    titular.style.fontSize = Math.max(40, Math.min(tam, 190)) + 'px';
  }
  ajustarTitular();
  window.addEventListener('resize', ajustarTitular);
  window.addEventListener('load', ajustarTitular);
  if (document.fonts) {
    // La fuente se pide recién cuando hay texto que la usa: se la carga a propósito y se recalcula al llegar.
    if (document.fonts.load) document.fonts.load('900 100px Anybody').then(ajustarTitular);
    if (document.fonts.ready) document.fonts.ready.then(ajustarTitular);
  }
  if ('ResizeObserver' in window && titular) new ResizeObserver(ajustarTitular).observe(titular.parentElement);

  /* ───── Textos gigantes del final: se ajustan al ancho de su columna para no pisar ni cortarse ───── */
  function medirTexto(el, texto) {
    var s = document.createElement('span');
    s.textContent = texto;
    s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font:inherit;letter-spacing:inherit;text-transform:inherit;font-variation-settings:inherit';
    el.appendChild(s);
    var ancho = s.getBoundingClientRect().width;
    s.remove();
    return ancho;
  }
  function ajustarFinal() {
    var t = $('.contacto-titulo');
    if (t) {
      t.style.fontSize = '100px';
      var palabra = medirTexto(t, 'ARMEMOS'); // la palabra más larga define el ancho mínimo
      if (palabra) t.style.fontSize = Math.max(34, Math.min(112, 100 * t.parentElement.clientWidth / palabra * 0.97)) + 'px';
    }
    var m = $('.pie-marca');
    if (m) {
      m.style.fontSize = '100px';
      var total = medirTexto(m, m.textContent);
      var cs = getComputedStyle(m.parentElement);
      var util = m.parentElement.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight); // ancho sin los márgenes internos
      if (total) m.style.fontSize = Math.max(40, Math.min(260, 100 * util / total * 0.99)) + 'px';
    }
  }
  ajustarFinal();
  window.addEventListener('resize', ajustarFinal);
  window.addEventListener('load', ajustarFinal);
  if (document.fonts && document.fonts.load) document.fonts.load('900 100px Anybody').then(ajustarFinal);

  /* ───── Scroll suave (Lenis) y anclas ───── */
  var lenis = null;
  if (hayGsap && typeof Lenis !== 'undefined' && !reducido) {
    lenis = new Lenis({ lerp: 0.1, smoothWheel: true });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
    gsap.ticker.lagSmoothing(0);
  }
  $$('a[href^="#"]').forEach(function (a) {
    var id = a.getAttribute('href');
    if (id.length < 2) return;
    a.addEventListener('click', function (e) {
      var destino = $(id);
      if (!destino) return;
      e.preventDefault();
      if (lenis) lenis.scrollTo(destino, { offset: -56 });
      else destino.scrollIntoView({ behavior: reducido ? 'auto' : 'smooth' });
    });
  });

  /* ───── Reloj del partido y barra oscura sobre las secciones oscuras ───── */
  var minEl = $('#min'), tiempoEl = $('#tiempo'), barra = $('#barra');
  function actualizarReloj() {
    var max = document.documentElement.scrollHeight - window.innerHeight;
    var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
    var m = Math.round(p * 90);
    if (minEl) minEl.textContent = m;
    if (tiempoEl) tiempoEl.textContent = m >= 89 ? 'Final' : (m < 45 ? '1.er tiempo' : '2.º tiempo');
    var oscuras = $$('.caos, .contacto, .pie'), y = 30, sobre = false;
    oscuras.forEach(function (s) { var b = s.getBoundingClientRect(); if (b.top <= y && b.bottom >= y) sobre = true; });
    if (barra) barra.classList.toggle('oscura', sobre);
  }
  window.addEventListener('scroll', actualizarReloj, { passive: true });
  window.addEventListener('resize', actualizarReloj);
  actualizarReloj();

  /* ───── Diseños: elegir diseño y color (capturas, o la demo en vivo) ───── */
  var estado = { tema: 'cancha', color: 'original' };
  var hexColor = { naranja: 'e2731f', violeta: '6b54d6', rojo: 'd42e5b', turquesa: '0e8f8f', azul: '3d6bff' };
  var enVivo = !!(C.DEMO_EN_VIVO && C.DEMO_URL);
  var cuerpo = $('#navegadorCuerpo'), imgDiseno = $('#vistaDiseno'), abrir = $('#abrirDemo'), notaDemo = $('#notaDemo'), iframe = null;
  function urlDemo() {
    var u = C.DEMO_URL.replace(/\/$/, '') + '/?tema=' + estado.tema;
    if (estado.color !== 'original') u += '&marca=%23' + hexColor[estado.color];
    return u;
  }
  function escalarIframe() {
    if (iframe && cuerpo) iframe.style.transform = 'scale(' + (cuerpo.clientWidth / 1440) + ')';
  }
  function pintarDiseno() {
    $$('.opcion').forEach(function (b) { b.setAttribute('aria-checked', b.dataset.tema === estado.tema ? 'true' : 'false'); });
    $$('.color').forEach(function (b) { b.setAttribute('aria-checked', b.dataset.color === estado.color ? 'true' : 'false'); });
    if (enVivo) {
      if (iframe) iframe.src = urlDemo() + '&embed=1';
      if (abrir) abrir.href = urlDemo();
    } else if (imgDiseno) {
      var nueva = 'assets/img/var-' + estado.tema + '-' + estado.color + '.webp';
      imgDiseno.classList.add('cambia');
      setTimeout(function () {
        imgDiseno.src = nueva;
        imgDiseno.alt = 'Sitio de ejemplo con el diseño ' + estado.tema.charAt(0).toUpperCase() + estado.tema.slice(1);
        imgDiseno.classList.remove('cambia');
      }, 180);
    }
  }
  if (cuerpo) {
    if (enVivo) {
      iframe = document.createElement('iframe');
      iframe.title = 'Demo en vivo de ElTablón';
      iframe.loading = 'lazy';
      iframe.src = urlDemo() + '&embed=1';
      cuerpo.innerHTML = '';
      cuerpo.appendChild(iframe);
      if (abrir) { abrir.hidden = false; abrir.href = urlDemo(); }
      if (notaDemo) notaDemo.textContent = 'Es la demo en vivo, con clubes y datos ficticios. Probá los botones y navegá por el sitio.';
      escalarIframe();
      window.addEventListener('resize', escalarIframe);
    }
    $$('.opcion').forEach(function (b) { b.addEventListener('click', function () { estado.tema = b.dataset.tema; pintarDiseno(); }); });
    $$('.color').forEach(function (b) { b.addEventListener('click', function () { estado.color = b.dataset.color; pintarDiseno(); }); });
  }

  /* ───── Perfiles: pestañas ───── */
  var pestanas = $$('.pestana'), paneles = $$('.panel'), escenas = $$('.escena'), perfilActual = 0;
  var claves = ['hincha', 'periodista', 'admin'];
  function elegirPerfil(i) {
    perfilActual = i;
    pestanas.forEach(function (t, k) { t.setAttribute('aria-selected', k === i ? 'true' : 'false'); });
    paneles.forEach(function (p, k) { p.hidden = k !== i; p.classList.toggle('on', k === i); });
    escenas.forEach(function (e) { e.classList.toggle('on', e.dataset.escena === claves[i]); });
  }
  var disparadorPerfiles = null;
  pestanas.forEach(function (t, i) {
    t.addEventListener('click', function () {
      if (disparadorPerfiles) {
        var st = disparadorPerfiles, y = st.start + (i + 0.5) / 3 * (st.end - st.start);
        if (lenis) lenis.scrollTo(y); else window.scrollTo({ top: y, behavior: 'smooth' });
      }
      elegirPerfil(i);
    });
  });

  /* ───── Formulario ───── */
  var form = $('#formulario'), estadoForm = $('#estadoForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var d = new FormData(form), nombre = (d.get('nombre') || '').trim(), contacto = (d.get('contacto') || '').trim();
      if (!nombre || !contacto) { estadoForm.textContent = 'Completá tu nombre y un email o teléfono para poder responderte.'; return; }
      var datos = { nombre: nombre, liga: d.get('liga'), contacto: contacto, mensaje: d.get('mensaje') };
      if (C.FORM_ENDPOINT) {
        estadoForm.textContent = 'Enviando…';
        fetch(C.FORM_ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(datos) })
          .then(function (r) { if (!r.ok) throw new Error(); estadoForm.textContent = '¡Listo! Recibimos tu consulta y te respondemos a la brevedad.'; form.reset(); })
          .catch(function () { estadoForm.textContent = 'No pudimos enviar el formulario. Probá por WhatsApp o por email.'; });
      } else {
        var cuerpoMail = 'Nombre: ' + datos.nombre + '\nLiga: ' + (datos.liga || '') + '\nContacto: ' + datos.contacto + '\n\n' + (datos.mensaje || '');
        window.location.href = 'mailto:' + (C.EMAIL || '') + '?subject=' + encodeURIComponent(asunto) + '&body=' + encodeURIComponent(cuerpoMail);
        estadoForm.textContent = 'Se abrió tu programa de correo con el mensaje listo para enviar.';
      }
    });
  }

  /* ═════════ Animaciones ═════════ */
  var caos = $('#caos');
  if (!hayGsap || reducido) {
    if (caos) caos.classList.add('estatico');
    return;
  }

  // Entrada del hero: las palabras suben y el titular se ensancha como un banderín que se despliega.
  var palabras = $$('.titular .w');
  gsap.set(palabras, { yPercent: 110 });
  gsap.set(titular, { '--ancho': 60 });
  gsap.set('.hero-texto .bajada, .hero-texto .acciones', { y: 24, opacity: 0 });
  gsap.set('#escenario', { y: 60, opacity: 0 });
  var intro = gsap.timeline({ defaults: { ease: 'power3.out' }, onComplete: enlazarScrollHero });
  intro.to(palabras, { yPercent: 0, duration: 1, stagger: 0.09 }, 0.15)
       .to(titular, { '--ancho': 150, duration: 1.7 }, 0.15)
       .to('.hero-texto .bajada, .hero-texto .acciones', { y: 0, opacity: 1, duration: 0.8, stagger: 0.12 }, 0.9)
       .to('#escenario', { y: 0, opacity: 1, duration: 1.1 }, 0.5);

  // Al bajar, el titular se condensa y la maqueta se desplaza un poco más lento.
  function enlazarScrollHero() {
    gsap.to(titular, { '--ancho': 72, ease: 'none', scrollTrigger: { trigger: '#hero', start: 'top top', end: 'bottom top', scrub: true } });
    gsap.to('#escenario', { y: -70, ease: 'none', scrollTrigger: { trigger: '#hero', start: 'top top', end: 'bottom top', scrub: true } });
  }

  var mm = gsap.matchMedia();

  // Del caos al sitio: sección fija con los papeles que se ordenan y se vuelven el sitio.
  mm.add('(min-width: 901px)', function () {
    if (caos) caos.classList.remove('estatico');
    var esc = $('#caosEscenario'), papeles = $$('.st', esc);
    var w = esc.clientWidth, h = esc.clientHeight;
    papeles.forEach(function (s) {
      gsap.set(s, { x: (+s.dataset.x / 100) * w * 0.9, y: (+s.dataset.y / 100) * h * 0.9, rotation: +s.dataset.r });
    });
    var tl = gsap.timeline({ scrollTrigger: { trigger: '#caos', start: 'top top', end: '+=230%', pin: true, scrub: 0.7, anticipatePin: 1 } });
    tl.to(papeles, { rotation: function (i) { return gsap.utils.random(-16, 16); }, x: '+=12', y: '-=10', stagger: 0.03, duration: 0.5, ease: 'none' })
      .addLabel('orden', 0.6)
      .to(papeles, { x: 0, y: 0, rotation: 0, scale: 0.3, opacity: 0, stagger: 0.04, duration: 0.6, ease: 'power2.in' }, 'orden')
      .to('#caosTitulo .hoy, #caosSub .hoy', { opacity: 0, duration: 0.25 }, 'orden+=0.3')
      .to('#caosTitulo .ahora, #caosSub .ahora', { opacity: 1, duration: 0.25 }, 'orden+=0.45')
      .to('#sitioFinal', { opacity: 1, scale: 1, duration: 0.7, ease: 'power3.out' }, 'orden+=0.5')
      .to({}, { duration: 0.5 });
  });
  mm.add('(max-width: 900px)', function () { if (caos) caos.classList.add('estatico'); });

  // Diseños: el marco se endereza al entrar.
  gsap.fromTo('#disenosVista .navegador', { rotationX: 16, y: 70, opacity: 0.7 },
    { rotationX: 0, y: 0, opacity: 1, ease: 'none', scrollTrigger: { trigger: '#disenosVista', start: 'top 92%', end: 'top 42%', scrub: true } });

  // Perfiles: sección fija que recorre los tres tipos de usuario al hacer scroll.
  mm.add('(min-width: 901px)', function () {
    disparadorPerfiles = ScrollTrigger.create({
      trigger: '#perfiles', start: 'top top', end: '+=260%', pin: true, anticipatePin: 1,
      onUpdate: function (self) {
        var i = Math.min(2, Math.floor(self.progress * 3));
        if (i !== perfilActual) elegirPerfil(i);
      }
    });
    return function () { disparadorPerfiles = null; };
  });

  // Ventajas: las líneas se dibujan al entrar.
  $$('.frases li').forEach(function (li) {
    gsap.fromTo(li, { '--l': 0 }, { '--l': 1, duration: 0.9, ease: 'power3.out', scrollTrigger: { trigger: li, start: 'top 88%' } });
  });

  // Instagram: las tres imágenes se abren en abanico.
  gsap.fromTo('.carta.c1', { rotation: 0, xPercent: 0, yPercent: 0 }, { rotation: -11, xPercent: -26, yPercent: 5, ease: 'none', scrollTrigger: { trigger: '#abanico', start: 'top 88%', end: 'top 34%', scrub: true } });
  gsap.fromTo('.carta.c3', { rotation: 0, xPercent: 0, yPercent: 0 }, { rotation: 11, xPercent: 26, yPercent: 5, ease: 'none', scrollTrigger: { trigger: '#abanico', start: 'top 88%', end: 'top 34%', scrub: true } });
  gsap.fromTo('.carta.c2', { yPercent: 0 }, { yPercent: -6, ease: 'none', scrollTrigger: { trigger: '#abanico', start: 'top 88%', end: 'top 34%', scrub: true } });

  // Pasos: el número del paso que se está leyendo se rellena.
  $$('#pasosLista li').forEach(function (li) {
    ScrollTrigger.create({ trigger: li, start: 'top 68%', end: 'bottom 42%', toggleClass: { targets: li, className: 'act' } });
  });

  // Contacto: el titular entra desde abajo.
  gsap.from('.contacto-titulo', { yPercent: 18, opacity: 0, duration: 1, ease: 'power3.out', scrollTrigger: { trigger: '.contacto', start: 'top 70%' } });

  window.addEventListener('load', function () { ScrollTrigger.refresh(); });
})();
