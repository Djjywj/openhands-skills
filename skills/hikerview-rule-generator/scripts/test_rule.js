#!/usr/bin/env node
'use strict';
// 海阔视界 rule.json 本地测试桩（PC 端）
//
// 在电脑上模拟 Hiker JSEngine 跑 find_rule / searchFind / detail_find_rule 的解析逻辑，
// 并模拟占位符替换拼出真实 URL，用来验证规则"爬得对不对"，不必每次都上真机。
//
// 能力（本桩覆盖）:
//   ✅ 目标页面真实 HTTP 响应（HTML / JSON 结构）
//   ✅ find_rule / searchFind / detail_find_rule 的 JS 提取逻辑
//   ✅ 占位符替换 fyclass/fypage/fyarea/fysort/fyyear/**: 拼真实 URL
//   ✅ 原生 DOM 选择器 parseDom/parseDomForHtml/parseDomForArray（内置 mini_dom 引擎）
//   ✅ 常用 API：fetch/request/post(同步, 走 python3 fetch_url.py)、base64、md5、
//      getParam、getVar/putVar/getMyVar/getItem、$ 工厂、MY_URL/MY_PAGE 等
//   ✅ 本地文件/图片 API 垫片：fileExist/getPath/writeHexFile/writeFile/readFile/saveImage
//      （hiker://files/ 映射到系统临时目录，验证「加密封面落地文件」类优化）
//   ℹ️ ES 语法提示（ES6+ 兼容性提示，旧版海阔仅支持 ES5）
//
// 不能测（需真机 / 海阔视界 app）:
//   ❌ 实际 UI 渲染长相、播放嗅探
//   ❌ aes/rsa/CryptoJS、startProxyServer、loadJavaClass、registerDNS 等平台专属 API
//   ❌ 符号链接自动补全、app 内置 header 修饰符是否真的生效
//   ❌ @lazyRule / x5Rule 在真实 WebView 里的执行
//
// 用法:
//   node test_rule.js <rule.json> [选项]
//
//   --rule <name>          find_rule(默认) | searchFind | detail_find_rule
//   --html <file.html>     本地 HTML 喂给 getResCode()
//   --url  <https://...>   在线抓取页面喂给 getResCode()
//   --kw   <关键词>        替换 search_url 的 **
//   --fyclass 1 --fypage 1 --fyarea 美国 --fysort hits --fyyear 2024
//   --top  <N>             打印前 N 条样例（默认 5）
//   --dump <out.json>      把解析结果写到 JSON
//   -h / --help            帮助
//
// 环境: Node.js v16+（推荐 v18+），无需 npm 依赖；同步 fetch 需 python3。

const fs = require('fs');
const path = require('path');
const os = require('os');
const https = require('https');
const http = require('http');
const zlib = require('zlib');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const DOM = require(path.join(__dirname, 'lib', 'mini_dom.js'));

function printHelp() {
  console.log(`
海阔视界 rule.json 本地测试桩（PC 端）

用法:
  node test_rule.js <rule.json> [选项]

  --rule <name>          find_rule(默认) | searchFind | detail_find_rule
  --html <file.html>     本地 HTML 喂给 getResCode()
  --url  <https://...>   在线抓取页面（忽略 SSL / 跟随重定向 / 带 referer）
  --kw   <关键词>        替换 search_url 的 **
  --fyclass 1 --fypage 1 --fyarea 美国 --fysort hits --fyyear 2024
  --top  <N>             打印前 N 条样例（默认 5）
  --dump <out.json>      结果写入 JSON
  --selftest             自检桩本身（校验 pd 自动补全 / pdfh 不补全语义），不跑规则
  -h / --help            显示帮助

说明: 本桩验证"爬得对不对"，不验证 UI 渲染与播放嗅探（需真机）。
`);
}

function parseArgs(argv) {
  const o = { rule: 'find_rule', top: 5, fy: {}, ruleJson: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--rule') o.rule = argv[++i];
    else if (a === '--html') o.html = argv[++i];
    else if (a === '--url') o.url = argv[++i];
    else if (a === '--kw') o.kw = argv[++i];
    else if (a === '--top') o.top = parseInt(argv[++i], 10) || 5;
    else if (a === '--dump') o.dump = argv[++i];
    else if (a === '--fyclass') o.fy.fyclass = argv[++i];
    else if (a === '--fypage') o.fy.fypage = argv[++i];
    else if (a === '--fyarea') o.fy.fyarea = argv[++i];
    else if (a === '--fysort') o.fy.fysort = argv[++i];
    else if (a === '--fyyear') o.fy.fyyear = argv[++i];
    else if (a === '--vid') o.vid = argv[++i];
    else if (a === '-h' || a === '--help') { printHelp(); process.exit(0); }
    else if (a === '--selftest') o.selftest = true;
    else if (!a.startsWith('-') && o.ruleJson === null) o.ruleJson = a;
  }
  return o;
}

function substitutePlaceholders(url, fy, kw) {
  let u = url;
  const map = { fyclass: fy.fyclass, fypage: fy.fypage, fyarea: fy.fyarea, fysort: fy.fysort, fyyear: fy.fyyear };
  for (const k in map) if (map[k] !== undefined) u = u.split(k).join(map[k]);
  if (kw !== undefined) u = u.split('**').join(encodeURIComponent(kw));
  return u;
}

// 忠实模拟海阔对规则 URL 的处理（见 hikerView 源码）：
//   url;方法;编码;{头};body
// GET/无方法：MY_URL = 带 query 的 url；getParam 从 query 取值。
// POST：海阔在第一个 ? 处切开，query 作为 POST body（HttpParser.post 的
//       onSuccess(finalUrl) 且 finalUrl=ss[0]），因此 MY_URL 丢掉 query，
//       getParam('t') 会读成空——这正是「点分类内容不变」的根因。
function hikerModelUrl(raw) {
  const seg = String(raw == null ? '' : raw).split(';');
  const headRaw = seg[0];
  const method = (seg[1] || 'get').toLowerCase();
  let urlRaw = headRaw;
  // 海阔顺序：POST 先按 ASCII ? 切分（此时 ？？ 还是全角、不会命中），
  // 再在 post() 里 decodeConflictStr 把 ？？＆＆；； 还原。顺序反了就测不准。
  if (method === 'post') {
    const qi = headRaw.indexOf('?');
    if (qi >= 0) urlRaw = headRaw.slice(0, qi);
  }
  const url = urlRaw
    .replace(/？？/g, '?').replace(/＆＆/g, '&').replace(/；；/g, ';');
  const params = {};
  const qi = url.indexOf('?');
  if (qi >= 0) {
    url.slice(qi + 1).split('&').forEach((kv) => {
      const i = kv.indexOf('=');
      if (i > 0) params[kv.slice(0, i)] = kv.slice(i + 1);
    });
  }
  return { url, params, method };
}

// 忠实模拟海阔 pd 的「自动补全链接」：相对地址用 MY_URL 补成绝对地址。
// 官方文档：pd/parseDom 会自动补全域名与 http 前缀；而 **pdfh/parseDomForHtml
// 不会**（"完全返回解析到的内容"），pdfa 同理。第四参数可覆盖补全基准。
// 少了这步差异，PC 桩会把 '/detail/1' 原样输出（或给 pdfh 补错），
// 让人误以为规则写错了、进而做出错误的"修复"。
function joinUrl(href, base) {
  const s = String(href == null ? '' : href);
  if (!s || s.indexOf('<') >= 0) return s;
  if (/^(https?:|hiker:|file:|data:|ftp:|\/\/)/i.test(s)) return s;
  if (!base) return s;
  try { return new URL(s, base).toString(); } catch (e) { return s; }
}

function fetchLive(url, referer, depth) {
  depth = depth || 0;
  return new Promise((resolve, reject) => {
    if (depth > 5) return reject(new Error('重定向次数过多'));
    const lib = url.startsWith('https') ? https : http;
    const req = lib.get(url, { headers: { 'User-Agent': 'Mozilla/5.0', 'Referer': referer || '' }, rejectUnauthorized: false }, (res) => {
      if ([301, 302, 303, 307, 308].includes(res.statusCode) && res.headers.location) {
        res.resume();
        return resolve(fetchLive(new URL(res.headers.location, url).toString(), referer, depth + 1));
      }
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        let buf = Buffer.concat(chunks);
        const enc = (res.headers['content-encoding'] || '').toLowerCase();
        try {
          if (enc === 'gzip') buf = zlib.gunzipSync(buf);
          else if (enc === 'deflate') buf = zlib.inflateSync(buf);
        } catch (e) { /* ignore */ }
        resolve(buf.toString('utf8'));
      });
    });
    req.on('error', reject);
    req.setTimeout(30000, () => req.destroy(new Error('抓取超时')));
  });
}

// 规则内部调用 fetch()/request()：用 python3 同步抓取（海阔 fetch 是同步的）
function syncFetch(url, opts) {
  opts = opts || {};
  if (typeof url !== 'string') return '';
  const helper = path.join(__dirname, 'fetch_url.py');
  const args = [helper, url, '--method', (opts.method || 'GET').toUpperCase(),
    '--headers', JSON.stringify(opts.headers || {}), '--timeout', String(Math.max(1, Math.round((opts.timeout || 15000) / 1000)))];
  if (opts.body !== undefined && opts.body !== null) {
    args.push('--body', typeof opts.body === 'string' ? opts.body : JSON.stringify(opts.body));
  }
  let out = '';
  try {
    out = execFileSync('python3', args, { maxBuffer: 64 * 1024 * 1024 }).toString('utf8');
  } catch (e) {
    return '';
  }
  if (opts.withHeaders || opts.withStatusCode) {
    return JSON.stringify({ body: out, headers: {}, statusCode: 200 });
  }
  return out;
}

// CryptoJS 最小垫片：只实现规则常用的 AES + enc.Utf8 + mode/pad
// 用 Node crypto 还原 CryptoJS 在「WordArray 作为 key/iv」时的行为：
//   - 字符串 key 长度决定 AES-128/192/256；mode 用 CBC/ECB（ECB 无 iv）
//   - encrypt 返回 { toString(): base64密文 }
//   - decrypt 返回 { toString(enc): 明文 }
function cjAES(op, data, key, cfg) {
  const keyStr = (key && key.__utf8 !== undefined) ? key.__utf8 : String(key);
  const dataStr = (data && data.__utf8 !== undefined) ? data.__utf8 : String(data);
  const ivStr = (cfg && cfg.iv) ? ((cfg.iv.__utf8 !== undefined) ? cfg.iv.__utf8 : String(cfg.iv)) : null;
  const mode = (cfg && cfg.mode === 0) ? 'ecb' : 'cbc';
  const alg = 'aes-' + (Buffer.byteLength(keyStr) * 8) + '-' + mode;
  const pad = !(cfg && cfg.pad === 0);
  const iv = mode === 'ecb' ? null : Buffer.from(ivStr, 'utf8');
  if (op === 1) {
    const c = crypto.createCipheriv(alg, Buffer.from(keyStr, 'utf8'), iv);
    c.setAutoPadding(pad);
    return Buffer.concat([c.update(Buffer.from(dataStr, 'utf8')), c.final()]).toString('base64');
  }
  const d = crypto.createDecipheriv(alg, Buffer.from(keyStr, 'utf8'), iv);
  d.setAutoPadding(pad);
  return Buffer.concat([d.update(Buffer.from(dataStr, 'base64')), d.final()]).toString('utf8');
}

function getCryptoJSShim() {
  return 'var CryptoJS={' +
    'enc:{' +
    'Utf8:{parse:function(s){return{__utf8:String(s)};},stringify:function(w){return (w&&w.__utf8!==undefined)?w.__utf8:String(w);}},' +
    'Hex:{__enc:"hex",stringify:function(w){return (w&&w.__bin!==undefined)?Buffer.from(w.__bin,"binary").toString("hex"):"";}},' +
    'Base64:{__enc:"base64",' +
    'parse:function(b){var buf=Buffer.from(String(b).replace(/\\s+/g,""),"base64");' +
    'return{__bin:buf.toString("binary"),toString:function(enc){return (enc&&enc.__enc==="hex")?buf.toString("hex"):buf.toString("base64");}};},' +
    'stringify:function(w){return (w&&w.__bin!==undefined)?Buffer.from(w.__bin,"binary").toString("base64"):"";}}' +
    '},' +
    'mode:{CBC:1,ECB:0},pad:{Pkcs7:1,NoPadding:0},' +
    'AES:{encrypt:function(m,k,c){return{toString:function(){return __cjAES(1,m,k,c);}};},' +
    'decrypt:function(t,k,c){return{toString:function(e){return __cjAES(0,t,k,c);}};}}' +
    '};';
}

function lintES5(code) {
  const rules = [
    { re: /\b(const|let)\s+/, msg: 'const / let（请用 var）' },
    { re: /=>/, msg: '箭头函数 =>（请用 function(){}）' },
    { re: /`/, msg: '反引号模板字符串（请用字符串拼接 +）' },
    { re: /\$\{/, msg: '模板字符串插值 ${}' },
    { re: /\bclass\s+\w/, msg: 'class 类' },
    { re: /\b(async|await|yield)\b/, msg: 'async / await / yield' },
    { re: /\bimport\s+/, msg: 'import 模块' },
    { re: /\bexport\s+/, msg: 'export 模块' },
    { re: /for\s*\([^)]*\bof\b/, msg: 'for...of（请用普通 for）' },
  ];
  return rules.filter((r) => r.re.test(code)).map((r) => r.msg);
}

function runRule(code, html, top, ruleObj) {
  let out = null;
  const store = {};

  // ---- 文件/图片 API 垫片（模拟海阔的 hiker://files 域，落到系统临时目录）----
  // 让规则里「图片解密后落地成本地文件、列表传 file://」的优化能在 PC 端跑通验证。
  const HIKER_FILES_ROOT = path.join(os.tmpdir(), 'hiker_files_shim');
  const shimToAbs = (p) => {
    const s = String(p);
    if (s.indexOf('hiker://files/') === 0) return path.join(HIKER_FILES_ROOT, s.slice('hiker://files/'.length));
    if (s.indexOf('file://') === 0) return s.slice('file://'.length);
    return s;
  };
  const fileExist = (p) => { try { return fs.existsSync(shimToAbs(p)); } catch (e) { return false; } };
  const getPath = (p) => {
    const s = String(p);
    if (s.indexOf('file://') === 0) return s;
    return 'file://' + shimToAbs(s);
  };
  const writeHexFile = (p, hex) => {
    const abs = shimToAbs(p);
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, Buffer.from(String(hex), 'hex'));
    return 'file://' + abs;
  };
  const writeFile = (p, content) => {
    const abs = shimToAbs(p);
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, String(content));
    return 'file://' + abs;
  };
  const readFile = (p) => fs.readFileSync(shimToAbs(p), 'utf8');
  const saveImage = (url, p) => {
    const first = String(url).split('||')[0];
    const abs = shimToAbs(p);
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    if (first.indexOf('data:') === 0) {
      fs.writeFileSync(abs, Buffer.from(first.slice(first.indexOf(',') + 1), 'base64'));
    } else {
      fs.writeFileSync(abs, Buffer.from(syncFetch(first), 'binary'));
    }
    return 'file://' + abs;
  };
  const getResCode = () => html;
  const setResult = (d) => { out = d; };
  const log = (...a) => console.log('[rule log]', ...a.map((x) => typeof x === 'object' ? JSON.stringify(x) : x));
  const noop = () => '';
  const unsupported = (name) => () => {
    throw new Error('Hiker 平台专属 API ' + name + '() 在 PC 桩中不可用，请真机测试该规则段');
  };
  const $ = (url, param) => ({
    rule: (fn) => String(url) + '@rule=js:' + $.toString(fn),
    lazyRule: (fn) => String(url) + '@lazyRule=' + (param ? param + '.' : '') + 'js:' + $.toString(fn),
    x5Rule: (fn) => String(url) + '@x5Rule=js:' + $.toString(fn),
    input: (fn) => String(url) + '@input=js:' + $.toString(fn),
    confirm: (fn) => String(url) + '@confirm=js:' + $.toString(fn),
    select: (fn) => String(url) + '@select=js:' + $.toString(fn),
    b64: () => Buffer.from(String(url), 'utf8').toString('base64'),
  });
  $.toString = function (fn, ...args) {
    let s = '(' + String(fn) + ')';
    if (args.length) s += '(' + args.map((a) => JSON.stringify(a)).join(',') + ')';
    else s += '()';
    return s;
  };
  $.stringify = (o) => JSON.stringify(o);
  $.type = (o) => Array.isArray(o) ? 'array' : (o === null ? 'null' : typeof o);
  $.log = log;
  $.require = (p) => { throw new Error('$.require(' + p + ') 依赖外部模块/子页面，PC 桩不支持，请真机测试'); };

  const myRule = ruleObj || {};
  // 海阔的 POST 传参约定：URL 内的英文问号在规则里要写成中文问号 ？？，
  // app 解析 URL 时会还原成英文 ?。这里模拟同样的还原，便于本地测详情传参。
  const hikerUrl = String(myRule.url || '').replace(/？？/g, '?').replace(/；；/g, ';');
  // 忠实模拟海阔：MY_URL 与 getParam 都来自“最终请求 URL”。
  // 关键差异——POST 规则海阔会在 ? 处切开、把 query 当 POST body（HttpParser.post 的
  // onSuccess(finalUrl) 且 finalUrl=ss[0]），于是 MY_URL 丢掉 query，getParam 读不到！
  const modeled = hikerModelUrl((myRule._myUrl != null) ? myRule._myUrl : hikerUrl);
  const myUrl = modeled.url;
  const myUrlParams = modeled.params;
  const paramsErrors = [];

  try {
    const fn = new Function(
      'getResCode', 'setResult', 'setHomeResult', 'setSearchResult', 'setError', 'log', 'toast',
      'parseDom', 'parseDomForHtml', 'parseDomForArray', 'pd', 'pdfh', 'pdfa',
      'xpath', 'xpathArray', 'xpa',
      'fetch', 'request', 'post', 'batchFetch', 'bf',
      'base64Encode', 'base64Decode', 'md5', 'encodeStr', 'decodeStr',
      'getParam', 'getVar', 'putVar', 'clearVar', 'getMyVar', 'putMyVar', 'clearMyVar',
      'getItem', 'setItem', 'getPublicItem', 'setPublicItem', 'getCookie', 'setCookie',
      'MY_URL', 'MY_PAGE', 'MY_HOME', 'MY_TYPE', 'MY_RULE', 'MY_PARAMS', 'MY_NAME',
      'MOBILE_UA', 'PC_UA', 'refreshPage', 'back', '$',
      'aesDecode', 'aesEncode', 'rsaEncrypt', 'rsaDecrypt', 'getCryptoJS', 'evalPrivateJS', '__cjAES',
      'startProxyServer', 'fetchCodeByWebView', 'cacheM3u8', 'clearM3u8Ad', 'clearM3u8AdLazy',
      'batchExecute', 'syncExecute', 'registerDNS', 'sharePaste', 'parsePaste',
      'downloadFile', 'saveFile', 'readFile', 'loadJavaClass', 'registerTask',
      'fileExist', 'getPath', 'writeHexFile', 'writeFile', 'saveImage',
      code
    );
    fn(
      getResCode, setResult, setResult, setResult, log, log, noop,
      DOM.parseDom, DOM.parseDomForHtml, DOM.parseDomForArray, ((h, s, b) => joinUrl(DOM.parseDom(h, s), b || myUrl)), DOM.parseDomForHtml, DOM.parseDomForArray,
      DOM.xpath, DOM.xpathArray, DOM.xpathArray,
      syncFetch, syncFetch, (u, o) => syncFetch(u, Object.assign({}, o, { method: 'POST' })),
      (reqs) => Array.isArray(reqs) ? reqs.map((r) => syncFetch(r && r.url, r && r.options)) : [],
      (reqs) => Array.isArray(reqs) ? reqs.map((r) => syncFetch(r && r.url, r && r.options)) : [],
      (s) => Buffer.from(String(s), 'utf8').toString('base64'),
      (s) => Buffer.from(String(s), 'base64').toString('utf8'),
      (s) => crypto.createHash('md5').update(String(s)).digest('hex'),
      (s) => String(s), (s) => String(s),
      (k, d) => (myUrlParams[k] !== undefined) ? myUrlParams[k] : ((ruleObj && ruleObj._params && ruleObj._params[k] !== undefined) ? ruleObj._params[k] : d),
      (k, d) => store[k] !== undefined ? store[k] : d, (k, v) => { store[k] = v; }, (k) => { delete store[k]; },
      (k, d) => store['my_' + k] !== undefined ? store['my_' + k] : d, (k, v) => { store['my_' + k] = v; }, (k) => { delete store['my_' + k]; },
      (k, d) => store['item_' + k] !== undefined ? store['item_' + k] : d, (k, v) => { store['item_' + k] = v; },
      (k, d) => store['pub_' + k] !== undefined ? store['pub_' + k] : d, (k, v) => { store['pub_' + k] = v; },
      () => '', () => {},
      myUrl, String((ruleObj && ruleObj._page) || 1), myUrl.replace(/^(https?:\/\/[^/]+).*$/, '$1'),
      (ruleObj && ruleObj._type) || 'home', myRule, {}, '海阔视界',
      'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
      noop, noop, $,
      unsupported('aesDecode'), unsupported('aesEncode'), unsupported('rsaEncrypt'), unsupported('rsaDecrypt'),
      getCryptoJSShim, unsupported('evalPrivateJS'), cjAES, unsupported('startProxyServer'),
      unsupported('fetchCodeByWebView'), unsupported('cacheM3u8'), unsupported('clearM3u8Ad'),
      unsupported('clearM3u8AdLazy'), unsupported('batchExecute'), unsupported('syncExecute'),
      unsupported('registerDNS'), unsupported('sharePaste'), unsupported('parsePaste'),
      unsupported('downloadFile'), unsupported('saveFile'), readFile,
      unsupported('loadJavaClass'), unsupported('registerTask'),
      fileExist, getPath, writeHexFile, writeFile, saveImage
    );
  } catch (e) {
    console.log('\n[错误] 执行规则 JS 失败: ' + e.message);
    if (/平台专属 API/.test(e.message)) {
      console.log('       → 该规则段用了 PC 桩无法模拟的平台 API，请真机测试。');
    }
    return null;
  }

  const list = Array.isArray(out) ? out : [];
  console.log('\n=== 解析结果 ===');
  console.log('提取条数:', list.length);
  const n = Math.min(top, list.length);
  for (let i = 0; i < n; i++) {
    const it = list[i] || {};
    console.log('\n[' + (i + 1) + ']');
    console.log('  标题:', it.title || '(空)');
    console.log('  简介:', String(it.desc || '').slice(0, 60));
    console.log('  海报:', String(it.img || it.pic_url || '').slice(0, 90));
    console.log('  链接:', it.url || '');
    console.log('  布局:', it.col_type || '');
  }
  if (list.length === 0) {
    console.log('\n[警告] 解析出 0 条。常见原因: 字段名与站点真实结构不符、HTML 转义未处理、' +
      '占位符 URL 拼错抓到空页、或该段用了平台专属 API。');
  }
  return list;
}

// 自检：确保 pd 自动补全、pdfh/pdfa 不补全（与官方文档一致）。
// 这是本桩最容易「悄悄失真」的地方——补错了会让人误改正确的规则。
function selfTest() {
  const base = 'https://example.com/index.php/vod/show/id/1.html';
  const cases = [
    ['pd 补全相对链接', joinUrl('/detail/1', base), 'https://example.com/detail/1'],
    ['pd 补全无斜杠相对链接', joinUrl('detail/2', base), 'https://example.com/index.php/vod/show/id/detail/2'],
    ['pd 不动绝对链接', joinUrl('https://cdn.x/a.jpg', base), 'https://cdn.x/a.jpg'],
    ['pd 不动 hiker://', joinUrl('hiker://empty', base), 'hiker://empty'],
    ['pd 不动 data:', joinUrl('data:image/png;base64,AAA', base), 'data:image/png;base64,AAA'],
    ['pd 不动片段/HTML', joinUrl('<a href="x">', base), '<a href="x">'],
    ['无基准时原样返回', joinUrl('/detail/1', ''), '/detail/1'],
  ];
  let bad = 0;
  console.log('=== test_rule.js 自检：pd 自动补全语义 ===\n');
  for (const [name, got, want] of cases) {
    const ok = got === want;
    if (!ok) bad++;
    console.log(`${ok ? '✓' : '✗'} ${name}\n    得到: ${got}\n    期望: ${want}`);
  }
  // pdfh/pdfa 必须保持原样（不补全）
  const passthrough = [DOM.parseDomForHtml('<a href="/d/1">x</a>', 'a&&href', ''), DOM.parseDomForArray('<a href="/d/1">x</a>', 'a', '')];
  const okPass = passthrough[0] === '/d/1';
  if (!okPass) bad++;
  console.log(`${okPass ? '✓' : '✗'} pdfh 取 href 不补全（应为 /d/1，实际 ${passthrough[0]}）`);
  console.log(bad ? `\n✗ 自检失败 ${bad} 项\n` : '\n✓ 自检通过\n');
  process.exit(bad ? 1 : 0);
}

async function main() {
  const o = parseArgs(process.argv);
  if (o.selftest) return selfTest();
  if (!o.ruleJson) { printHelp(); process.exit(2); }
  if (!fs.existsSync(o.ruleJson)) { console.error('[错误] 找不到 rule.json: ' + o.ruleJson); process.exit(1); }
  let rule;
  try { rule = JSON.parse(fs.readFileSync(o.ruleJson, 'utf8').replace(/^\ufeff/, '')); }
  catch (e) { console.error('[错误] 读取/解析 rule.json 失败: ' + e.message); process.exit(1); }

  console.log('规则: ' + (rule.title || '?') + '  | type=' + (rule.type || '?') + '  | 待测规则=' + o.rule);

  const urlField = o.rule === 'searchFind' ? 'search_url' : 'url';
  const baseUrl = rule[urlField] || '';
  if (!baseUrl) { console.log('\n[警告] 规则无 ' + urlField + ' 字段，无法拼 URL。'); return; }

  const realUrl = substitutePlaceholders(baseUrl, o.fy, o.kw);
  const refMatch = baseUrl.match(/\{referer@([^}]+)\}/);
  const referer = refMatch ? refMatch[1] : '';
  console.log('\n=== 占位符替换后的真实 URL ===');
  console.log(realUrl);
  console.log('提取到的 referer 修饰符: ' + (referer || '(无)'));

  let html = null;
  if (o.html) {
    if (!fs.existsSync(o.html)) { console.error('[错误] 找不到 HTML 文件: ' + o.html); process.exit(1); }
    html = fs.readFileSync(o.html, 'utf8');
  } else if (o.url) {
    console.log('\n[正在在线抓取] ' + o.url);
    try { html = await fetchLive(o.url, referer); }
    catch (e) { console.error('[错误] 在线抓取失败: ' + e.message); process.exit(1); }
    console.log('抓取字节数: ' + Buffer.byteLength(html, 'utf8'));
  } else {
    console.log('\n[提示] 未提供 --html 或 --url，仅展示真实 URL（跳过解析执行）。');
    console.log('        想验证解析逻辑请加 --html <file.html> 或 --url <https://...>');
    return;
  }

  let code = rule[o.rule] || '';
  code = code.replace(/^js:\s*/, '');
  const esHits = lintES5(code);
  if (esHits.length) {
    console.log('\nℹ️ [ES 语法提示] 检测到 ES6+ 语法（兼容性提示，不算错误）：');
    esHits.forEach((m) => console.log('   - ' + m));
    console.log('   说明: 新版海阔 JSEngine 支持 ES6+（官方文档示例即用 let/const/箭头函数），');
    console.log('         但旧版仅支持 ES5。本库默认写 ES5 以兼容所有版本；真机实测 ES6 可用则可忽略本提示。');
    console.log('         注意: 本桩跑在 Node 上，ES6 一定通过 —— 所以“PC 通过”不能证明“真机通过”。');
  }
  if (!code.trim()) { console.log('\n[警告] ' + o.rule + ' 为空，无内容可测。'); return; }

  const r2 = Object.assign({}, rule, { _page: o.fy.fypage, _type: o.rule === 'searchFind' ? 'search' : 'home' });
  // 真机上 MY_URL 就是当前页地址；用 --url 测试详情时把它当作 MY_URL。
  if (o.url) r2.url = o.url;
  // 忠实模拟海阔的 MY_URL / getParam：只以“最终请求 URL”为准。
  // 注意：不再用 _params 直接塞 t/p，否则会掩盖 POST 丢 query 的真机 bug。
  const modelSrc = o.url ? o.url : realUrl;
  const model = hikerModelUrl(modelSrc);
  r2._myUrl = model.url;
  r2._myUrlParams = model.params;
  console.log('海阔模型: 方法=' + model.method + '  MY_URL=' + model.url);
  console.log('          MY_URL 参数=' + JSON.stringify(model.params) + '  (getParam 只认这里)');
  r2._params = Object.assign({}, o.fy);
  if (o.vid !== undefined) r2._params.vid = o.vid;
  if (o.kw !== undefined) { r2._params.key = o.kw; r2._params.keyword = o.kw; r2._params.kw = o.kw; r2._params.k = o.kw; }
  const list = runRule(code, html, o.top, r2);
  if (o.dump) {
    try { fs.writeFileSync(o.dump, JSON.stringify(list || [], null, 2), 'utf8'); console.log('\n结果已写入 ' + o.dump); }
    catch (e) { console.error('[错误] 写入 dump 失败: ' + e.message); }
  }
}

main().catch((e) => { console.error('[异常] ' + e.message); process.exit(1); });
