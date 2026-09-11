// 用真实的接口数据在 node 里跑规则 JS，验证收集逻辑 + 统计耗时/条数
import fs from 'fs';

const rulePath = process.argv[2];
const cls = process.argv[3] || '300';
const useBatch = process.argv[4] !== 'nobatch';
const rule = JSON.parse(fs.readFileSync(rulePath, 'utf8'));
const which = process.env.RULE_JS === 'searchFind' ? 'searchFind' : 'find_rule';
const KW = process.env.RULE_KW || '';
const JS = rule[which].replace(/^js:/, '');
const UA = 'com.ss.android.ugc.aweme/300000 (Linux; U; Android 13; zh_CN; Pixel; Build/TQ3A; )';
const BASE = JS.match(/var BASE='([^']+)'/)[1];
const pageUrl = (p) => BASE + '&refresh_index=' + p;
const MY_URL = which === 'searchFind'
  ? rule.search_url.split(';get;')[0].replace('**', encodeURIComponent(KW))
  : rule.url.split(';get;')[0].replace('fyclass', cls).replace('fypage', '1');

const cache = {};
const missing = [];
const urls = [];
for (let p = 1; p <= 14; p++) urls.push(pageUrl(p));

const t0 = Date.now();
await Promise.all(urls.map(async (u) => {
  try {
    const r = await fetch(u, { headers: { 'User-Agent': UA, 'Referer': 'https://www.douyin.com/' } });
    cache[u] = await r.text();
  } catch (e) { cache[u] = ''; }
}));
const netMs = Date.now() - t0;

let result = null;
const sandbox = {
  getResCode: () => cache[pageUrl(1)] || '',
  setResult: (x) => { result = x; },
  fetch: (u, o) => {
    if (!(u in cache)) { missing.push(u); return ''; }
    return cache[u] || '';
  },
  MY_URL: MY_URL,
  getParam: (n) => (String(n) === 'min_sec' ? cls : ''),
  log: (...a) => console.log('[log]', ...a),
};
const args = ['getResCode', 'setResult', 'fetch', useBatch ? 'batchFetch' : 'bf_unused', 'MY_URL', 'getParam', 'log'];
if (useBatch) {
  sandbox.batchFetch = (reqs) => reqs.map((r) => sandbox.fetch(r && r.url, r && r.options));
} else {
  sandbox.bf_unused = undefined;
}

const t1 = Date.now();
new Function(...args, JS)(...args.map((k) => sandbox[k]));
const jsMs = Date.now() - t1;

const list = Array.isArray(result) ? result : [];
console.log('模式: %s | 分类=%s | 并发取数 %dms（%d 页）| JS 执行 %dms',
  useBatch ? 'batchFetch' : '无batchFetch(逐个fetch)', cls, netMs, urls.length, jsMs);
console.log('输出条数: %d | 未缓存命中的请求: %d', list.length, missing.length);
list.slice(0, 14).forEach((it, i) => {
  console.log('  [%d] %s || %s', i, it.title, it.desc);
});
