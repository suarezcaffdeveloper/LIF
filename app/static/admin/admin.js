/* ElTablón · panel de administración
   - Apariencia: claro / oscuro / auto, guardada en una cookie (la lee el servidor para no parpadear).
   - Menú lateral como cajón en celular.
   - Avisos: una sola API, ElTablonAdmin.aviso(tipo, texto). Lee también los mensajes flash del servidor. */
(function () {
  'use strict';
  var doc = document;
  var raiz = doc.documentElement;

  /* ── Apariencia ── */
  function guardarTema(valor) {
    var cookie = 'admin_tema=' + (valor === 'auto' ? '; max-age=0' : valor + '; max-age=31536000');
    doc.cookie = cookie + '; path=/; SameSite=Lax';
  }
  function aplicarTema(valor) {
    raiz.setAttribute('data-tema', valor);
    doc.querySelectorAll('[data-tema-set]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-tema-set') === valor ? 'true' : 'false');
    });
    doc.dispatchEvent(new CustomEvent('admin:tema', { detail: valor }));
  }
  doc.addEventListener('click', function (e) {
    var b = e.target.closest('[data-tema-set]');
    if (!b) return;
    var valor = b.getAttribute('data-tema-set');
    guardarTema(valor);
    aplicarTema(valor);
  });

  /* ── Menú lateral (celular) ── */
  function menu(abrir) {
    doc.body.classList.toggle('ad-menu-abierto', abrir);
    var burger = doc.querySelector('[data-abrir-menu]');
    if (burger) burger.setAttribute('aria-expanded', abrir ? 'true' : 'false');
  }
  doc.addEventListener('click', function (e) {
    if (e.target.closest('[data-abrir-menu]')) return menu(true);
    if (e.target.closest('[data-cerrar-menu]')) return menu(false);
    if (e.target.closest('.ad-nav-item') && doc.body.classList.contains('ad-menu-abierto')) menu(false);
  });
  doc.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') menu(false);
  });

  /* ── Avisos ── */
  var TIPOS = { success: 'ok', ok: 'ok', danger: 'danger', error: 'danger', warning: 'warn', warn: 'warn', info: 'info', message: 'info' };
  var ICONOS = { ok: 'i-ok', danger: 'i-error', warn: 'i-alerta', info: 'i-info' };

  function aviso(tipo, texto, ms) {
    var caja = doc.getElementById('ad-avisos');
    if (!caja || !texto) return null;
    var t = TIPOS[tipo] || 'info';
    var el = doc.createElement('div');
    el.className = 'ad-aviso';
    el.setAttribute('data-tipo', t);
    el.setAttribute('role', t === 'danger' ? 'alert' : 'status');
    el.innerHTML = '<svg class="ad-i"><use href="#' + ICONOS[t] + '"/></svg><p></p>' +
      '<button type="button" aria-label="Cerrar aviso"><svg class="ad-i"><use href="#i-cerrar"/></svg></button>';
    el.querySelector('p').textContent = String(texto);
    function cerrar() {
      if (!el.parentNode) return;
      el.classList.add('saliendo');
      setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 220);
    }
    el.querySelector('button').addEventListener('click', cerrar);
    caja.appendChild(el);
    while (caja.children.length > 4) caja.removeChild(caja.firstChild);
    setTimeout(cerrar, ms || (t === 'danger' ? 9000 : 6000));
    return el;
  }

  /* Mensajes flash que dejó el servidor en la página */
  function avisosDelServidor() {
    var nodo = doc.getElementById('ad-flashes');
    if (!nodo) return;
    var lista = [];
    try { lista = JSON.parse(nodo.textContent || '[]'); } catch (_) { /* sin avisos */ }
    lista.forEach(function (par) { aviso(par[0], par[1]); });
  }

  /* Confirmación con el diseño del panel; devuelve una promesa (true/false) */
  function confirmar(opciones) {
    var o = opciones || {};
    return new Promise(function (resolver) {
      var fondo = doc.createElement('div');
      fondo.className = 'ad-modal-fondo is-abierto';
      fondo.innerHTML = '<div class="ad-modal" role="dialog" aria-modal="true"><h2></h2><p></p>' +
        '<div class="ad-modal-acciones"><button type="button" class="ad-btn" data-no></button>' +
        '<button type="button" class="ad-btn ad-btn-primario" data-si></button></div></div>';
      fondo.querySelector('h2').textContent = o.titulo || '¿Confirmás la acción?';
      fondo.querySelector('p').textContent = o.texto || '';
      fondo.querySelector('[data-no]').textContent = o.cancelar || 'Cancelar';
      var si = fondo.querySelector('[data-si]');
      si.textContent = o.aceptar || 'Confirmar';
      if (o.peligro) si.className = 'ad-btn ad-btn-peligro';
      function fin(valor) { doc.removeEventListener('keydown', teclas); fondo.remove(); resolver(valor); }
      function teclas(e) { if (e.key === 'Escape') fin(false); }
      fondo.addEventListener('click', function (e) { if (e.target === fondo) fin(false); });
      fondo.querySelector('[data-no]').addEventListener('click', function () { fin(false); });
      si.addEventListener('click', function () { fin(true); });
      doc.addEventListener('keydown', teclas);
      doc.body.appendChild(fondo);
      si.focus();
    });
  }

  window.ElTablonAdmin = { aviso: aviso, confirmar: confirmar, tema: aplicarTema };

  /* Alias de las funciones que tenía cada pantalla: (mensaje, tipo) */
  window.mostrarFlash = function (msg, tipo) { aviso(tipo || 'success', msg); };
  window.showFlash = window.mostrarFlash;

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', avisosDelServidor);
  else avisosDelServidor();
})();
