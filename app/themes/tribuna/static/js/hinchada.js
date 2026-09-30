/* Tema Tribuna · la hinchada.
   Dibuja en un <canvas> una tribuna realista: personas con hombros, cuello y pelo, brazos articulados,
   telas simuladas (banderas y trapos con pliegues y sombreado), bengalas con humo, papelitos,
   perspectiva atmosférica (desenfoque + bruma) y grano.
   Uso:  <canvas class="hinchada" data-variante="pie|hero|auth" data-texto="LIF" aria-hidden="true"></canvas>
   Los colores salen de las variables CSS del tema (--azul, --amarillo, --tinta, --fondo…): cada liga tiene su hinchada.
   Variantes:  pie  → la ola, sobre el footer
               hero → sin ola: festejo, banderas al viento, humo de bengalas y papelitos
               auth → tribuna sobre el fondo azul del login */
(function () {
  'use strict';
  var canvases = Array.prototype.slice.call(document.querySelectorAll('canvas.hinchada'));
  if (!canvases.length) return;

  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var TAU = Math.PI * 2, PI = Math.PI;

  /* ───── Utilidades ───── */
  function rng(seed) {
    var s = seed >>> 0;
    return function () {
      s = (s + 0x6D2B79F5) >>> 0;
      var t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function frac(v) { return v - Math.floor(v); }
  function smooth(x) { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); }
  function mix(a, b, t) { return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]; }
  function rgba(c, a) { return 'rgba(' + Math.round(c[0]) + ',' + Math.round(c[1]) + ',' + Math.round(c[2]) + ',' + (a == null ? 1 : +a.toFixed(3)) + ')'; }
  function pickw(list, r) {
    var tot = 0, i;
    for (i = 0; i < list.length; i++) tot += list[i][1];
    var v = r() * tot;
    for (i = 0; i < list.length; i++) { v -= list[i][1]; if (v <= 0) return list[i][0]; }
    return list[list.length - 1][0];
  }
  function texture(w, h, fn) {
    var c = document.createElement('canvas');
    c.width = w; c.height = h;
    fn(c.getContext('2d'), w, h);
    return c;
  }
  /* Lee una variable CSS y la devuelve como [r,g,b] (soporta hex, rgb() y color-mix()) */
  function leerColor(nombre, respaldo) {
    var p = document.createElement('i');
    p.style.cssText = 'position:absolute;visibility:hidden;color:var(' + nombre + ',' + respaldo + ')';
    document.body.appendChild(p);
    var v = getComputedStyle(p).color;
    p.remove();
    var n = v.match(/[\d.]+/g) || [];
    if (/^color\(/.test(v)) return [n[0] * 255, n[1] * 255, n[2] * 255];
    return n.length >= 3 ? [+n[0], +n[1], +n[2]] : [13, 18, 25];
  }

  /* trama de la tela + luz suave: la textura deja de ser un color plano */
  function weave(g, w, h) {
    var x, y;
    g.save();
    g.globalAlpha = 0.07;
    g.fillStyle = '#000';
    for (y = 0; y < h; y += 2) g.fillRect(0, y, w, 1);
    for (x = 0; x < w; x += 2) g.fillRect(x, 0, 1, h);
    g.restore();
    var gr = g.createLinearGradient(0, 0, 0, h);
    gr.addColorStop(0, 'rgba(255,255,255,.12)');
    gr.addColorStop(0.5, 'rgba(0,0,0,0)');
    gr.addColorStop(1, 'rgba(0,0,0,.16)');
    g.fillStyle = gr;
    g.fillRect(0, 0, w, h);
  }
  function estrella(g, cx, cy, r, col) {
    g.fillStyle = col;
    g.beginPath();
    for (var i = 0; i < 10; i++) {
      var rr = i % 2 ? r * 0.42 : r, a = -PI / 2 + i * PI / 5;
      g[i ? 'lineTo' : 'moveTo'](cx + Math.cos(a) * rr, cy + Math.sin(a) * rr);
    }
    g.closePath();
    g.fill();
  }

  /* ───── Tela ───── */
  function cloth(g, dpr, tex, top, bot, shade, dims, litA) {
    var n = top.length - 1, tw = tex.width, th = tex.height, sw = tw / n, i;
    for (i = 0; i < n; i++) {
      var sx = i * sw, ax = top[i][0], ay = top[i][1];
      var a = (top[i + 1][0] - ax) / sw, b = (top[i + 1][1] - ay) / sw;
      var c = (bot[i][0] - ax) / th, d = (bot[i][1] - ay) / th;
      g.setTransform(dpr * a, dpr * b, dpr * c, dpr * d, dpr * (ax - a * sx), dpr * (ay - b * sx));
      var ww = Math.min(sw + 0.9, tw - sx);
      g.drawImage(tex, sx, 0, ww, th, sx, 0, ww, th);
    }
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    for (i = 0; i < n; i++) {
      var s = (shade[i] + shade[i + 1]) / 2;
      if (Math.abs(s) < 0.01) continue;
      g.beginPath();
      g.moveTo(top[i][0], top[i][1]);
      g.lineTo(top[i + 1][0], top[i + 1][1]);
      g.lineTo(bot[i + 1][0], bot[i + 1][1]);
      g.lineTo(bot[i][0], bot[i][1]);
      g.closePath();
      g.fillStyle = s > 0 ? 'rgba(8,12,30,' + s.toFixed(3) + ')' : 'rgba(255,255,255,' + (-s * litA).toFixed(3) + ')';
      g.fill();
    }
    for (var k = 0; k < dims.length; k++) {
      if (dims[k][1] < 0.01) continue;
      g.beginPath();
      g.moveTo(top[0][0], top[0][1]);
      for (i = 1; i <= n; i++) g.lineTo(top[i][0], top[i][1]);
      for (i = n; i >= 0; i--) g.lineTo(bot[i][0], bot[i][1]);
      g.closePath();
      g.fillStyle = rgba(dims[k][0], dims[k][1]);
      g.fill();
    }
  }

  /* bandera en mástil: ondas que viajan hacia la punta, pliegues secundarios, se comprime con la onda */
  function flagMesh(x, y, w, h, dir, t, o) {
    var n = 28, top = [], bot = [], shade = [], px = x, i, amp = o.amp * h;
    function z(u) {
      var env = 0.1 + 0.9 * Math.min(1, u * 1.5);
      return (Math.sin(o.k * u - o.speed * t + o.phase) * 0.72 + Math.sin(o.k * 2.3 * u - o.speed * 1.6 * t + o.phase * 1.7) * 0.28) * amp * env;
    }
    for (i = 0; i <= n; i++) {
      var u = i / n, zi = z(u);
      var sl = (z(Math.min(1, u + 0.02)) - z(Math.max(0, u - 0.02))) / (0.04 * w);
      if (i > 0) px += dir * (w / n) / Math.sqrt(1 + sl * sl);
      var dr = o.droop * h * u * u * 3.2;
      top.push([px, y + zi * 0.55 + dr]);
      bot.push([px + dir * zi * 0.06, y + h * (1 - 0.04 * u) + zi * 0.75 + dr]);
      shade.push(clamp(sl * dir * o.shadeK, -0.55, 0.65));
    }
    return { top: top, bot: bot, shade: shade };
  }

  /* trapo sostenido por dos personas: borde superior con comba, ondulación que recorre la tela */
  function bannerMesh(p0, p1, h, t, o) {
    var n = 32, top = [], bot = [], shade = [], i;
    for (i = 0; i <= n; i++) {
      var u = i / n, ph = o.k * u - o.speed * t + o.phase;
      var wv = Math.sin(ph) * 0.75 + Math.sin(ph * 2.2 + 1.3 + t * 0.4) * 0.25;
      var dv = Math.cos(ph) * 0.75;
      var sag = Math.sin(u * PI) * o.sag * h;
      var x = lerp(p0[0], p1[0], u) + Math.cos(ph) * o.amp * h * 0.16;
      var y = lerp(p0[1], p1[1], u) + sag + wv * o.amp * h * 0.10;
      top.push([x, y]);
      bot.push([x + wv * o.amp * h * 0.05, y + h * (1 + 0.05 * Math.sin(ph * 0.7)) + wv * o.amp * h * 0.45 + sag * 0.5]);
      shade.push(clamp(dv * o.shadeK, -0.5, 0.6));
    }
    return { top: top, bot: bot, shade: shade };
  }

  /* brazo de dos huesos: el codo se calcula para que el gesto sea natural */
  function arm(g, sx, sy, tx, ty, l1, l2, side, wUp, wFo, cSleeve, cSkin) {
    var dx = tx - sx, dy = ty - sy, d = Math.sqrt(dx * dx + dy * dy) || 0.001;
    var maxd = (l1 + l2) * 0.985;
    if (d > maxd) { tx = sx + dx / d * maxd; ty = sy + dy / d * maxd; dx = tx - sx; dy = ty - sy; d = maxd; }
    var a = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
    var hh = Math.sqrt(Math.max(0, l1 * l1 - a * a));
    var ux = dx / d, uy = dy / d;
    var ex = sx + ux * a - uy * hh * side, ey = sy + uy * a + ux * hh * side;
    g.lineCap = 'round';
    g.strokeStyle = cSleeve; g.lineWidth = wUp;
    g.beginPath(); g.moveTo(sx, sy); g.lineTo(ex, ey); g.stroke();
    g.strokeStyle = cSkin; g.lineWidth = wFo;
    g.beginPath(); g.moveTo(ex, ey); g.lineTo(tx, ty); g.stroke();
    g.fillStyle = cSkin;
    g.beginPath(); g.arc(tx, ty, wFo * 0.62, 0, TAU); g.fill();
    return [tx, ty];
  }

  /* ───── Paletas y telas por liga ───── */
  function paleta(canvas, fondoVar) {
    var P = {
      tinta: leerColor('--tinta', '#0D1219'),
      fondo: leerColor(fondoVar || '--fondo', '#EFF1F5'),
      azul: leerColor('--azul', '#2B4BF2'),
      azulOsc: leerColor('--azul-osc', '#1B31B8'),
      amarillo: leerColor('--amarillo', '#FFD23F'),
      blanco: [255, 255, 255],
      texto: (canvas.dataset.texto || 'LIF').toUpperCase().slice(0, 6)
    };
    var f = (getComputedStyle(document.documentElement).getPropertyValue('--f-display') || '').trim();
    P.fuente = f || 'Anton, Impact, "Arial Black", sans-serif';
    return P;
  }

  function telas(P) {
    var A = rgba(P.azul), AO = rgba(P.azulOsc), Y = rgba(P.amarillo), B = '#f6f7fb';
    function texto(g, txt, cx, cy, size, maxW, col) {
      g.textAlign = 'center'; g.textBaseline = 'middle';
      g.font = '400 ' + size + 'px ' + P.fuente;
      var w = g.measureText(txt).width;
      if (w > maxW) { size = size * maxW / w; g.font = '400 ' + size + 'px ' + P.fuente; }
      g.fillStyle = col; g.fillText(txt, cx, cy);
    }
    function bandas(cols, txt, colTxt) {
      return texture(360, 230, function (g, w, h) {
        for (var i = 0; i < cols.length; i++) { g.fillStyle = cols[i]; g.fillRect(0, Math.floor(h * i / cols.length), w, Math.ceil(h / cols.length) + 1); }
        if (txt) texto(g, txt, w / 2, h / 2 + 4, 92, w * 0.8, colTxt);
        weave(g, w, h);
      });
    }
    var T = {};
    T.b1 = bandas([A, B, A]);
    T.b2 = texture(360, 230, function (g, w, h) {
      g.fillStyle = Y; g.fillRect(0, 0, w, h);
      g.fillStyle = A; g.fillRect(0, h * 0.34, w, h * 0.32);
      weave(g, w, h);
    });
    T.b3 = bandas([B, B], P.texto, A);
    T.b4 = bandas([AO, AO], P.texto, Y);
    T.trapoBlanco = texture(720, 150, function (g, w, h) {
      g.fillStyle = B; g.fillRect(0, 0, w, h);
      g.fillStyle = A; g.fillRect(0, 0, w, 18);
      g.fillStyle = Y; g.fillRect(0, h - 28, w, 28);
      texto(g, P.texto, w / 2, h / 2 - 3, 112, w * 0.5, AO);
      estrella(g, 110, h / 2 - 3, 24, A); estrella(g, w - 110, h / 2 - 3, 24, A);
      weave(g, w, h);
    });
    T.trapoAzul = texture(720, 150, function (g, w, h) {
      var gr = g.createLinearGradient(0, 0, w, h);
      gr.addColorStop(0, rgba(mix(P.azul, P.blanco, 0.12))); gr.addColorStop(1, AO);
      g.fillStyle = gr; g.fillRect(0, 0, w, h);
      g.strokeStyle = Y; g.lineWidth = 7; g.strokeRect(9, 9, w - 18, h - 18);
      texto(g, P.texto, w / 2 + 5, h / 2 + 9, 120, w * 0.5, Y);
      texto(g, P.texto, w / 2, h / 2 + 4, 120, w * 0.5, '#ffffff');
      weave(g, w, h);
    });
    return T;
  }

  function gente(P) {
    return {
      shirts: [[P.azul, 3], [P.blanco, 2.5], [P.amarillo, 2], [P.azulOsc, 1.6], [P.tinta, 1.6], [[154, 163, 181], 1], [mix(P.azul, P.blanco, 0.5), 0.9]],
      hairs: [[[26, 20, 18], 5], [[59, 42, 30], 3], [[107, 74, 43], 2], [[184, 150, 90], 1], [[154, 154, 157], 0.7]],
      skins: [[[224, 172, 130], 3], [[198, 139, 98], 3], [[141, 90, 59], 2], [[240, 201, 164], 2]],
      scarves: [[[P.azul, P.blanco], 1], [[P.amarillo, P.azul], 1]]
    };
  }

  /* ───── Variantes ───── */
  var VARIANTES = {
    /* footer: la ola, baja de altura, se funde con la página y con la base oscura */
    pie: function (P) {
      var T = telas(P), base = gente(P);
      return {
        seed: 5, rows: 5, hr: [0.026, 0.07], top: 0.17, bottom: 0.50, minW: 700,
        blur: [1.3, 0.8, 0.35, 0, 0], haze: [0.7, 0],
        shadowAmt: 0.08, lit: 0.42, side: 'left', rim: 0.55, rimA0: PI * 0.95, rimA1: PI * 1.62,
        clothLit: 0.55, clothShadow: 0.2, shadeK: 0.55, lean: 0.12, swing: 0.07, swingSpeed: 1.05,
        olaK: 1.0, olaT: 7.5, cel: 0.42, wind: 18, grain: 0.05, dprMax: 2,
        colors: { haze: P.fondo, shadow: mix(P.tinta, P.azulOsc, 0.25), light: [255, 240, 207] },
        shirts: base.shirts, hairs: base.hairs, skins: base.skins, scarves: base.scarves,
        flags: [
          { row: 3, at: 0.10, tex: T.b1, w: 7, amp: 0.3, k: 6.2, speed: 5.0, len: 4.6, dir: 1 },
          { row: 3, at: 0.93, tex: T.b2, w: 7, amp: 0.3, k: 6.7, speed: 5.5, len: 4.6, dir: 1 },
          { row: 2, at: 0.30, tex: T.b3, w: 6.5, amp: 0.3, k: 6.0, speed: 4.8, len: 4.4, dir: 1 },
          { row: 2, at: 0.76, tex: T.b4, w: 6.5, amp: 0.3, k: 6.5, speed: 5.3, len: 4.4, dir: 1 },
          { row: 1, at: 0.55, tex: T.b2, w: 6, amp: 0.3, k: 6.4, speed: 5.1, len: 4.2, dir: 1 }
        ],
        trapos: [{ row: 4, at: 0.40, span: 7, aspect: 4.8, tex: T.trapoBlanco, k: 6.5, speed: 3.8, amp: 0.4, sag: 0.11 }],
        bengalas: [],
        overlay: function (g, W, H) {
          /* la grada se va oscureciendo hacia abajo, donde va el texto del footer */
          var b = g.createLinearGradient(0, H * 0.4, 0, H);
          b.addColorStop(0, rgba(P.tinta, 0)); b.addColorStop(0.45, rgba(P.tinta, 0.9)); b.addColorStop(0.75, rgba(P.tinta, 0.97)); b.addColorStop(1, rgba(P.tinta, 1));
          g.fillStyle = b; g.fillRect(0, H * 0.4, W, H * 0.6 + 1);
        }
      };
    },

    /* hero: sin ola. Festejo continuo, banderas que se agitan, humo de bengalas y papelitos */
    hero: function (P) {
      var T = telas(P), base = gente(P);
      var r = rng(31), papeles = [], i;
      var cols = [P.azul, P.amarillo, P.azulOsc, mix(P.azul, P.blanco, 0.4)];
      for (i = 0; i < 46; i++) papeles.push({ x: r(), y: r(), vy: 20 + r() * 34, vx: (r() - 0.5) * 16, w: 4 + r() * 4, h: 8 + r() * 6, rot: r() * TAU, giro: (r() - 0.5) * 3.2, ph: r() * TAU, col: cols[Math.floor(r() * cols.length)] });
      return {
        seed: 9, rows: 7, hr: [0.011, 0.034], top: 0.5, bottom: 0.87, minW: 0,
        blur: [2.4, 1.8, 1.2, 0.8, 0.45, 0.15, 0], haze: [0.72, 0],
        shadowAmt: 0.08, lit: 0.42, side: 'left', rim: 0.6, rimA0: PI * 0.95, rimA1: PI * 1.62,
        clothLit: 0.55, clothShadow: 0.2, shadeK: 0.55, lean: 0.14, swing: 0.22, swingSpeed: 1.9,
        ola: false, cel: 0.8, burstSpeed: 0.75, wob: 0.55, wind: 26, smokeA: 0.5, flareBlend: 'source-over', grain: 0.05, dprMax: 1.5,
        colors: { haze: P.fondo, shadow: mix(P.tinta, P.azulOsc, 0.25), light: [255, 240, 207] },
        shirts: base.shirts, hairs: base.hairs, skins: base.skins, scarves: base.scarves,
        flags: [
          { row: 6, at: 0.60, tex: T.b1, w: 8.5, amp: 0.3, k: 6.2, speed: 6.2, len: 7.2, dir: 1 },
          { row: 6, at: 0.94, tex: T.b2, w: 8.5, amp: 0.3, k: 6.7, speed: 6.6, len: 7.6, dir: 1 },
          { row: 5, at: 0.95, tex: T.b3, w: 8, amp: 0.3, k: 6.0, speed: 5.8, len: 7.2, dir: 1 },
          { row: 4, at: 0.46, tex: T.b4, w: 8, amp: 0.3, k: 6.5, speed: 6.0, len: 7.0, dir: 1 },
          { row: 4, at: 0.84, tex: T.b1, w: 7.5, amp: 0.3, k: 6.4, speed: 6.4, len: 7.0, dir: 1 },
          { row: 3, at: 0.68, tex: T.b2, w: 7, amp: 0.3, k: 6.8, speed: 6.1, len: 7.0, dir: 1 },
          { row: 2, at: 0.30, tex: T.b3, w: 6, amp: 0.3, k: 6.3, speed: 5.9, len: 6.5, dir: 1 }
        ],
        trapos: [{ row: 5, at: 0.40, span: 5, aspect: 4.8, tex: T.trapoAzul, k: 7, speed: 4.4, amp: 0.4, sag: 0.11 }],
        bengalas: [
          { row: 6, at: 0.76, col: P.azul, smoke: P.azul },
          { row: 4, at: 0.62, col: P.amarillo, smoke: mix(P.amarillo, [255, 150, 40], 0.25) }
        ],
        overlay: function (g, W, H, t) {
          for (var k = 0; k < papeles.length; k++) {
            var q = papeles[k];
            var yy = ((q.y * H + t * q.vy) % (H + 24)) - 12;
            var xx = (((q.x * W + Math.sin(t * 0.8 + q.ph) * 22 + t * q.vx) % W) + W) % W;
            g.save();
            g.translate(xx, yy); g.rotate(q.rot + t * q.giro); g.scale(1, Math.cos(t * 2.4 + q.ph));
            g.fillStyle = rgba(q.col, 0.9);
            g.fillRect(-q.w / 2, -q.h / 2, q.w, q.h);
            g.restore();
          }
        }
      };
    },

    /* login y registro: tribuna oscura sobre el fondo de marca */
    auth: function (P) {
      var T = telas(P), base = gente(P);
      return {
        seed: 11, rows: 6, hr: [0.010, 0.030], top: 0.42, bottom: 0.80, minW: 0,
        blur: [1.8, 1.2, 0.7, 0.3, 0, 0], haze: [0.7, 0.05],
        shadowAmt: 0.75, lit: 0.5, side: 'top', rim: 0.8, rimA0: PI * 1.1, rimA1: PI * 1.9,
        clothLit: 0.35, clothShadow: 0.7, shadeK: 0.6, lean: 0.14, swing: 0.08, swingSpeed: 1.1,
        olaK: 1.0, olaT: 7.5, cel: 0.42, phones: true, wind: 20, grain: 0.05, dprMax: 2,
        colors: { haze: mix(P.azul, P.azulOsc, 0.5), shadow: mix(P.tinta, P.azulOsc, 0.3), light: [255, 234, 184] },
        shirts: base.shirts, hairs: base.hairs, skins: base.skins, scarves: base.scarves,
        flags: [
          { row: 4, at: 0.16, tex: T.b1, w: 8, amp: 0.28, k: 6.4, speed: 5.4, len: 7, dir: 1 },
          { row: 4, at: 0.80, tex: T.b2, w: 8, amp: 0.28, k: 6.9, speed: 5.9, len: 7, dir: 1 },
          { row: 3, at: 0.46, tex: T.b3, w: 7.5, amp: 0.28, k: 6.0, speed: 5.0, len: 7, dir: 1 }
        ],
        trapos: [], bengalas: []
      };
    }
  };

  /* ───── Motor ───── */
  function Hinchada(canvas) {
    var nombre = canvas.dataset.variante;
    var fab = VARIANTES[nombre] || VARIANTES.hero;
    var P = paleta(canvas, nombre === 'hero' ? '--fondo-2' : nombre === 'pie' ? '--blanco' : '--fondo');
    var cfg = fab(P);
    var ctx = canvas.getContext('2d');
    var lay = document.createElement('canvas'), lctx = lay.getContext('2d');
    var canFilter = 'filter' in ctx;
    var C = cfg.colors;
    var W = 0, H = 0, dpr = 1, rows = [], flares = [], parts = [], sprites = {};
    var last = 0, raf = 0, t0 = performance.now(), running = false, visible = false;
    var noiseP = null;

    var noiseCv = texture(180, 180, function (g) {
      var im = g.createImageData(180, 180), d = im.data;
      for (var i = 0; i < d.length; i += 4) { var v = Math.random() * 255; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 255; }
      g.putImageData(im, 0, 0);
    });

    function sprite(col) {
      var k = col.map(Math.round).join(',');
      if (sprites[k]) return sprites[k];
      sprites[k] = texture(64, 64, function (g) {
        var gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
        gr.addColorStop(0, rgba(col, 1)); gr.addColorStop(0.45, rgba(col, 0.45)); gr.addColorStop(1, rgba(col, 0));
        g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
      });
      return sprites[k];
    }
    function tone(col, hz) { return mix(mix(col, C.shadow, cfg.shadowAmt), C.haze, hz); }
    function near(row, x, skip) {
      var best = null, d = 1e9;
      row.people.forEach(function (p) {
        if (p.role || p === skip) return;
        var dd = Math.abs(p.x - x);
        if (dd < d) { d = dd; best = p; }
      });
      return best;
    }
    function tNow() { return reduce ? (cfg.stillT || 3.2) : (performance.now() - t0) / 1000; }

    /* Construye la grada con semilla fija para que no cambie entre cuadros */
    function armar() {
      var r = rng(cfg.seed || 7), R = cfg.rows, f, i;
      rows = [];
      for (f = 0; f < R; f++) {
        var t = R === 1 ? 1 : f / (R - 1);
        var hr = lerp(cfg.hr[0], cfg.hr[1], Math.pow(t, 1.1)) * H;
        var paso = hr * 3.05;
        var row = { t: t, hr: hr, y: lerp(cfg.top, cfg.bottom, t) * H, paso: paso, blur: cfg.blur[f] || 0, hz: lerp(cfg.haze[0], cfg.haze[1], Math.pow(t, 0.8)), people: [], trapos: [] };
        var n = Math.ceil(W / paso) + 4, off = (f % 2) * paso * 0.5;
        for (i = 0; i < n; i++) {
          row.people.push({
            x: -2 * paso + i * paso + off + (r() - 0.5) * paso * 0.3,
            ph: r() * TAU, asy: r(), tam: 0.93 + r() * 0.14,
            shirt: pickw(cfg.shirts, r), hair: pickw(cfg.hairs, r), skin: pickw(cfg.skins, r),
            cap: r() < 0.11 ? pickw(cfg.shirts, r) : null,
            cel: r() < (cfg.cel || 0.42), phone: cfg.phones ? r() < 0.08 : false,
            scarf: r() < 0.07 ? pickw(cfg.scarves, r) : null,
            role: null, acc: 0, hand: null
          });
        }
        rows.push(row);
      }
      if (W >= (cfg.minW || 0)) {
        (cfg.trapos || []).forEach(function (tr) {
          var row = rows[tr.row]; if (!row) return;
          var a = near(row, tr.at * W); if (!a) return;
          a.role = 'trapoA';
          var b = near(row, a.x + tr.span * row.paso, a);
          if (!b) { a.role = null; return; }
          b.role = 'trapoB';
          row.trapos.push({ a: a, b: b, tr: tr });
        });
      }
      (cfg.flags || []).forEach(function (fl) {
        var row = rows[fl.row]; if (!row) return;
        var p = near(row, fl.at * W);
        if (p) { p.role = 'flag'; p.fl = fl; }
      });
      (cfg.bengalas || []).forEach(function (bg) {
        var row = rows[bg.row]; if (!row) return;
        var p = near(row, bg.at * W);
        if (p) { p.role = 'bengala'; p.bg = bg; }
      });
    }

    function dibujarFila(f, t) {
      var row = rows[f], g = ctx, layer = canFilter && row.blur > 0.15, i;
      if (layer) { g = lctx; g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H); }
      var hr = row.hr, hz = row.hz, lit = cfg.lit;
      var dims = [[C.shadow, cfg.shadowAmt * (cfg.clothShadow == null ? 0.4 : cfg.clothShadow)], [C.haze, hz * 0.8]];
      var wob = cfg.wob || 0.3;
      for (i = 0; i < row.people.length; i++) {
        var p = row.people[i], s = hr * p.tam;
        if (p.x < -s * 5 || p.x > W + s * 5) continue;

        /* ola que recorre la grada + zonas que festejan con los brazos arriba */
        var ola = 0;
        if (cfg.ola !== false) {
          var ph = frac((p.x / W) * (cfg.olaK || 1) + f * 0.02 - t / (cfg.olaT || 7));
          ola = ph < 0.2 ? Math.pow(Math.sin(ph / 0.2 * PI), 2) : 0;
        }
        var burst = smooth((Math.sin(t * (cfg.burstSpeed || 0.42) + p.x / W * 2.4 + f * 0.55) - 0.5) / 0.5);
        var a = Math.max(ola, p.cel ? burst * 0.92 : 0);
        var x = p.x + Math.sin(t * 0.9 + p.ph) * s * 0.06;
        var yh = row.y - ola * s * 0.85 - (p.cel ? burst * s * 0.22 : 0) + Math.sin(t * 1.6 + p.ph) * s * 0.04;
        var sw = s * 2.15, nw = s * 0.42, ySh = yh + s * 1.5, base = H + 8;
        var rx = s * 0.86, ry = s;

        var shirt = tone(p.shirt, hz), hair = tone(p.hair, hz), skin = tone(p.skin, hz);
        var aL = clamp(a * (0.88 + 0.24 * p.asy), 0, 1), aR = clamp(a * (1.12 - 0.24 * p.asy), 0, 1);
        if (p.role === 'flag' || p.role === 'bengala') aR = 1;
        else if (p.role === 'trapoA' || p.role === 'trapoB') { aL = 1; aR = 1; }

        /* brazos (van detrás del torso: el hombro los cubre) */
        var sleeve = rgba(mix(shirt, C.light, lit * 0.45)), skinC = rgba(mix(skin, C.light, lit * 0.4));
        var syh = ySh + s * 0.45, hL = null, hR = null, wig = t * (3 + p.asy * 2) * (wob > 0.4 ? 1.5 : 1) + p.ph;
        if (aL > 0.05) hL = arm(g, x - sw * 0.8, syh, x - sw * 0.8 - s * (0.5 + 0.9 * aL) + Math.sin(wig + 1) * s * wob * aL, ySh - s * (0.15 + 3.5 * aL), s * 1.75, s * 1.75, -1, s * 0.84, s * 0.56, sleeve, skinC);
        if (aR > 0.05) hR = arm(g, x + sw * 0.8, syh, x + sw * 0.8 + s * (0.5 + 0.9 * aR) + Math.sin(wig) * s * wob * aR, ySh - s * (0.15 + 3.5 * aR), s * 1.75, s * 1.75, 1, s * 0.84, s * 0.56, sleeve, skinC);
        p.hand = p.role === 'trapoB' ? hL : hR;

        /* orejas, torso, cuello */
        g.fillStyle = rgba(mix(skin, C.shadow, 0.25));
        g.beginPath(); g.ellipse(x - rx * 0.98, yh + ry * 0.18, s * 0.16, s * 0.24, 0, 0, TAU); g.fill();
        g.beginPath(); g.ellipse(x + rx * 0.98, yh + ry * 0.18, s * 0.16, s * 0.24, 0, 0, TAU); g.fill();

        var gr;
        if (cfg.side === 'left') {
          gr = g.createLinearGradient(x - sw, 0, x + sw, 0);
          gr.addColorStop(0, rgba(mix(shirt, C.light, lit)));
          gr.addColorStop(0.55, rgba(shirt));
          gr.addColorStop(1, rgba(mix(shirt, C.shadow, 0.32)));
        } else {
          gr = g.createLinearGradient(0, ySh - s * 0.2, 0, ySh + s * 2.6);
          gr.addColorStop(0, rgba(mix(shirt, C.light, lit)));
          gr.addColorStop(1, rgba(shirt));
        }
        g.fillStyle = gr;
        g.beginPath();
        g.moveTo(x - sw, base);
        g.lineTo(x - sw, ySh + s * 0.9);
        g.bezierCurveTo(x - sw, ySh + s * 0.1, x - sw * 0.55, ySh, x - nw, ySh - s * 0.15);
        g.lineTo(x + nw, ySh - s * 0.15);
        g.bezierCurveTo(x + sw * 0.55, ySh, x + sw, ySh + s * 0.1, x + sw, ySh + s * 0.9);
        g.lineTo(x + sw, base);
        g.closePath();
        g.fill();
        g.fillStyle = rgba(mix(skin, C.shadow, 0.38));
        g.fillRect(x - nw, yh + s * 0.7, nw * 2, ySh - yh - s * 0.55);

        /* cabeza vista de espaldas: pelo con luz arriba */
        var hg = g.createLinearGradient(0, yh - ry, 0, yh + ry);
        hg.addColorStop(0, rgba(mix(hair, C.light, lit * 0.55)));
        hg.addColorStop(0.55, rgba(hair));
        hg.addColorStop(1, rgba(mix(hair, C.shadow, 0.3)));
        g.fillStyle = hg;
        g.beginPath(); g.ellipse(x, yh, rx, ry, 0, 0, TAU); g.fill();
        if (p.cap) {
          var cc = tone(p.cap, hz);
          g.fillStyle = rgba(mix(cc, C.light, lit * 0.5));
          g.beginPath(); g.ellipse(x, yh - ry * 0.04, rx * 1.03, ry * 1.03, 0, PI, TAU); g.closePath(); g.fill();
          g.fillStyle = rgba(mix(cc, C.shadow, 0.3));
          g.fillRect(x - rx, yh - ry * 0.06, rx * 2, Math.max(1, s * 0.16));
        }
        if (cfg.rim > 0) {
          g.strokeStyle = rgba(C.light, cfg.rim * (1 - hz * 0.8));
          g.lineWidth = Math.max(0.7, s * 0.15);
          g.lineCap = 'round';
          g.beginPath(); g.ellipse(x, yh, rx, ry, 0, cfg.rimA0, cfg.rimA1); g.stroke();
          g.beginPath(); g.moveTo(x - nw, ySh - s * 0.15); g.bezierCurveTo(x - sw * 0.55, ySh, x - sw, ySh + s * 0.1, x - sw, ySh + s * 0.9); g.stroke();
          if (cfg.side !== 'left') {
            g.beginPath(); g.moveTo(x + nw, ySh - s * 0.15); g.bezierCurveTo(x + sw * 0.55, ySh, x + sw, ySh + s * 0.1, x + sw, ySh + s * 0.9); g.stroke();
          }
        }

        /* bufanda estirada entre las dos manos */
        if (p.scarf && hL && hR && aL > 0.5 && aR > 0.5 && !p.role) {
          var sg = s * (1 + Math.sin(t * 2 + p.ph) * 0.25), sc = tone(p.scarf[0], hz), sc2 = tone(p.scarf[1], hz);
          var my = Math.min(hL[1], hR[1]) + sg;
          g.lineCap = 'butt';
          g.strokeStyle = rgba(sc); g.lineWidth = s * 0.55;
          g.beginPath(); g.moveTo(hL[0], hL[1]); g.quadraticCurveTo((hL[0] + hR[0]) / 2, my + sg, hR[0], hR[1]); g.stroke();
          g.strokeStyle = rgba(sc2); g.setLineDash([s * 0.9, s * 0.9]);
          g.beginPath(); g.moveTo(hL[0], hL[1]); g.quadraticCurveTo((hL[0] + hR[0]) / 2, my + sg, hR[0], hR[1]); g.stroke();
          g.setLineDash([]);
        }

        /* luz de celular */
        if (p.phone && hR && aR > 0.3) {
          var pr = s * 1.7;
          g.globalCompositeOperation = 'lighter';
          var pg = g.createRadialGradient(hR[0], hR[1] - s * 0.5, 0, hR[0], hR[1] - s * 0.5, pr);
          pg.addColorStop(0, 'rgba(210,225,255,' + (0.7 * (1 - hz * 0.6)).toFixed(3) + ')');
          pg.addColorStop(1, 'rgba(120,150,255,0)');
          g.fillStyle = pg; g.fillRect(hR[0] - pr, hR[1] - s * 0.5 - pr, pr * 2, pr * 2);
          g.globalCompositeOperation = 'source-over';
        }

        /* bandera en mástil */
        if (p.role === 'flag' && hR) {
          var fl = p.fl, A = Math.sin(t * (cfg.swingSpeed || 1.05) + p.ph) * (cfg.swing || 0.07) + (cfg.lean || 0.12), plen = s * (fl.len || 8);
          var bx = hR[0] - Math.sin(A) * s * 1.5, by = hR[1] + Math.cos(A) * s * 1.5;
          var tx = hR[0] + Math.sin(A) * plen, ty = hR[1] - Math.cos(A) * plen;
          g.lineCap = 'round';
          g.strokeStyle = rgba(tone([205, 208, 214], hz * 0.8)); g.lineWidth = Math.max(1, s * 0.15);
          g.beginPath(); g.moveTo(bx, by); g.lineTo(tx, ty); g.stroke();
          var fw = s * fl.w, fh = fw * fl.tex.height / fl.tex.width;
          var m = flagMesh(tx, ty, fw, fh, fl.dir || 1, t, { amp: fl.amp, k: fl.k, speed: fl.speed, phase: p.ph, droop: 0.05, shadeK: cfg.shadeK || 0.6 });
          cloth(g, dpr, fl.tex, m.top, m.bot, m.shade, dims, cfg.clothLit);
        }

        /* bengala con brillo */
        if (p.role === 'bengala' && hR) {
          var bg = p.bg, tipx = hR[0] + s * 0.4, tipy = hR[1] - s * 1.3;
          g.lineCap = 'round';
          g.strokeStyle = rgba(tone([60, 60, 70], hz)); g.lineWidth = Math.max(1, s * 0.24);
          g.beginPath(); g.moveTo(hR[0], hR[1] + s * 0.2); g.lineTo(tipx, tipy); g.stroke();
          var fk = 0.85 + 0.15 * Math.sin(t * 23 + p.ph) + 0.06 * Math.sin(t * 51);
          var gl = s * 7;
          g.globalCompositeOperation = cfg.flareBlend || 'lighter';
          var fg = g.createRadialGradient(tipx, tipy, 0, tipx, tipy, gl);
          fg.addColorStop(0, rgba(mix(bg.col, [255, 255, 255], 0.55), 0.95 * fk));
          fg.addColorStop(0.2, rgba(bg.col, 0.5 * fk));
          fg.addColorStop(1, rgba(bg.col, 0));
          g.fillStyle = fg; g.fillRect(tipx - gl, tipy - gl, gl * 2, gl * 2);
          g.globalCompositeOperation = 'source-over';
          g.fillStyle = 'rgba(255,255,255,' + (0.95 * fk).toFixed(3) + ')';
          g.beginPath(); g.arc(tipx, tipy, Math.max(1, s * 0.3), 0, TAU); g.fill();
          flares.push({ p: p, x: tipx, y: tipy, s: s, col: bg.smoke });
        }
      }

      /* trapos: pasan por encima de las cabezas de la fila que los sostiene */
      for (i = 0; i < row.trapos.length; i++) {
        var T = row.trapos[i], A0 = T.a.hand, B0 = T.b.hand;
        if (!A0 || !B0) continue;
        var dist = Math.abs(B0[0] - A0[0]), th = dist / T.tr.aspect;
        var bm = bannerMesh(A0, B0, th, t, { k: T.tr.k || 7, speed: T.tr.speed || 4.4, amp: T.tr.amp || 0.34, sag: T.tr.sag || 0.1, phase: T.a.ph, shadeK: cfg.shadeK || 0.6 });
        cloth(g, dpr, T.tr.tex, bm.top, bm.bot, bm.shade, dims, cfg.clothLit);
      }

      if (layer) {
        ctx.save();
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.filter = 'blur(' + (row.blur * dpr).toFixed(2) + 'px)';
        ctx.drawImage(lay, 0, 0);
        ctx.restore();
        ctx.filter = 'none';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
    }

    /* ───── Humo de bengalas ───── */
    function emitir(dt) {
      for (var i = 0; i < flares.length; i++) {
        var fl = flares[i], p = fl.p, sc = Math.max(0.5, fl.s / 12), k = 0;
        p.acc += dt * 30;
        while (p.acc >= 1 && k++ < 8) {
          p.acc -= 1;
          parts.push({ x: fl.x + (Math.random() - 0.5) * 2, y: fl.y, vx: cfg.wind * (0.4 + Math.random() * 0.8) + (Math.random() - 0.5) * 12 * sc, vy: -(16 + Math.random() * 26) * sc, life: 0, max: 3.4 + Math.random() * 2.8, r0: fl.s * 0.9, gr: fl.s * (2.4 + Math.random() * 1.8), col: fl.col });
        }
      }
    }
    function mover(dt) {
      var j = 0;
      for (var i = 0; i < parts.length; i++) {
        var q = parts[i];
        q.life += dt;
        if (q.life >= q.max) continue;
        q.x += q.vx * dt; q.y += q.vy * dt;
        q.vx += (cfg.wind - q.vx) * dt * 0.5; q.vy *= (1 - 0.22 * dt);
        parts[j++] = q;
      }
      parts.length = j;
    }
    function dibujarHumo() {
      for (var i = 0; i < parts.length; i++) {
        var q = parts[i], k = q.life / q.max;
        var al = (cfg.smokeA || 0.4) * (1 - k) * (1 - k) * Math.min(1, q.life * 2.5);
        if (al < 0.004) continue;
        var r = q.r0 + q.gr * k;
        ctx.globalAlpha = al;
        ctx.drawImage(sprite(q.col), q.x - r, q.y - r, r * 2, r * 2);
      }
      ctx.globalAlpha = 1;
    }

    /* ───── Cuadro ───── */
    function dibujar(t, dt) {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      flares.length = 0;
      for (var f = 0; f < rows.length; f++) dibujarFila(f, t);
      emitir(dt); mover(dt);
      dibujarHumo();
      if (cfg.overlay) cfg.overlay(ctx, W, H, t);
      if (cfg.grain) {
        if (!noiseP) noiseP = ctx.createPattern(noiseCv, 'repeat');
        ctx.save();
        ctx.setTransform(1, 0, 0, 1, Math.floor(Math.random() * 180), Math.floor(Math.random() * 180));
        ctx.globalAlpha = cfg.grain;
        ctx.globalCompositeOperation = 'source-atop';
        ctx.fillStyle = noiseP;
        ctx.fillRect(-180, -180, canvas.width + 360, canvas.height + 360);
        ctx.restore();
      }
    }

    function medir() {
      var w = Math.max(1, canvas.offsetWidth), h = Math.max(1, canvas.offsetHeight);
      if (w === W && h === H) return;
      W = w; H = h;
      dpr = Math.min(window.devicePixelRatio || 1, cfg.dprMax || 2);
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      lay.width = canvas.width; lay.height = canvas.height;
      noiseP = null; parts.length = 0;
      armar();
      dibujar(tNow(), 0);
      for (var k = 0; k < 120; k++) { emitir(0.05); mover(0.05); }
      dibujar(tNow(), 0);
    }

    function cuadro(ahora) {
      if (!running) return;
      var dt = Math.min(0.05, (ahora - last) / 1000);
      last = ahora;
      dibujar((ahora - t0) / 1000, dt);
      raf = requestAnimationFrame(cuadro);
    }
    function arrancar() {
      if (reduce || running || !visible || document.hidden) return;
      running = true; last = performance.now();
      raf = requestAnimationFrame(cuadro);
    }
    function parar() { running = false; cancelAnimationFrame(raf); }

    /* ───── Ciclo de vida ───── */
    medir();
    if (window.ResizeObserver) {
      var pendiente = 0;
      new ResizeObserver(function () { clearTimeout(pendiente); pendiente = setTimeout(medir, 120); }).observe(canvas);
    } else {
      window.addEventListener('resize', medir);
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        visible = es[0].isIntersecting;
        if (visible) arrancar(); else parar();
      }, { threshold: 0 }).observe(canvas);
    } else {
      visible = true;
      arrancar();
    }
    document.addEventListener('visibilitychange', function () { if (document.hidden) parar(); else arrancar(); });
  }

  /* la tipografía de las telas tiene que estar lista antes de dibujar el texto */
  var listo = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
  listo.then(function () {
    canvases.forEach(function (cv) { new Hinchada(cv); });
  });
})();
