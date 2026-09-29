/* Tema Tribuna · comportamiento. Cada bloque se activa solo si su elemento existe en la página. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ───── Nav: se compacta al scrollear ───── */
  var nav = $('#nav');
  function onScroll() {
    if (nav) nav.classList.toggle('scrolled', window.scrollY > 40);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ───── La ola: se pausa cuando la tribuna no se ve ───── */
  var grada = $('.grada');
  if (grada && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        grada.style.animationPlayState = e.isIntersecting ? 'running' : 'paused';
        $$('.hincha', grada).forEach(function (h) {
          h.style.animationPlayState = e.isIntersecting ? 'running' : 'paused';
        });
      });
    }, { threshold: 0.05 }).observe(grada);
    if (reduce) $$('.hincha', grada).forEach(function (h) { h.style.animation = 'none'; });
  }

  /* ───── Reveal on scroll: .rv aparece con fade-up ───── */
  var rv = $$('.rv');
  if (rv.length && 'IntersectionObserver' in window) {
    var obsRv = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); obsRv.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    rv.forEach(function (el) { obsRv.observe(el); });
  } else {
    rv.forEach(function (el) { el.classList.add('in'); });
  }

  /* ───── Pestañas: muestran un panel por grupo ─────
     <div class="tabs" data-group="tabla"><button data-key="primera" aria-selected="true">…</button></div>
     <div class="pane" data-group="tabla" data-key="primera">…</div>                     */
  function initTabs(tabs) {
    var group = tabs.dataset.group;
    if (!group) return;
    var btns = $$('button', tabs);
    if (!btns.length) return;
    function select(b, scroll) {
      btns.forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      if (scroll) tabs.scrollTo({ left: b.offsetLeft - (tabs.clientWidth - b.offsetWidth) / 2, behavior: 'smooth' });
      $$('.pane[data-group="' + group + '"]').forEach(function (p) { p.hidden = p.dataset.key !== b.dataset.key; });
    }
    btns.forEach(function (b) { b.addEventListener('click', function () { select(b, true); }); });
    var inicial = btns.filter(function (b) { return b.getAttribute('aria-selected') === 'true'; })[0] || btns[0];
    select(inicial, false);
  }
  $$('.tabs[data-group]').forEach(initTabs);

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

  /* ───── Barra inferior del celular: marca la sección visible ───── */
  var secciones = $$('[data-dock]');
  if (secciones.length && 'IntersectionObserver' in window) {
    var dockLinks = $$('.dock a');
    var obs = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        dockLinks.forEach(function (a) { a.classList.toggle('on', a.dataset.dock === e.target.dataset.dock); });
      });
    }, { threshold: 0.3 });
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
