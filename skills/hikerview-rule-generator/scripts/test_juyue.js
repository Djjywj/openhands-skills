#!/usr/bin/env node
'use strict';
// 聚阅子程序（parse 对象）本地测试桩（PC 端）
//
// 聚阅子程序本质是一个 `let parse = {主页/分类/二级/搜索/解析/最新...}` 的 JS 对象，
// 运行在聚阅宿主运行时里（支持 ES6）。本桩用 Node 模拟海阔内置 API，验证解析逻辑：
//   ✅ 主页/分类/搜索 列表提取条数、标题/图片/链接
//   ✅ 二级 返回结构 {detail1,detail2,desc,img,line,list}
//   ✅ 解析 返回的可播直链
//   ✅ request/fetch（用 python3 同步抓取）、pdfa/pdfh/pd（mini_dom）、
//      getMyVar/putMyVar/getItem/setItem/getCookie/setCookie、base64、$ 等
//
// 不能测：验证码图片识别、$().input 用户交互、真机 cookie 持久化、UI 渲染。
//
// 用法:
//   node test_juyue.js <parse.js> --fn 主页
//   node test_juyue.js <parse.js> --fn 搜索 --kw 关键词
//   node test_juyue.js <parse.js> --fn 二级 --url https://站点/detail/1.html
//   node test_juyue.js <parse.js> --fn 解析 --url https://站点/play/1.html
//   node test_juyue.js <parse.js> --fn 分类 --fypage 1
//   --top N   打印前 N 条（默认 5）

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const DOM = require(path.join(__dirname, 'lib', 'mini_dom.js'));

function syncFetch(url, opts) {
  opts = opts || {};
  if (typeof url !== 'string') return '';
  if (url.indexOf('toast://') === 0 || url.indexOf('hiker://') === 0) return '';
  const helper = path.join(__dirname, 'fetch_url.py');
  const args = [helper, url, '--method', (opts.method || 'GET').toUpperCase(),
    '--headers', JSON.stringify(opts.headers || {}),
    '--timeout', String(Math.max(1, Math.round((opts.timeout || 15000) / 1000)))];
  if (opts.body !== undefined && opts.body !== null) {
    args.push('--body', typeof opts.body === 'string' ? opts.body : JSON.stringify(opts.body));
  }
  try { return execFileSync('python3', args, { maxBuffer: 64 * 1024 * 1024 }).toString('utf8'); }
  catch (e) { return ''; }
}

function parseArgs(argv) {
  const o = { fn: '主页', top: 5 };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--fn') o.fn = argv[++i];
    else if (a === '--kw') o.kw = argv[++i];
    else if (a === '--url') o.url = argv[++i];
    else if (a === '--fypage') o.fypage = argv[++i];
    else if (a === '--top') o.top = parseInt(argv[++i], 10) || 5;
    else if (a === '-h' || a === '--help') { console.log('用法: node test_juyue.js <parse.js> --fn 主页|分类|搜索|二级|解析|最新 [--kw 词] [--url 地址]'); process.exit(0); }
    else if (!a.startsWith('-') && !o.file) o.file = a;
  }
  return o;
}

function loadParse(file) {
  const code = fs.readFileSync(file, 'utf8');
  const store = {};
  const $ = (url, param) => ({
    rule: (fn) => String(url) + '@rule=js:' + $.toString(fn),
    lazyRule: (fn) => String(url) + '@lazyRule=' + (param ? param + '.' : '') + 'js:' + $.toString(fn),
    x5Rule: (fn) => String(url) + '@x5Rule=js:' + $.toString(fn),
    input: (fn) => String(url) + '@input=js:' + $.toString(fn),
    confirm: (fn) => String(url) + '@confirm=js:' + $.toString(fn),
    select: (fn) => String(url) + '@select=js:' + $.toString(fn),
  });
  $.toString = function (fn, ...args) {
    let s = '(' + String(fn) + ')';
    s += args.length ? '(' + args.map((a) => JSON.stringify(a)).join(',') + ')' : '()';
    return s;
  };
  $.stringify = (o) => JSON.stringify(o);
  $.type = (o) => Array.isArray(o) ? 'array' : (o === null ? 'null' : typeof o);

  const warn = (name) => () => { throw new Error('平台专属 API ' + name + '() 在 PC 桩中不可用（需真机），若规则分支用到请真机测试'); };

  const fn = new Function(
    'request', 'fetch', 'post', 'pdfa', 'pdfh', 'pd', 'parseDom', 'parseDomForHtml', 'parseDomForArray',
    'getVar', 'putVar', 'getMyVar', 'putMyVar', 'getItem', 'setItem', 'getCookie', 'setCookie',
    'base64Encode', 'base64Decode', 'md5', 'MY_PAGE', 'MY_URL', 'MY_HOME', 'MY_TYPE', 'refreshPage',
    'log', 'toast', '$', 'getHome', 'closeMe',
    'aesEncode', 'aesDecode', 'getCryptoJS', 'startProxyServer', 'evalPrivateJS', 'batchExecute', 'registerTask',
    code + '\n;return (typeof parse !== "undefined") ? parse : (typeof 接口 !== "undefined" ? 接口 : null);'
  );
  const parse = fn(
    syncFetch, syncFetch, (u, o) => syncFetch(u, Object.assign({}, o, { method: 'POST' })),
    DOM.parseDomForArray, DOM.parseDomForHtml, DOM.parseDom,
    DOM.parseDom, DOM.parseDomForHtml, DOM.parseDomForArray,
    (k, d) => store[k] !== undefined ? store[k] : d, (k, v) => { store[k] = v; },
    (k, d) => store['my_' + k] !== undefined ? store['my_' + k] : d, (k, v) => { store['my_' + k] = v; },
    (k, d) => store['item_' + k] !== undefined ? store['item_' + k] : d, (k, v) => { store['item_' + k] = v; },
    () => '', () => {},
    (s) => Buffer.from(String(s), 'utf8').toString('base64'),
    (s) => Buffer.from(String(s), 'base64').toString('utf8'),
    (s) => require('crypto').createHash('md5').update(String(s)).digest('hex'),
    process.env.MY_PAGE || '1', process.env.MY_URL || '', '', 'home', () => {},
    (...a) => console.log('[log]', ...a.map((x) => typeof x === 'object' ? JSON.stringify(x) : x)),
    () => {}, $, () => '', () => {},
    warn('aesEncode'), warn('aesDecode'), warn('getCryptoJS'), warn('startProxyServer'),
    warn('evalPrivateJS'), warn('batchExecute'), warn('registerTask')
  );
  return parse;
}

function printList(list, top, label) {
  list = Array.isArray(list) ? list : [];
  console.log('\n=== ' + label + ' ===');
  console.log('提取条数:', list.length);
  for (let i = 0; i < Math.min(top, list.length); i++) {
    const it = list[i] || {};
    console.log('\n[' + (i + 1) + ']');
    console.log('  标题:', it.title || '(空)');
    console.log('  简介:', String(it.desc || '').slice(0, 60));
    console.log('  图片:', String(it.img || it.pic_url || '').slice(0, 90));
    console.log('  链接:', it.url || '');
    console.log('  布局:', it.col_type || '');
  }
}

function main() {
  const o = parseArgs(process.argv);
  if (!o.file) { console.error('用法: node test_juyue.js <parse.js> --fn 主页|分类|搜索|二级|解析|最新 [--kw 词] [--url 地址]'); process.exit(2); }
  if (!fs.existsSync(o.file)) { console.error('[错误] 找不到 parse 文件: ' + o.file); process.exit(1); }
  if (o.fypage) process.env.MY_PAGE = o.fypage;
  if (o.url) process.env.MY_URL = o.url;

  console.log('parse 文件: ' + o.file + '  | 待测函数: ' + o.fn);
  const parse = loadParse(o.file);
  if (!parse) { console.error('[错误] 文件里没有找到 parse / 接口 对象'); process.exit(1); }
  if (typeof parse[o.fn] !== 'function') {
    console.error('[错误] parse 里没有函数 ' + o.fn + '，可用: ' + Object.keys(parse).filter((k) => typeof parse[k] === 'function').join(', '));
    process.exit(1);
  }

  try {
    if (o.fn === '二级') {
      const r = parse.二级(o.url || '');
      console.log('\n=== 二级返回结构 ===');
      console.log('标题:', (r && r.detail1) || '');
      console.log('副标题:', (r && r.detail2) || '');
      console.log('简介:', String((r && r.desc) || '').slice(0, 80));
      console.log('海报:', (r && r.img) || '');
      console.log('线路:', JSON.stringify((r && r.line) || []));
      const list = r && r.list;
      if (Array.isArray(list) && Array.isArray(list[0])) {
        console.log('多线路选集组数:', list.length);
        list.forEach((g, i) => console.log('  线路' + (i + 1) + ' 集数:', Array.isArray(g) ? g.length : 0));
        printList(list[0], o.top, '线路1 选集样例');
      } else {
        printList(list, o.top, '选集');
      }
    } else if (o.fn === '解析' || o.fn === '最新') {
      const r = parse[o.fn](o.url || '');
      console.log('\n=== 解析结果 ===');
      console.log(String(r));
    } else if (o.fn === '搜索') {
      printList(parse.搜索(o.kw || ''), o.top, '搜索结果');
    } else {
      printList(parse[o.fn](), o.top, o.fn);
    }
  } catch (e) {
    console.error('[错误] 执行 parse.' + o.fn + '() 失败: ' + e.message);
    process.exit(1);
  }
}

main();
