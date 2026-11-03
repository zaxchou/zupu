/* Standalone Canvas-like PDF backend for paintTreeBody. Inline before its caller.
 * Dependency: ZUPU_PDF_FONT_BASE64, a base64-encoded static TrueType (glyf) font.
 * No shaping/kerning or weight synthesis: all sizes/families use this one font.
 * Only drawImage rasterizes (individual photos); everything else stays vector/text.
 */
function createVectorPdfContext(width, height, fontBase64) {
  'use strict';
  const fail = message => { throw new Error('PDF export: ' + message); };
  const finite = (...xs) => { if (!xs.every(Number.isFinite)) fail('Coordinates and dimensions must be finite numbers'); };
  finite(width, height);
  if (width <= 0 || height <= 0) fail('Page width and height must be positive');
  const num = x => {
    finite(x);
    if (Math.abs(x) >= 1e21) fail('Numeric value is too large');
    return x.toFixed(6).replace(/\.?0+$/, '') || '0';
  };
  const hex = x => x.toString(16).padStart(4, '0');
  const bytes = s => new TextEncoder().encode(s);
  const concat = parts => {
    const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
    let offset = 0;
    for (const part of parts) { out.set(part, offset); offset += part.length; }
    return out;
  };
  const unbase64 = s => {
    const raw = atob(s), out = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  };
  let fontData;
  function getFont() {
    if (fontData) return fontData;
    const source = fontBase64 == null ? (typeof ZUPU_PDF_FONT_BASE64 === 'string' ? ZUPU_PDF_FONT_BASE64 : '') : fontBase64;
    if (typeof source !== 'string' || !source) fail('Missing embedded font ZUPU_PDF_FONT_BASE64');
    let data;
    try { data = unbase64(source); }
    catch (_) { fail('Invalid base64 font data'); }
    const view = new DataView(data.buffer), tables = new Map();
    const check = (p, length) => {
      if (!Number.isInteger(p) || p < 0 || length < 0 || p + length > data.length) fail('Incomplete TrueType font data');
    };
    const u16 = p => { check(p, 2); return view.getUint16(p); };
    const i16 = p => { check(p, 2); return view.getInt16(p); };
    const u32 = p => { check(p, 4); return view.getUint32(p); };
    if (u32(0) !== 0x00010000 && u32(0) !== 0x74727565) fail('A static TrueType TTF font is required (TTC/CFF is unsupported)');
    const count = u16(4);
    check(12, count * 16);
    for (let i = 0; i < count; i++) {
      const p = 12 + i * 16;
      const tag = String.fromCharCode(...data.subarray(p, p + 4));
      const offset = u32(p + 8), length = u32(p + 12);
      check(offset, length);
      tables.set(tag, { offset, length });
    }
    if (tables.has('fvar')) fail('Select a static TTF font; variable fonts are unsupported');
    const os2 = tables.get('OS/2');
    const fsType = os2 && os2.length >= 10 ? u16(os2.offset + 8) : 0;
    if (fsType & 0x0002) fail('This font prohibits embedding; select an embeddable TTF font');
    if (fsType & 0x0200) fail('This font permits bitmap embedding only; select an outline-embeddable TTF font');
    const canSubset = !(fsType & 0x0100);
    const table = (tag, min) => {
      const t = tables.get(tag);
      if (!t || t.length < min) fail('TrueType font is missing a valid ' + tag + ' table');
      return t.offset;
    };
    const head = table('head', 54), hhea = table('hhea', 36), maxp = table('maxp', 6);
    const hmtx = table('hmtx', 4), loca = table('loca', 2), glyf = table('glyf', 0);
    const units = u16(head + 18), glyphCount = u16(maxp + 4), metricsCount = u16(hhea + 34);
    const locaFormat = i16(head + 50);
    if (!units || !glyphCount || !metricsCount || metricsCount > glyphCount || ![0, 1].includes(locaFormat)) fail('Invalid font metrics');
    table('hmtx', metricsCount * 4 + (glyphCount - metricsCount) * 2);
    table('loca', (glyphCount + 1) * (locaFormat ? 4 : 2));
    const locations = Array.from({ length: glyphCount + 1 }, (_, i) => locaFormat ? u32(loca + i * 4) : u16(loca + i * 2) * 2);
    if (locations.some((p, i) => p > tables.get('glyf').length || (i && p < locations[i - 1]))) fail('Invalid font loca table');
    const advance = gid => u16(hmtx + Math.min(gid, metricsCount - 1) * 4);
    // PDF widths and measureText use exactly the same rounded 1000-em metrics.
    const pdfWidth = gid => +num(advance(gid) * 1000 / units);
    const cmap = table('cmap', 4), cmapEnd = cmap + tables.get('cmap').length, cmaps = [];
    if (cmap + 4 + u16(cmap + 2) * 8 > cmapEnd) fail('Invalid font cmap table');
    for (let i = 0; i < u16(cmap + 2); i++) {
      const r = cmap + 4 + i * 8, platform = u16(r), encoding = u16(r + 2);
      if (platform !== 0 && !(platform === 3 && (encoding === 1 || encoding === 10))) continue;
      const p = cmap + u32(r + 4);
      if (p < cmap || p + 2 > cmapEnd) fail('Font cmap subtable is out of bounds');
      const format = u16(p);
      if (format !== 4 && format !== 12) continue;
      if (p + (format === 12 ? 16 : 14) > cmapEnd) fail('Incomplete font cmap subtable');
      const length = format === 12 ? u32(p + 4) : u16(p + 2), end = p + length;
      if (end > cmapEnd || length < (format === 12 ? 16 : 16)) fail('Invalid font cmap length');
      const n = format === 12 ? u32(p + 12) : u16(p + 6) / 2;
      if (!Number.isInteger(n) || (format === 12 ? 16 + n * 12 : 16 + n * 8) > length) fail('Invalid font cmap entries');
      cmaps.push({ p, end, format, n });
    }
    cmaps.sort((a, b) => b.format - a.format);
    if (!cmaps.length) fail('Font has no Unicode cmap format 4/12');
    function glyph(cp, allowMissing = false) {
      for (const c of cmaps) {
        let gid = 0, lo = 0, hi = c.n - 1;
        if (c.format === 12) {
          while (lo <= hi) {
            const mid = (lo + hi) >>> 1, p = c.p + 16 + mid * 12;
            if (cp < u32(p)) hi = mid - 1;
            else if (cp > u32(p + 4)) lo = mid + 1;
            else { gid = u32(p + 8) + cp - u32(p); break; }
          }
        } else if (cp <= 0xffff) {
          while (lo <= hi) {
            const mid = (lo + hi) >>> 1;
            if (u16(c.p + 14 + mid * 2) < cp) lo = mid + 1;
            else hi = mid - 1;
          }
          if (lo < c.n && cp >= u16(c.p + 16 + c.n * 2 + lo * 2)) {
            const delta = i16(c.p + 16 + c.n * 4 + lo * 2);
            const r = c.p + 16 + c.n * 6 + lo * 2, range = u16(r);
            if (!range) gid = (cp + delta) & 0xffff;
            else {
              const at = r + range + (cp - u16(c.p + 16 + c.n * 2 + lo * 2)) * 2;
              if (at < c.p || at + 2 > c.end) fail('Font cmap glyph mapping is out of bounds');
              gid = u16(at);
              if (gid) gid = (gid + delta) & 0xffff;
            }
          }
        }
        if (gid && gid < glyphCount) return gid;
      }
      if (allowMissing) return 0;
      const ch = String.fromCodePoint(cp), code = 'U+' + cp.toString(16).toUpperCase().padStart(4, '0');
      fail('Embedded font is missing character “' + ch + '” (' + code + ')' + (cp >= 0xd800 && cp <= 0xdfff ? '; isolated surrogate detected, iterate text by Unicode code point' : '; select a local TTF font containing this character in the export dialog'));
    }
    function subset(gids) {
      if (!canSubset) return data.slice();
      const used = new Set([0, ...gids]), pending = [...used];
      // Composite glyph references retain their original glyph IDs.
      for (let i = 0; i < pending.length; i++) {
        const gid = pending[i], start = glyf + locations[gid], end = glyf + locations[gid + 1];
        if (start === end) continue;
        if (end - start < 10) fail('Incomplete font glyf data');
        if (i16(start) >= 0) continue;
        let p = start + 10, flags;
        do {
          if (p + 4 > end) fail('Incomplete composite glyph data');
          flags = u16(p);
          const child = u16(p + 2);
          if (child >= glyphCount) fail('Composite glyph reference is out of bounds');
          if (!used.has(child)) { used.add(child); pending.push(child); }
          p += 4 + (flags & 1 ? 4 : 2) + (flags & 8 ? 2 : flags & 64 ? 4 : flags & 128 ? 8 : 0);
          if (p > end) fail('Composite glyph transform is out of bounds');
        } while (flags & 32);
      }
      const newLoca = new Uint8Array((glyphCount + 1) * 4), lv = new DataView(newLoca.buffer), parts = [];
      let size = 0;
      for (let gid = 0; gid < glyphCount; gid++) {
        lv.setUint32(gid * 4, size);
        if (!used.has(gid)) continue;
        const g = data.subarray(glyf + locations[gid], glyf + locations[gid + 1]);
        parts.push(g); size += g.length;
        const padding = (4 - size % 4) % 4;
        if (padding) { parts.push(new Uint8Array(padding)); size += padding; }
      }
      lv.setUint32(glyphCount * 4, size);
      const newHead = data.slice(head, head + tables.get('head').length), hv = new DataView(newHead.buffer);
      hv.setUint32(8, 0); hv.setInt16(50, 1);
      const keep = ['OS/2', 'cmap', 'cvt ', 'fpgm', 'gasp', 'glyf', 'head', 'hhea', 'hmtx', 'loca', 'maxp', 'name', 'post', 'prep'];
      const rebuilt = new Map([['glyf', concat(parts)], ['loca', newLoca], ['head', newHead]]);
      for (const tag of keep) {
        if (!rebuilt.has(tag) && tables.has(tag)) {
          const t = tables.get(tag);
          rebuilt.set(tag, data.subarray(t.offset, t.offset + t.length));
        }
      }
      const tags = [...rebuilt.keys()].sort(), n = tags.length;
      const total = 12 + n * 16 + [...rebuilt.values()].reduce((s, t) => s + Math.ceil(t.length / 4) * 4, 0);
      const out = new Uint8Array(total), ov = new DataView(out.buffer);
      const checksum = a => {
        let sum = 0;
        for (let i = 0; i < a.length; i += 4) sum = (sum + ((a[i] || 0) * 0x1000000 + (a[i + 1] || 0) * 0x10000 + (a[i + 2] || 0) * 256 + (a[i + 3] || 0))) >>> 0;
        return sum;
      };
      ov.setUint32(0, 0x00010000); ov.setUint16(4, n);
      const power = 2 ** Math.floor(Math.log2(n));
      ov.setUint16(6, power * 16); ov.setUint16(8, Math.log2(power)); ov.setUint16(10, n * 16 - power * 16);
      let offset = 12 + n * 16, headOffset;
      tags.forEach((tag, i) => {
        const p = 12 + i * 16, t = rebuilt.get(tag);
        for (let j = 0; j < 4; j++) out[p + j] = tag.charCodeAt(j);
        ov.setUint32(p + 4, checksum(t)); ov.setUint32(p + 8, offset); ov.setUint32(p + 12, t.length);
        out.set(t, offset);
        if (tag === 'head') headOffset = offset;
        offset += Math.ceil(t.length / 4) * 4;
      });
      ov.setUint32(headOffset + 8, (0xb1b0afba - checksum(out)) >>> 0);
      return out;
    }
    fontData = {
      glyph, pdfWidth, subset, units, canSubset, ascent: i16(hhea + 4), descent: i16(hhea + 6),
      bbox: [i16(head + 36), i16(head + 38), i16(head + 40), i16(head + 42)],
      glyphBox(gid) {
        const p = glyf + locations[gid];
        return locations[gid + 1] - locations[gid] >= 10 ? [i16(p + 2), i16(p + 4), i16(p + 6), i16(p + 8)] : [0, 0, 0, 0];
      }
    };
    return fontData;
  }

  let state = {
    font: '10px sans-serif', fillStyle: '#000000', strokeStyle: '#000000',
    lineWidth: 1, lineCap: 'butt', lineJoin: 'miter', miterLimit: 10,
    textAlign: 'start', textBaseline: 'alphabetic', direction: 'ltr', globalAlpha: 1,
    lineDashOffset: 0, dash: [], matrix: [1, 0, 0, 1, 0, 0]
  };
  const stack = [], ops = [], characters = new Map(), alphas = new Map(), images = [], imageCache = new WeakMap();
  let path = [], current = null, subpath = null;
  const point = (x, y, m = state.matrix) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
  function inverse(m) {
    const det = m[0] * m[3] - m[1] * m[2];
    return det ? [m[3] / det, -m[1] / det, -m[2] / det, m[0] / det, (m[2] * m[5] - m[3] * m[4]) / det, (m[1] * m[4] - m[0] * m[5]) / det] : null;
  }
  function pathString(inv) {
    return path.map(c => {
      if (c[0] === 'h') return 'h';
      const values = [];
      for (let i = 1; i < c.length; i += 2) values.push(...(inv ? point(c[i], c[i + 1], inv) : [c[i], c[i + 1]]));
      return values.map(num).join(' ') + ' ' + c[0];
    }).join('\n');
  }
  function color(value) {
    const s = String(value).trim().toLowerCase();
    if (s === 'transparent') return [0, 0, 0, 0];
    if (s === 'white') return [1, 1, 1, 1];
    if (s === 'black') return [0, 0, 0, 1];
    let m = /^#([\da-f]{3,4}|[\da-f]{6}|[\da-f]{8})$/.exec(s);
    if (m) {
      let h = m[1];
      if (h.length < 5) h = [...h].map(c => c + c).join('');
      return [0, 2, 4, 6].map((i, n) => n === 3 && h.length === 6 ? 1 : parseInt(h.slice(i, i + 2), 16) / 255);
    }
    m = /^rgba?\(\s*([+-]?[\d.]+)(%)?\s*,\s*([+-]?[\d.]+)(%)?\s*,\s*([+-]?[\d.]+)(%)?(?:\s*,\s*([+-]?[\d.]+)(%)?)?\s*\)$/.exec(s);
    if (!m) fail('Unsupported color: ' + s);
    const clamp = x => Math.max(0, Math.min(1, x));
    const result = [clamp(+m[1] / (m[2] ? 100 : 255)), clamp(+m[3] / (m[4] ? 100 : 255)), clamp(+m[5] / (m[6] ? 100 : 255)), m[7] === undefined ? 1 : clamp(+m[7] / (m[8] ? 100 : 1))];
    finite(...result);
    return result;
  }
  function alphaCommand(alpha) {
    const key = num(Math.max(0, Math.min(1, alpha * state.globalAlpha)));
    if (!alphas.has(key)) alphas.set(key, 'GS' + (alphas.size + 1));
    return '/' + alphas.get(key) + ' gs';
  }
  function paintStyle(stroke) {
    const c = color(stroke ? state.strokeStyle : state.fillStyle);
    let s = c.slice(0, 3).map(num).join(' ') + (stroke ? ' RG\n' : ' rg\n') + alphaCommand(c[3]);
    if (stroke) {
      const cap = { butt: 0, round: 1, square: 2 }[state.lineCap], join = { miter: 0, round: 1, bevel: 2 }[state.lineJoin];
      if (cap === undefined || join === undefined || !(state.lineWidth > 0) || !(state.miterLimit > 0)) fail('Invalid line style');
      s += '\n' + num(state.lineWidth) + ' w ' + cap + ' J ' + join + ' j ' + num(state.miterLimit) + ' M\n[' + state.dash.map(num).join(' ') + '] ' + num(state.lineDashOffset) + ' d';
    }
    return s;
  }
  function draw(command, stroke) {
    if (!inverse(state.matrix)) return;
    ops.push('q\n' + state.matrix.map(num).join(' ') + ' cm\n' + paintStyle(stroke) + '\n' + command + '\nQ');
  }
  function fontSize() {
    const m = /(?:^|\s)(\d+(?:\.\d+)?|\.\d+)px(?=\s|\/|$)/i.exec(String(state.font));
    if (!m || !(+m[1] > 0)) fail('Font size must be positive and use px: ' + state.font);
    return +m[1];
  }
  function textRun(text) {
    const f = getFont(), size = fontSize(), glyphs = [];
    let width = 0;
    for (const ch of String(text)) {
      const cp = ch.codePointAt(0), gid = f.glyph(cp, cp === 0x25b8), vector = !gid && cp === 0x25b8;
      const advance = (vector ? 650 : f.pdfWidth(gid)) * size / 1000;
      glyphs.push({ ch, cp, gid, vector, x: width }); width += advance;
    }
    return { f, size, glyphs, width };
  }
  const ctx = {
    canvas: { width, height },
    save() {
      stack.push({ ...state, dash: state.dash.slice(), matrix: state.matrix.slice() }); ops.push('q');
    },
    restore() { if (stack.length) { state = stack.pop(); ops.push('Q'); } },
    translate(x, y) {
      finite(x, y); const p = point(x, y); state.matrix[4] = p[0]; state.matrix[5] = p[1];
    },
    scale(x, y) {
      finite(x, y); state.matrix[0] *= x; state.matrix[1] *= x; state.matrix[2] *= y; state.matrix[3] *= y;
    },
    setLineDash(dash) {
      const a = Array.from(dash, Number); finite(...a);
      if (a.some(x => x < 0)) fail('Dash lengths must not be negative');
      state.dash = a.length % 2 ? a.concat(a) : a;
      if (state.dash.every(x => x === 0)) state.dash = [];
    },
    getLineDash() { return state.dash.slice(); },
    beginPath() { path = []; current = subpath = null; },
    moveTo(x, y) {
      finite(x, y); current = point(x, y); subpath = current; path.push(['m', ...current]);
    },
    lineTo(x, y) {
      finite(x, y);
      if (!current) return ctx.moveTo(x, y);
      current = point(x, y); path.push(['l', ...current]);
    },
    bezierCurveTo(x1, y1, x2, y2, x, y) {
      finite(x1, y1, x2, y2, x, y);
      if (!current) ctx.moveTo(x1, y1);
      current = point(x, y); path.push(['c', ...point(x1, y1), ...point(x2, y2), ...current]);
    },
    quadraticCurveTo(x1, y1, x, y) {
      finite(x1, y1, x, y);
      if (!current) ctx.moveTo(x1, y1);
      const p = point(x1, y1), end = point(x, y);
      path.push(['c', current[0] + (p[0] - current[0]) * 2 / 3, current[1] + (p[1] - current[1]) * 2 / 3, end[0] + (p[0] - end[0]) * 2 / 3, end[1] + (p[1] - end[1]) * 2 / 3, ...end]);
      current = end;
    },
    closePath() { if (current) { path.push(['h']); current = subpath; } },
    arc(x, y, radius, start, end, counterclockwise = false) {
      finite(x, y, radius, start, end);
      if (radius < 0) fail('Arc radius must not be negative');
      const tau = Math.PI * 2, raw = end - start;
      let delta = counterclockwise ? (raw <= -tau ? -tau : raw > 0 ? -tau + raw % tau : raw) : (raw >= tau ? tau : raw < 0 ? tau - (-raw) % tau : raw);
      start %= tau;
      const sx = x + radius * Math.cos(start), sy = y + radius * Math.sin(start);
      if (current) ctx.lineTo(sx, sy); else ctx.moveTo(sx, sy);
      const steps = Math.ceil(Math.abs(delta) / (Math.PI / 2));
      if (!steps || radius === 0) return;
      delta /= steps;
      for (let i = 0; i < steps; i++) {
        const a = start + i * delta, b = a + delta, k = 4 / 3 * Math.tan(delta / 4);
        ctx.bezierCurveTo(x + radius * (Math.cos(a) - k * Math.sin(a)), y + radius * (Math.sin(a) + k * Math.cos(a)), x + radius * (Math.cos(b) + k * Math.sin(b)), y + radius * (Math.sin(b) - k * Math.cos(b)), x + radius * Math.cos(b), y + radius * Math.sin(b));
      }
    },
    roundRect(x, y, w, h, radii = 0) {
      finite(x, y, w, h);
      let r = Array.isArray(radii) ? radii.slice() : [radii];
      if (!r.length || r.length > 4) fail('Expected one to four corner radii');
      r = r.map(Number); finite(...r);
      if (r.some(v => v < 0)) fail('Corner radii must not be negative');
      r = r.length === 1 ? [r[0], r[0], r[0], r[0]] : r.length === 2 ? [r[0], r[1], r[0], r[1]] : r.length === 3 ? [r[0], r[1], r[2], r[1]] : r;
      const reverse = (w < 0) !== (h < 0);
      if (w < 0) { x += w; w = -w; r = [r[1], r[0], r[3], r[2]]; }
      if (h < 0) { y += h; h = -h; r = [r[3], r[2], r[1], r[0]]; }
      const factor = Math.min(1, w / (r[0] + r[1] || 1), w / (r[2] + r[3] || 1), h / (r[0] + r[3] || 1), h / (r[1] + r[2] || 1));
      r = r.map(v => v * factor);
      const corners = [[x + w - r[1], y + r[1], r[1], -Math.PI / 2], [x + w - r[2], y + h - r[2], r[2], 0], [x + r[3], y + h - r[3], r[3], Math.PI / 2], [x + r[0], y + r[0], r[0], Math.PI]];
      ctx.moveTo(x + r[0], y);
      if (!reverse) {
        for (const [cx, cy, radius, angle] of corners) ctx.arc(cx, cy, radius, angle, angle + Math.PI / 2);
      } else {
        ctx.arc(x + r[0], y + r[0], r[0], -Math.PI / 2, -Math.PI, true);
        ctx.arc(x + r[3], y + h - r[3], r[3], Math.PI, Math.PI / 2, true);
        ctx.arc(x + w - r[2], y + h - r[2], r[2], Math.PI / 2, 0, true);
        ctx.arc(x + w - r[1], y + r[1], r[1], 0, -Math.PI / 2, true);
      }
      ctx.closePath(); ctx.moveTo(x, y);
    },
    fill(rule = 'nonzero') {
      if (!['nonzero', 'evenodd'].includes(rule)) fail('Unsupported fill rule');
      const inv = inverse(state.matrix);
      if (inv && path.length) draw(pathString(inv) + (rule === 'evenodd' ? '\nf*' : '\nf'), false);
    },
    stroke() { const inv = inverse(state.matrix); if (inv && path.length) draw(pathString(inv) + '\nS', true); },
    clip(rule = 'nonzero') {
      if (!['nonzero', 'evenodd'].includes(rule)) fail('Unsupported clip rule');
      ops.push(pathString() + (rule === 'evenodd' ? '\nW* n' : '\nW n'));
    },
    fillRect(x, y, w, h) { finite(x, y, w, h); draw([x, y, w, h].map(num).join(' ') + ' re f', false); },
    measureText(text) {
      const run = textRun(text), f = run.f, k = run.size / f.units;
      let left = Infinity, right = -Infinity, top = 0, bottom = 0;
      for (const g of run.glyphs) {
        const box = g.vector ? [0.1 * f.units, 0, 0.55 * f.units, 0.6 * f.units] : f.glyphBox(g.gid);
        left = Math.min(left, g.x + box[0] * k); right = Math.max(right, g.x + box[2] * k);
        top = Math.max(top, box[3] * k); bottom = Math.max(bottom, -box[1] * k);
      }
      const align = alignment(run.width), baseline = baselineOffset(f, run.size);
      return {
        width: run.width, actualBoundingBoxLeft: run.glyphs.length ? align - left : 0,
        actualBoundingBoxRight: run.glyphs.length ? right - align : 0,
        actualBoundingBoxAscent: top - baseline, actualBoundingBoxDescent: bottom + baseline,
        fontBoundingBoxAscent: f.ascent * k - baseline, fontBoundingBoxDescent: -f.descent * k + baseline
      };
    },
    fillText(text, x, y, maxWidth) {
      finite(x, y);
      if (maxWidth !== undefined) { finite(maxWidth); if (maxWidth <= 0) return; }
      const run = textRun(text);
      if (!run.glyphs.length) return;
      const factor = maxWidth === undefined || !run.width ? 1 : Math.min(1, maxWidth / run.width);
      x -= alignment(run.width * factor); y += baselineOffset(run.f, run.size);
      let encoded = '', runX = x;
      const flush = () => {
        if (encoded) draw('BT /F1 ' + num(run.size) + ' Tf ' + num(factor) + ' 0 0 -1 ' + num(runX) + ' ' + num(y) + ' Tm <' + encoded + '> Tj ET', false);
        encoded = '';
      };
      for (const g of run.glyphs) {
        if (g.vector) {
          // Only the UI disclosure marker may fall back to a vector triangle.
          flush();
          const vx = x + (g.x + run.size * 0.1) * factor, vy = y - run.size * 0.6;
          draw(num(vx) + ' ' + num(vy) + ' m ' + num(vx + run.size * 0.45 * factor) + ' ' + num(vy + run.size * 0.3) + ' l ' + num(vx) + ' ' + num(y) + ' l h f', false);
          continue;
        }
        if (!encoded) runX = x + g.x * factor;
        if (!characters.has(g.cp)) {
          if (characters.size >= 65535) fail('Too many distinct characters on one page (maximum 65535)');
          characters.set(g.cp, { ...g, cid: characters.size + 1 });
        }
        encoded += hex(characters.get(g.cp).cid);
      }
      flush();
    },
    drawImage(image, x, y, w, h) {
      const iw = image.naturalWidth || image.width, ih = image.naturalHeight || image.height;
      if (w === undefined && h === undefined) { w = iw; h = ih; }
      finite(x, y, w, h, iw, ih);
      if (!iw || !ih) fail('Photo is not decoded or has zero dimensions');
      if (!w || !h || !inverse(state.matrix)) return;
      if (w < 0) { x += w; w = -w; }
      if (h < 0) { y += h; h = -h; }
      let item = imageCache.get(image);
      if (!item) {
        try {
          const canvas = document.createElement('canvas'); canvas.width = iw; canvas.height = ih;
          const c = canvas.getContext('2d');
          c.fillStyle = '#ffffff'; c.fillRect(0, 0, iw, ih); c.drawImage(image, 0, 0, iw, ih);
          const url = canvas.toDataURL('image/jpeg', 0.92);
          if (!url.startsWith('data:image/jpeg;base64,')) fail('Browser cannot encode a JPEG photo');
          item = { name: 'Im' + (images.length + 1), width: iw, height: ih, data: unbase64(url.slice(url.indexOf(',') + 1)) };
          images.push(item); imageCache.set(image, item);
        } catch (e) { fail('Failed to convert photo to JPEG: ' + e.message); }
      }
      ops.push('q\n' + state.matrix.map(num).join(' ') + ' cm\n' + alphaCommand(1) + '\n' + [w, 0, 0, -h, x, y + h].map(num).join(' ') + ' cm /' + item.name + ' Do\nQ');
    },
    async toBytes() {
      // Snapshot before the first await; drawing may continue while compression runs.
      const chars = [...characters.values()], alphaEntries = [...alphas], photoEntries = images.slice();
      const pageScale = Math.min(1, 14400 / Math.max(width, height));
      const pageW = +num(width * pageScale), pageH = +num(height * pageScale);
      // Keep tiny page scales precise; rounding to coordinate precision could clip a long tree.
      const scaleToken = pageScale.toFixed(20).replace(/\.?0+$/, '');
      if (!(+scaleToken > 0)) fail('Page dimensions are too large');
      const content = bytes('q\n' + scaleToken + ' 0 0 -' + scaleToken + ' 0 ' + num(pageH) + ' cm\n' + ops.join('\n') + '\n' + 'Q\n'.repeat(stack.length + 1));
      const objects = [null], add = value => { objects.push(value); return objects.length - 1; };
      async function stream(data, entries = '', compress = true) {
        const length1 = data.length;
        let filter = '';
        if (compress && typeof CompressionStream === 'function') {
          try {
            const zipped = new Uint8Array(await new Response(new Blob([data]).stream().pipeThrough(new CompressionStream('deflate'))).arrayBuffer());
            if (zipped.length < data.length) { data = zipped; filter = ' /Filter /FlateDecode'; }
          } catch (_) { /* Uncompressed streams remain valid PDF. */ }
        }
        return add(concat([bytes('<< /Length ' + data.length + filter + entries.replace(/\$LENGTH1/g, String(length1)) + ' >>\nstream\n'), data, bytes('\nendstream')]));
      }
      const catalog = add(null), pages = add(null), page = add(null);
      let fontId;
      if (chars.length) {
        const f = getFont(), subset = f.subset(chars.map(c => c.gid));
        const fontFile = await stream(subset, ' /Length1 $LENGTH1');
        const metric = x => num(x * 1000 / f.units), name = (f.canSubset ? 'ZUPUAA+' : '') + 'ZupuVector';
        const descriptor = add(bytes('<< /Type /FontDescriptor /FontName /' + name + ' /Flags 4 /FontBBox [' + f.bbox.map(metric).join(' ') + '] /ItalicAngle 0 /Ascent ' + metric(f.ascent) + ' /Descent ' + metric(f.descent) + ' /CapHeight ' + metric(f.ascent) + ' /StemV 80 /FontFile2 ' + fontFile + ' 0 R >>'));
        const mapping = new Uint8Array((chars.length + 1) * 2), mv = new DataView(mapping.buffer);
        for (const c of chars) mv.setUint16(c.cid * 2, c.gid);
        const cidMap = await stream(mapping);
        const widths = chars.map(c => num(f.pdfWidth(c.gid))).join(' ');
        const cidFont = add(bytes('<< /Type /Font /Subtype /CIDFontType2 /BaseFont /' + name + ' /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor ' + descriptor + ' 0 R /DW 1000 /W [1 [' + widths + ']] /CIDToGIDMap ' + cidMap + ' 0 R >>'));
        let unicode = '/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n/CMapName /ZupuUnicode def\n/CMapType 2 def\n1 begincodespacerange\n<0000> <ffff>\nendcodespacerange\n';
        for (let i = 0; i < chars.length; i += 100) {
          const group = chars.slice(i, i + 100);
          unicode += group.length + ' beginbfchar\n';
          for (const c of group) {
            let utf16 = '';
            for (let j = 0; j < c.ch.length; j++) utf16 += hex(c.ch.charCodeAt(j));
            unicode += '<' + hex(c.cid) + '> <' + utf16 + '>\n';
          }
          unicode += 'endbfchar\n';
        }
        unicode += 'endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n';
        const toUnicode = await stream(bytes(unicode));
        fontId = add(bytes('<< /Type /Font /Subtype /Type0 /BaseFont /' + name + ' /Encoding /Identity-H /DescendantFonts [' + cidFont + ' 0 R] /ToUnicode ' + toUnicode + ' 0 R >>'));
      }
      const gs = alphaEntries.map(([alpha, name]) => '/' + name + ' ' + add(bytes('<< /Type /ExtGState /ca ' + alpha + ' /CA ' + alpha + ' >>')) + ' 0 R');
      const xobjects = [];
      for (const image of photoEntries) {
        const id = await stream(image.data, ' /Type /XObject /Subtype /Image /Width ' + image.width + ' /Height ' + image.height + ' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode', false);
        xobjects.push('/' + image.name + ' ' + id + ' 0 R');
      }
      const contents = await stream(content);
      objects[catalog] = bytes('<< /Type /Catalog /Pages ' + pages + ' 0 R >>');
      objects[pages] = bytes('<< /Type /Pages /Kids [' + page + ' 0 R] /Count 1 >>');
      objects[page] = bytes('<< /Type /Page /Parent ' + pages + ' 0 R /MediaBox [0 0 ' + num(pageW) + ' ' + num(pageH) + '] /Resources <<' + (fontId ? ' /Font << /F1 ' + fontId + ' 0 R >>' : '') + ' /ExtGState << ' + gs.join(' ') + ' >> /XObject << ' + xobjects.join(' ') + ' >> >> /Contents ' + contents + ' 0 R >>');
      const chunks = [bytes('%PDF-1.7\n%'), new Uint8Array([0xe2, 0xe3, 0xcf, 0xd3, 10])], offsets = [0];
      let offset = chunks.reduce((sum, c) => sum + c.length, 0);
      for (let i = 1; i < objects.length; i++) {
        offsets.push(offset);
        const chunk = concat([bytes(i + ' 0 obj\n'), objects[i], bytes('\nendobj\n')]);
        chunks.push(chunk); offset += chunk.length;
      }
      let xref = 'xref\n0 ' + objects.length + '\n0000000000 65535 f\r\n';
      for (let i = 1; i < offsets.length; i++) xref += String(offsets[i]).padStart(10, '0') + ' 00000 n\r\n';
      chunks.push(bytes(xref + 'trailer\n<< /Size ' + objects.length + ' /Root ' + catalog + ' 0 R >>\nstartxref\n' + offset + '\n%%EOF\n'));
      return concat(chunks);
    }
  };
  function alignment(w) {
    const a = state.textAlign;
    if (a === 'center') return w / 2;
    if (a === 'right' || (a === 'end' && state.direction !== 'rtl') || (a === 'start' && state.direction === 'rtl')) return w;
    return 0;
  }
  function baselineOffset(f, size) {
    const asc = f.ascent * size / f.units, desc = f.descent * size / f.units;
    switch (state.textBaseline) {
      case 'top': return asc;
      case 'hanging': return asc * 0.8;
      case 'middle': return (asc + desc) / 2;
      case 'bottom': case 'ideographic': return desc;
      default: return 0;
    }
  }
  for (const key of Object.keys(state)) {
    if (key === 'matrix' || key === 'dash') continue;
    Object.defineProperty(ctx, key, { enumerable: true, get: () => state[key], set: value => { state[key] = value; } });
  }
  return ctx;
}
