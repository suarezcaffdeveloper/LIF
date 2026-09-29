/* Tema Cancha · comportamiento. Cada bloque se activa solo si su elemento existe en la página. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ───── Nav: se oscurece al scrollear y muestra el progreso de lectura ───── */
  var nav = $('#nav'), prog = $('#prog'), lines = $('#lines');
  function onScroll() {
    var y = window.scrollY, max = document.documentElement.scrollHeight - window.innerHeight;
    if (nav) nav.classList.toggle('scrolled', y > 50);
    if (prog) prog.style.transform = 'scaleX(' + (max > 0 ? y / max : 0) + ')';
    if (lines && y < window.innerHeight) lines.style.transform = 'translateY(' + (y * 0.12) + 'px)';
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (lines) {
    window.addEventListener('mousemove', function (e) {
      if (window.scrollY > window.innerHeight) return;
      lines.style.transform = 'translate(' + ((e.clientX / innerWidth - 0.5) * -30) + 'px,' +
        ((e.clientY / innerHeight - 0.5) * -20 + window.scrollY * 0.12) + 'px)';
    });
  }

  /* ───── Pestañas con pieza deslizante que muestran un panel por grupo ─────
     <div class="seg" data-group="tabla"><button data-key="primera" aria-selected="true">…</button></div>
     <div class="pane" data-group="tabla" data-key="primera">…</div>                              */
  function initSeg(seg) {
    var group = seg.dataset.group;
    var btns = $$('button', seg);
    if (!btns.length) return;
    var th = document.createElement('span');
    th.className = 'th';
    seg.insertBefore(th, seg.firstChild);
    function move(b) { th.style.left = b.offsetLeft + 'px'; th.style.width = b.offsetWidth + 'px'; }
    function select(b, scroll) {
      btns.forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      move(b);
      /* Centra la pestaña elegida dentro de la barra (sin mover la página). */
      seg.scrollTo({ left: b.offsetLeft - (seg.clientWidth - b.offsetWidth) / 2, behavior: scroll ? 'smooth' : 'auto' });
      $$('.pane[data-group="' + group + '"]').forEach(function (p) { p.hidden = p.dataset.key !== b.dataset.key; });
    }
    btns.forEach(function (b) { b.addEventListener('click', function () { select(b, true); }); });
    var inicial = btns.filter(function (b) { return b.getAttribute('aria-selected') === 'true'; })[0] || btns[0];
    select(inicial, false);
    var reajustar = function () { move($('[aria-selected="true"]', seg)); };
    window.addEventListener('resize', reajustar);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(reajustar);
  }
  $$('.seg').forEach(initSeg);

  /* ───── Inicio: mazo de tarjetas que rota solo ───── */
  var deck = $('#deck'), dots = $('#dots');
  if (deck && dots) {
    var cards = $$('.card', deck), cur = 0, timer;
    dots.innerHTML = cards.map(function () { return '<i></i>'; }).join('');
    var show = function (n) {
      cur = (n + cards.length) % cards.length;
      cards.forEach(function (c, k) { c.dataset.p = (k - cur + cards.length) % cards.length; });
      $$('i', dots).forEach(function (d, k) {
        d.classList.remove('on');
        if (k === cur) { void d.offsetWidth; d.classList.add('on'); }
      });
      clearTimeout(timer);
      if (cards.length > 1) timer = setTimeout(function () { show(cur + 1); }, 4500);
    };
    deck.addEventListener('click', function () { show(cur + 1); });
    show(0);
  }

  /* ───── Filas de resultados que se expanden ───── */
  var rows = $$('.row');
  rows.forEach(function (r) {
    r.addEventListener('click', function (e) {
      if (e.target.closest('a')) return;
      var abierta = r.classList.contains('open');
      $$('.row.open', r.parentNode).forEach(function (x) { x.classList.remove('open'); });
      if (!abierta) r.classList.add('open');
    });
  });

  /* ───── Cuenta regresiva al próximo partido ───── */
  var cd = $('#cd');
  if (cd && cd.dataset.objetivo) {
    var objetivo = new Date(cd.dataset.objetivo).getTime();
    var nums = $$('b', cd);
    var tick = function () {
      var d = Math.max(0, objetivo - Date.now());
      var v = [Math.floor(d / 864e5), Math.floor(d / 36e5) % 24, Math.floor(d / 6e4) % 60, Math.floor(d / 1e3) % 60];
      nums.forEach(function (e, k) { e.textContent = String(v[k]).padStart(2, '0'); });
    };
    tick();
    setInterval(tick, 1000);
  }

  /* ───── Barra inferior del celular: marca la sección visible en el inicio ───── */
  var secciones = $$('[data-dock]');
  if (secciones.length && 'IntersectionObserver' in window) {
    var dockLinks = $$('.dock a');
    var obs = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        dockLinks.forEach(function (a) { a.classList.toggle('on', a.dataset.dock === e.target.dataset.dock); });
      });
    }, { threshold: 0.35 });
    secciones.forEach(function (s) { obs.observe(s); });
  }

  /* ───── Avisos que se cierran solos ───── */
  $$('.flash').forEach(function (f) {
    setTimeout(function () { f.classList.add('out'); setTimeout(function () { f.remove(); }, 500); }, 4200);
  });

  /* ───── Formularios de acceso: ver/ocultar contraseña y coincidencia ───── */
  $$('.eye').forEach(function (b) {
    b.addEventListener('click', function () {
      var input = document.getElementById(b.dataset.target);
      if (!input) return;
      var oculto = input.type === 'password';
      input.type = oculto ? 'text' : 'password';
      b.setAttribute('aria-label', oculto ? 'Ocultar contraseña' : 'Mostrar contraseña');
    });
  });
  var pw = $('#password'), vpw = $('#verifypassword'), hint = $('#password-hint');
  if (pw && vpw && hint) {
    var check = function () {
      if (!pw.value && !vpw.value) { hint.textContent = ''; hint.className = 'hint'; pw.className = vpw.className = ''; return; }
      var ok = pw.value === vpw.value;
      hint.textContent = ok ? 'Las contraseñas coinciden' : 'Las contraseñas no coinciden';
      hint.className = 'hint ' + (ok ? 'match' : 'no-match');
      [pw, vpw].forEach(function (i) { i.classList.toggle('is-valid', ok); i.classList.toggle('is-invalid', !ok); });
    };
    pw.addEventListener('input', check);
    vpw.addEventListener('input', check);
  }
})();
