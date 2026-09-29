/* Tema Marcador · comportamiento. Cada bloque se activa solo si su elemento existe en la página. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ───── Pestañas con subrayado LED que muestran un panel por grupo ─────
     <div class="tabs" data-group="tabla"><button data-key="primera" aria-selected="true">…</button></div>
     <div class="pane" data-group="tabla" data-key="primera">…</div>                                  */
  function llenarBarras(raiz) {
    $$('[data-w]', raiz || document).forEach(function (el) { el.style.width = '0%'; });
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        $$('[data-w]', raiz || document).forEach(function (el) { el.style.width = el.dataset.w + '%'; });
      });
    });
  }
  function iniciarTabs(tabs) {
    var grupo = tabs.dataset.group, botones = $$('button', tabs);
    if (!botones.length) return;
    var tinta = document.createElement('span');
    tinta.className = 'ink';
    tabs.appendChild(tinta);
    function mover(b) { tinta.style.left = b.offsetLeft + 'px'; tinta.style.width = b.offsetWidth + 'px'; }
    function elegir(b, animar) {
      botones.forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      mover(b);
      tabs.scrollTo({ left: b.offsetLeft - (tabs.clientWidth - b.offsetWidth) / 2, behavior: animar ? 'smooth' : 'auto' });
      $$('.pane[data-group="' + grupo + '"]').forEach(function (p) {
        var ver = p.dataset.key === b.dataset.key;
        p.hidden = !ver;
        if (ver && animar) llenarBarras(p);
      });
    }
    botones.forEach(function (b) { b.addEventListener('click', function () { elegir(b, true); }); });
    var inicial = botones.filter(function (b) { return b.getAttribute('aria-selected') === 'true'; })[0] || botones[0];
    elegir(inicial, false);
    var reajustar = function () { mover($('[aria-selected="true"]', tabs)); };
    window.addEventListener('resize', reajustar);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(reajustar);
  }
  $$('.tabs[data-group]').forEach(iniciarTabs);

  /* ───── Barras (goleadores y puntos): se llenan al entrar en pantalla ───── */
  if ('IntersectionObserver' in window) {
    var visto = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        visto.unobserve(e.target);
        llenarBarras(e.target);
      });
    }, { threshold: 0.2 });
    $$('.barras, .tabla-wrap').forEach(function (b) { visto.observe(b); });
  } else {
    llenarBarras();
  }

  /* ───── Marcador: los dígitos se encienden y la cuenta regresiva corre ───── */
  var marcador = $('#marcador');
  if (marcador) requestAnimationFrame(function () { marcador.classList.add('on'); });
  var cuenta = $('#cuenta');
  if (cuenta && cuenta.dataset.objetivo) {
    var objetivo = new Date(cuenta.dataset.objetivo).getTime();
    var digs = $$('.dig', cuenta), previos = [];
    var tic = function () {
      var d = Math.max(0, objetivo - Date.now());
      var v = [Math.floor(d / 864e5), Math.floor(d / 36e5) % 24, Math.floor(d / 6e4) % 60, Math.floor(d / 1e3) % 60];
      digs.forEach(function (el, k) {
        var t = String(v[k]).padStart(2, '0');
        if (previos[k] !== t) {
          el.textContent = t;
          if (previos[k] !== undefined) { el.classList.remove('tic'); void el.offsetWidth; el.classList.add('tic'); }
          previos[k] = t;
        }
      });
    };
    tic();
    setInterval(tic, 1000);
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
      [pw, vpw].forEach(function (i) { i.classList.toggle('is-valid', ok); i.classList.toggle('is-invalid', !ok); });
    };
    pw.addEventListener('input', revisar);
    vpw.addEventListener('input', revisar);
  }
})();
