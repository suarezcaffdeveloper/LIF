/* Tema Reflectores · comportamiento. Cada bloque se activa solo si su elemento existe en la página. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ───── Nav: vidrio al scrollear, se esconde al bajar y reaparece al subir ───── */
  var nav = $('#nav'), sheet = $('#sheet'), lastY = 0;
  window.addEventListener('scroll', function () {
    var y = window.scrollY;
    if (!nav) return;
    nav.classList.toggle('scrolled', y > 40);
    nav.classList.toggle('hide', y > lastY && y > 420 && !(sheet && sheet.classList.contains('open')));
    lastY = y;
  }, { passive: true });

  /* Indicador que sigue al mouse dentro del nav */
  var links = $('#links'), ind = links && $('.ind', links);
  if (links && ind) {
    $$('.nav-item', links).forEach(function (it) {
      it.addEventListener('mouseenter', function () {
        ind.style.opacity = 1;
        ind.style.left = it.offsetLeft + 'px';
        ind.style.width = it.offsetWidth + 'px';
      });
    });
    links.addEventListener('mouseleave', function () { ind.style.opacity = 0; });
  }

  /* Menú móvil a pantalla completa */
  var burger = $('#burger');
  function cerrarMenu() {
    if (!sheet || !burger) return;
    sheet.classList.remove('open');
    burger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }
  if (burger && sheet) {
    burger.addEventListener('click', function () {
      var abierto = sheet.classList.toggle('open');
      burger.setAttribute('aria-expanded', abierto ? 'true' : 'false');
      document.body.style.overflow = abierto ? 'hidden' : '';
    });
    $$('a', sheet).forEach(function (a) { a.addEventListener('click', cerrarMenu); });
    window.addEventListener('keydown', function (e) { if (e.key === 'Escape') cerrarMenu(); });
  }

  /* ───── Hero: la escena se mueve con el mouse y el scroll ───── */
  var scene = $('#scene');
  if (scene) {
    window.addEventListener('mousemove', function (e) {
      if (window.scrollY > window.innerHeight) return;
      var x = (e.clientX / innerWidth - 0.5) * -26, y = (e.clientY / innerHeight - 0.5) * -16;
      scene.style.transform = 'translate(' + x + 'px,' + (y + window.scrollY * 0.18) + 'px)';
    });
    window.addEventListener('scroll', function () {
      if (window.scrollY < window.innerHeight) scene.style.transform = 'translate(0,' + (window.scrollY * 0.18) + 'px)';
    }, { passive: true });
  }

  /* ───── Barras de puntos de la tabla ───── */
  function animarBarras(raiz) {
    $$('.ptsbar i[data-w]', raiz || document).forEach(function (i) {
      i.style.width = '0px';
      requestAnimationFrame(function () { requestAnimationFrame(function () { i.style.width = i.dataset.w + 'px'; }); });
    });
  }

  /* ───── Sliders de fixture: arrastrar, flechas y barra de progreso ───── */
  function initRail(wrap) {
    var rail = $('.rail', wrap), prog = $('.rail-progress i', wrap);
    if (!rail) return;
    function upd() {
      var max = rail.scrollWidth - rail.clientWidth;
      if (!rail.scrollWidth || !rail.clientWidth) return;
      var r = rail.clientWidth / rail.scrollWidth;
      if (prog) {
        prog.style.width = (r * 100) + '%';
        prog.style.marginLeft = (max > 0 ? rail.scrollLeft / max * (100 - r * 100) : 0) + '%';
      }
    }
    rail.addEventListener('scroll', upd, { passive: true });
    var n = $('.circ.next', wrap), p = $('.circ.prev', wrap);
    if (n) n.addEventListener('click', function () { rail.scrollBy({ left: 360, behavior: 'smooth' }); });
    if (p) p.addEventListener('click', function () { rail.scrollBy({ left: -360, behavior: 'smooth' }); });
    var down = false, sx = 0, sl = 0;
    rail.addEventListener('pointerdown', function (e) {
      if (e.pointerType !== 'mouse') return;
      down = true; sx = e.clientX; sl = rail.scrollLeft; rail.classList.add('drag');
    });
    window.addEventListener('pointermove', function (e) { if (down) rail.scrollLeft = sl - (e.clientX - sx); });
    window.addEventListener('pointerup', function () { down = false; rail.classList.remove('drag'); });
    wrap._upd = upd;
    upd();
  }
  $$('.railwrap').forEach(initRail);

  /* ───── Pestañas con pieza deslizante que muestran un panel por grupo ─────
     <div class="tabs" data-group="tabla"><button data-key="primera" aria-selected="true">…</button></div>
     <div class="pane" data-group="tabla" data-key="primera">…</div>                                  */
  function initTabs(tabs) {
    var group = tabs.dataset.group;
    var btns = $$('button', tabs);
    if (!btns.length) return;
    var th = document.createElement('span');
    th.className = 'thumb';
    tabs.insertBefore(th, tabs.firstChild);
    function move(b) { th.style.left = b.offsetLeft + 'px'; th.style.width = b.offsetWidth + 'px'; }
    function select(b, animar) {
      btns.forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      move(b);
      tabs.scrollTo({ left: b.offsetLeft - (tabs.clientWidth - b.offsetWidth) / 2, behavior: animar ? 'smooth' : 'auto' });
      $$('.pane[data-group="' + group + '"]').forEach(function (p) {
        var mostrar = p.dataset.key === b.dataset.key;
        p.hidden = !mostrar;
        if (mostrar) {
          $$('.railwrap', p).forEach(function (w) { if (w._upd) w._upd(); });
          if (animar) animarBarras(p);
        }
      });
    }
    btns.forEach(function (b) { b.addEventListener('click', function () { select(b, true); }); });
    var inicial = btns.filter(function (b) { return b.getAttribute('aria-selected') === 'true'; })[0] || btns[0];
    select(inicial, false);
    var reajustar = function () { move($('[aria-selected="true"]', tabs)); };
    window.addEventListener('resize', reajustar);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(reajustar);
  }
  $$('.tabs[data-group]').forEach(initTabs);
  animarBarras();

  /* ───── Contadores que suben al entrar en pantalla ───── */
  var stats = $('#stats');
  if (stats && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        $$('.n', e.target).forEach(function (n) {
          var to = +n.dataset.to, t0 = performance.now();
          (function f(t) {
            var p = Math.min((t - t0) / 1600, 1);
            n.textContent = Math.round(to * (1 - Math.pow(1 - p, 4)));
            if (p < 1) requestAnimationFrame(f);
          })(t0);
        });
      });
    }, { threshold: 0.4 });
    io.observe(stats);
  } else if (stats) {
    $$('.n', stats).forEach(function (n) { n.textContent = n.dataset.to; });
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
