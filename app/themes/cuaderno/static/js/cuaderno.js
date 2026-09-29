/* Tema Cuaderno · comportamiento. Cada bloque se activa solo si su elemento existe en la página. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ───── Encabezado: se marca con una línea al bajar ───── */
  var cab = $('#cab');
  function alBajar() { if (cab) cab.classList.toggle('scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', alBajar, { passive: true });
  alBajar();

  /* ───── Cajón del menú (celular) ───── */
  var burger = $('#burger'), velo = $('#velo');
  function menu(abrir) {
    document.body.classList.toggle('menu-abierto', abrir);
    if (burger) burger.setAttribute('aria-expanded', abrir ? 'true' : 'false');
  }
  if (burger) burger.addEventListener('click', function () { menu(!document.body.classList.contains('menu-abierto')); });
  if (velo) velo.addEventListener('click', function () { menu(false); });
  window.addEventListener('keydown', function (e) { if (e.key === 'Escape') menu(false); });

  /* ───── Barras (anchos y alturas): se llenan al entrar en pantalla ───── */
  function llenar(raiz) {
    $$('[data-w],[data-h]', raiz || document).forEach(function (el) {
      if (el.dataset.w) el.style.width = '0%';
      if (el.dataset.h) el.style.height = '0%';
    });
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        $$('[data-w],[data-h]', raiz || document).forEach(function (el) {
          if (el.dataset.w) el.style.width = el.dataset.w + '%';
          if (el.dataset.h) el.style.height = el.dataset.h + '%';
        });
      });
    });
  }
  if ('IntersectionObserver' in window) {
    var visto = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { visto.unobserve(e.target); llenar(e.target); } });
    }, { threshold: 0.2 });
    $$('.columnas, .tabla-wrap').forEach(function (b) { visto.observe(b); });
  } else {
    llenar();
  }

  /* ───── Pestañas de carpeta que muestran un panel por grupo ─────
     <div class="pest" data-group="tabla"><button data-key="primera" aria-selected="true">…</button></div>
     <div class="pane" data-group="tabla" data-key="primera">…</div>                                      */
  $$('.pest[data-group]').forEach(function (pest) {
    var grupo = pest.dataset.group, botones = $$('button', pest);
    if (!botones.length) return;
    function elegir(b, animar) {
      botones.forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      pest.scrollTo({ left: b.offsetLeft - (pest.clientWidth - b.offsetWidth) / 2, behavior: animar ? 'smooth' : 'auto' });
      $$('.pane[data-group="' + grupo + '"]').forEach(function (p) {
        var ver = p.dataset.key === b.dataset.key;
        p.hidden = !ver;
        if (ver && animar) llenar(p);
      });
    }
    botones.forEach(function (b) { b.addEventListener('click', function () { elegir(b, true); }); });
    elegir(botones.filter(function (b) { return b.getAttribute('aria-selected') === 'true'; })[0] || botones[0], false);
  });

  /* ───── Cuenta regresiva del próximo partido ───── */
  var cuenta = $('#cuenta');
  if (cuenta && cuenta.dataset.objetivo) {
    var objetivo = new Date(cuenta.dataset.objetivo).getTime(), nums = $$('b', cuenta);
    var tic = function () {
      var d = Math.max(0, objetivo - Date.now());
      var v = [Math.floor(d / 864e5), Math.floor(d / 36e5) % 24, Math.floor(d / 6e4) % 60, Math.floor(d / 1e3) % 60];
      nums.forEach(function (n, k) { n.textContent = String(v[k]).padStart(2, '0'); });
    };
    tic();
    setInterval(tic, 1000);
  }

  /* ───── Pizarra táctica: fichas arrastrables y flecha que las sigue ───── */
  var pizarra = $('#pizarra');
  if (pizarra) {
    var fichas = $$('.ficha', pizarra), trazo = $('#trazo'), punta = $('#punta');
    var W = 1000, H = 620, inicial = fichas.map(function (f) { return [f.style.left, f.style.top]; });
    var centro = function (f) { return [parseFloat(f.style.left) / 100 * W, parseFloat(f.style.top) / 100 * H]; };
    var flecha = function () {
      if (fichas.length < 2 || !trazo) return;
      var a = centro(fichas[0]), b = centro(fichas[1]);
      var dx = b[0] - a[0], dy = b[1] - a[1], dist = Math.hypot(dx, dy) || 1, ux = dx / dist, uy = dy / dist;
      var radio = 66, sx = a[0] + ux * radio, sy = a[1] + uy * radio, ex = b[0] - ux * (radio + 8), ey = b[1] - uy * (radio + 8);
      var largo = Math.hypot(ex - sx, ey - sy);
      if (largo < 40) { trazo.setAttribute('d', ''); if (punta) punta.setAttribute('d', ''); return; }
      var cx = (sx + ex) / 2 + uy * largo * 0.3, cy = (sy + ey) / 2 - ux * largo * 0.3; // la curva se arquea hacia arriba
      trazo.setAttribute('d', 'M' + sx + ',' + sy + ' Q' + cx + ',' + cy + ' ' + ex + ',' + ey);
      if (punta) {
        var tx = ex - cx, ty = ey - cy, tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
        var giro = function (ang) { var c = Math.cos(ang), s = Math.sin(ang); return [-(tx * c - ty * s) * 30, -(tx * s + ty * c) * 30]; };
        var p1 = giro(0.5), p2 = giro(-0.5);
        punta.setAttribute('d', 'M' + (ex + p1[0]) + ',' + (ey + p1[1]) + ' L' + ex + ',' + ey + ' L' + (ex + p2[0]) + ',' + (ey + p2[1]));
      }
    };
    flecha();
    fichas.forEach(function (f) {
      f.addEventListener('pointerdown', function (e) {
        f.setPointerCapture(e.pointerId);
        f.classList.add('arrastra');
        var caja = pizarra.getBoundingClientRect();
        var mover = function (ev) {
          var x = (ev.clientX - caja.left) / caja.width * 100, y = (ev.clientY - caja.top) / caja.height * 100;
          f.style.left = Math.max(7, Math.min(93, x)) + '%';
          f.style.top = Math.max(9, Math.min(88, y)) + '%';
          flecha();
        };
        var soltar = function () {
          f.classList.remove('arrastra');
          f.removeEventListener('pointermove', mover);
          f.removeEventListener('pointerup', soltar);
          f.removeEventListener('pointercancel', soltar);
        };
        f.addEventListener('pointermove', mover);
        f.addEventListener('pointerup', soltar);
        f.addEventListener('pointercancel', soltar);
      });
    });
    pizarra.addEventListener('dblclick', function () {
      fichas.forEach(function (f, i) { f.style.left = inicial[i][0]; f.style.top = inicial[i][1]; });
      flecha();
    });
  }

  /* ───── Índice lateral: marca la sección que se está leyendo ───── */
  var indice = $$('.indice a');
  if (indice.length && 'IntersectionObserver' in window) {
    var espia = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        indice.forEach(function (a) { a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id); });
      });
    }, { rootMargin: '-40% 0px -50% 0px' });
    indice.forEach(function (a) { var s = $(a.getAttribute('href')); if (s) espia.observe(s); });
  }

  /* ───── Avisos que se cierran solos ───── */
  $$('.flash').forEach(function (f) {
    setTimeout(function () { f.classList.add('out'); setTimeout(function () { f.remove(); }, 500); }, 4200);
  });

  /* ───── Acceso: ver/ocultar contraseña y coincidencia ───── */
  $$('.ojo').forEach(function (b) {
    b.addEventListener('click', function () {
      var input = document.getElementById(b.dataset.target);
      if (!input) return;
      var oculto = input.type === 'password';
      input.type = oculto ? 'text' : 'password';
      b.setAttribute('aria-label', oculto ? 'Ocultar contraseña' : 'Mostrar contraseña');
    });
  });
  var pw = $('#password'), vpw = $('#verifypassword'), pista = $('#pista-clave');
  if (pw && vpw && pista) {
    var revisar = function () {
      if (!pw.value && !vpw.value) { pista.textContent = ''; pista.className = 'pista-clave'; pw.className = vpw.className = ''; return; }
      var ok = pw.value === vpw.value;
      pista.textContent = ok ? 'Las contraseñas coinciden' : 'Las contraseñas no coinciden';
      pista.className = 'pista-clave ' + (ok ? 'ok' : 'mal');
      [pw, vpw].forEach(function (i) { i.classList.toggle('is-invalid', !ok); });
    };
    pw.addEventListener('input', revisar);
    vpw.addEventListener('input', revisar);
  }
})();
