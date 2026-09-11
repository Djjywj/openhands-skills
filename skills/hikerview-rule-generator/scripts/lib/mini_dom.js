'use strict';
// 轻量 HTML 解析 + 海阔/Jsoup 风格选择器引擎（PC 测试桩用，零依赖）。
// 覆盖常见语法：tag / #id / .class / [attr] / [attr=v] / [attr$=v] / [attr^=v] / [attr*=v]
//   - && 向下选择   - ,n 取第 n 个(支持负)   - || 或   - -- 排除首个匹配   - Text / Html / @attr
// 说明：为 PC 端验证"爬得对不对"，非完整浏览器级实现，个别冷门语法可能不支持。

const VOID = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
  'link', 'meta', 'param', 'source', 'track', 'wbr']);
const RAW = new Set(['script', 'style', 'textarea', 'title', 'xmp']);

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };

function decodeEntities(s) {
  return String(s == null ? '' : s).replace(/&(#x?[0-9a-fA-F]+|[a-zA-Z]+);/g, function (m, code) {
    if (code[0] === '#') {
      const n = code[1] === 'x' || code[1] === 'X' ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10);
      return isNaN(n) ? m : String.fromCodePoint(n);
    }
    return ENTITIES[code] !== undefined ? ENTITIES[code] : m;
  });
}

function parseAttrs(str) {
  const attrs = {};
  const re = /([a-zA-Z0-9:_-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
  let m;
  while ((m = re.exec(str)) !== null) {
    const val = m[2] !== undefined ? m[2] : (m[3] !== undefined ? m[3] : (m[4] !== undefined ? m[4] : ''));
    attrs[m[1].toLowerCase()] = decodeEntities(val);
  }
  return attrs;
}

function addText(parent, text) {
  if (text === '' || text === undefined || text === null) return;
  parent.children.push({ tag: '#text', text: text, attrs: {}, children: [], parent: parent });
}

function parse(html) {
  html = String(html == null ? '' : html);
  const root = { tag: '#root', attrs: {}, children: [], parent: null };
  let cur = root, i = 0;
  const n = html.length;
  while (i < n) {
    const lt = html.indexOf('<', i);
    if (lt < 0) { addText(cur, html.slice(i)); break; }
    if (lt > i) addText(cur, html.slice(i, lt));
    if (html.startsWith('<!--', lt)) { const e = html.indexOf('-->', lt + 4); i = e < 0 ? n : e + 3; continue; }
    if (html.startsWith('<!', lt)) { const e = html.indexOf('>', lt); i = e < 0 ? n : e + 1; continue; }
    if (html.startsWith('</', lt)) {
      const e = html.indexOf('>', lt);
      if (e < 0) { addText(cur, html.slice(lt)); break; }
      const name = html.slice(lt + 2, e).trim().toLowerCase();
      let p = cur;
      while (p && p.tag !== name && p !== root) p = p.parent;
      if (p && p !== root) cur = p.parent;
      i = e + 1;
      continue;
    }
    const e = html.indexOf('>', lt);
    if (e < 0) { addText(cur, html.slice(lt)); break; }
    let tc = html.slice(lt + 1, e);
    let selfClose = tc.endsWith('/');
    if (selfClose) tc = tc.slice(0, -1);
    const m = tc.match(/^\s*([a-zA-Z0-9:_-]+)([\s\S]*)$/);
    if (!m) { addText(cur, html.slice(lt, e + 1)); i = e + 1; continue; }
    const tag = m[1].toLowerCase();
    const node = { tag: tag, attrs: parseAttrs(m[2] || ''), children: [], parent: cur };
    cur.children.push(node);
    i = e + 1;
    if (VOID.has(tag) || selfClose) continue;
    if (RAW.has(tag)) {
      const closeRe = new RegExp('</' + tag + '\\s*>', 'i');
      const rest = html.slice(i);
      const cm = closeRe.exec(rest);
      if (cm) { addText(node, rest.slice(0, cm.index)); i = i + cm.index + cm[0].length; }
      else { addText(node, rest); i = n; }
    } else {
      cur = node;
    }
  }
  return root;
}

function outerHTML(node) {
  if (!node) return '';
  if (node.tag === '#text') return node.text;
  const attrs = Object.keys(node.attrs).map(function (k) {
    return ' ' + k + '="' + String(node.attrs[k]).replace(/"/g, '&quot;') + '"';
  }).join('');
  if (VOID.has(node.tag)) return '<' + node.tag + attrs + '>';
  return '<' + node.tag + attrs + '>' + node.children.map(outerHTML).join('') + '</' + node.tag + '>';
}

function nodeText(node) {
  if (!node) return '';
  if (node.tag === '#text') return node.text;
  return node.children.map(nodeText).join('');
}

function descendants(node, out) {
  out = out || [];
  for (let k = 0; k < node.children.length; k++) {
    const c = node.children[k];
    if (c.tag !== '#text') { out.push(c); descendants(c, out); }
  }
  return out;
}

function parseSimple(sel) {
  sel = sel.trim();
  const m = sel.match(/^([a-zA-Z0-9*_-]+)?((?:[#.][\w-]+)*)((?:\[[^\]]*\])*)$/);
  const spec = { tag: null, id: null, classes: [], attrs: [] };
  if (!m) return spec;
  if (m[1] && m[1] !== '*') spec.tag = m[1].toLowerCase();
  const idc = m[2] || '';
  const idRe = /([#.])([\w-]+)/g;
  let x;
  while ((x = idRe.exec(idc)) !== null) {
    if (x[1] === '#') spec.id = x[2];
    else spec.classes.push(x[2]);
  }
  const attrRe = /\[([^\]]*)\]/g;
  while ((x = attrRe.exec(m[3] || '')) !== null) {
    const body = x[1].trim();
    const am = body.match(/^([\w-]+)\s*(?:([$^*~|!]?=)\s*(.*?))?$/);
    if (!am) continue;
    let val = am[3];
    if (val !== undefined && /^["']/.test(val)) val = val.slice(1, -1);
    spec.attrs.push({ name: am[1].toLowerCase(), op: am[2] || null, val: val });
  }
  return spec;
}

function matchSpec(node, spec) {
  if (!node || node.tag === '#text') return false;
  if (spec.tag && node.tag !== spec.tag) return false;
  if (spec.id && String(node.attrs.id || '') !== spec.id) return false;
  if (spec.classes.length) {
    const cls = String(node.attrs.class || '').split(/\s+/);
    for (let k = 0; k < spec.classes.length; k++) if (cls.indexOf(spec.classes[k]) < 0) return false;
  }
  for (let k = 0; k < spec.attrs.length; k++) {
    const a = spec.attrs[k];
    const has = Object.prototype.hasOwnProperty.call(node.attrs, a.name);
    const v = has ? String(node.attrs[a.name]) : '';
    if (a.op === null) { if (!has) return false; }
    else if (a.op === '=') { if (!has || v !== a.val) return false; }
    else if (a.op === '$=') { if (!has || v.slice(-a.val.length) !== a.val) return false; }
    else if (a.op === '^=') { if (!has || v.slice(0, a.val.length) !== a.val) return false; }
    else if (a.op === '*=') { if (!has || v.indexOf(a.val) < 0) return false; }
    else if (a.op === '!=') { if (has && v === a.val) return false; }
    else if (a.op === '~=') { if (!has || (' ' + v + ' ').indexOf(' ' + a.val + ' ') < 0) return false; }
    else if (a.op === '|=') { if (!has || (v !== a.val && v.indexOf(a.val + '-') !== 0)) return false; }
  }
  return true;
}

// 单步选择：nodes 下按 sel 找后代
function selectStep(nodes, sel) {
  sel = sel.trim();
  if (!sel) return nodes.slice();
  if (sel.indexOf('||') >= 0) {
    const alts = sel.split('||');
    for (let k = 0; k < alts.length; k++) {
      const r = selectStep(nodes, alts[k]);
      if (r.length) return r;
    }
    return [];
  }
  let index = null, base = sel;
  const idxM = sel.match(/,(-?\d+)\s*$/);
  if (idxM) { index = parseInt(idxM[1], 10); base = sel.slice(0, idxM.index); }
  let excludeFirst = false;
  if (base.indexOf('--') >= 0) {
    const parts = base.split('--');
    base = parts[parts.length - 1];
    excludeFirst = true;
  }
  const spec = parseSimple(base);
  const found = [];
  for (let k = 0; k < nodes.length; k++) {
    const all = descendants(nodes[k]);
    for (let j = 0; j < all.length; j++) if (matchSpec(all[j], spec)) found.push(all[j]);
  }
  let out = found;
  if (excludeFirst && out.length) out = out.slice(1);
  if (index !== null) {
    const real = index < 0 ? out.length + index : index;
    out = real >= 0 && real < out.length ? [out[real]] : [];
  }
  return out;
}

const ATTR_NAMES = /^(href|src|data-.+|title|alt|value|content|poster|action|id|class|style|width|height|target|rel|type|name)$/i;

function isExtractToken(step, nodes) {
  if (step === 'Text' || step === 'Html') return true;
  if (!/^[a-zA-Z][\w-]*$/.test(step)) return false;
  if (!nodes || !nodes.length) return false;
  if (ATTR_NAMES.test(step)) return true;
  for (let k = 0; k < nodes.length; k++) if (Object.prototype.hasOwnProperty.call(nodes[k].attrs, step)) return true;
  return false;
}

function extractValue(nodes, token) {
  if (!nodes.length) return '';
  if (token === 'Text') return decodeEntities(nodeText(nodes[0])).trim();
  if (token === 'Html') return outerHTML(nodes[0]);
  const v = nodes[0].attrs[token];
  return v === undefined ? '' : v;
}

// 通用求值：返回 { nodes, value }（value 非 null 表示末段是取值）
function evalRule(html, sel) {
  const root = typeof html === 'string' ? parse(html) : html;
  const steps = String(sel || '').split('&&');
  let nodes = [root];
  for (let k = 0; k < steps.length; k++) {
    const step = steps[k].trim();
    if (k === steps.length - 1 && nodes.length && isExtractToken(step, nodes)) {
      return { nodes: nodes, value: extractValue(nodes, step) };
    }
    if (!step) continue;
    nodes = selectStep(nodes, step);
    if (!nodes.length) break;
  }
  return { nodes: nodes, value: null };
}

// ---- 对外 API ----
function query(html, sel) { return evalRule(html, sel).nodes; }

function parseDom(html, sel) {
  const r = evalRule(html, sel);
  if (r.value !== null) return r.value;
  return r.nodes.length ? outerHTML(r.nodes[0]) : '';
}

function parseDomForHtml(html, sel) { return parseDom(html, sel); }

function parseDomForArray(html, sel) {
  const r = evalRule(html, sel);
  if (r.value !== null) return [r.value];
  return r.nodes.map(outerHTML);
}

// 基础 XPath 子集：支持 //tag、//*、[@attr=v]、[n]、/@attr
function xpathArray(html, expr) {
  const root = typeof html === 'string' ? parse(html) : html;
  let nodes = [root];
  const parts = String(expr).split('/').filter(function (p) { return p !== ''; });
  for (let k = 0; k < parts.length; k++) {
    let p = parts[k].trim();
    if (p.charAt(0) === '@') {
      const attr = p.slice(1);
      return nodes.map(function (nd) { return nd.attrs[attr] === undefined ? '' : nd.attrs[attr]; });
    }
    let index = null;
    const im = p.match(/\[(\d+)\]\s*$/);
    if (im) { index = parseInt(im[1], 10); p = p.slice(0, im.index); }
    let attrCond = null;
    const am = p.match(/\[@([\w-]+)\s*=\s*["']?([^"'\]]*)["']?\]/);
    if (am) { attrCond = { name: am[1].toLowerCase(), val: am[2] }; p = p.replace(am[0], ''); }
    const spec = parseSimple(p || '*');
    const next = [];
    for (let i = 0; i < nodes.length; i++) {
      const all = descendants(nodes[i]);
      for (let j = 0; j < all.length; j++) {
        if (!matchSpec(all[j], spec)) continue;
        if (attrCond) {
          const v = all[j].attrs[attrCond.name];
          if (v === undefined || String(v) !== attrCond.val) continue;
        }
        next.push(all[j]);
      }
    }
    nodes = index !== null ? (next[index - 1] ? [next[index - 1]] : []) : next;
  }
  return nodes.map(outerHTML);
}

function xpath(html, expr) { const a = xpathArray(html, expr); return a.length ? a[0] : ''; }

module.exports = {
  parse: parse,
  outerHTML: outerHTML,
  nodeText: nodeText,
  parseDom: parseDom,
  parseDomForHtml: parseDomForHtml,
  parseDomForArray: parseDomForArray,
  xpath: xpath,
  xpathArray: xpathArray,
  _select: query,
};
