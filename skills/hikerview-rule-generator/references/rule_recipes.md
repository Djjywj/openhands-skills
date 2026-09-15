# 写法骨架速查（从 2070 条真实规则统计出来的「大家实际怎么写」）

> 本文回答一个问题：**面对一个站点，`find_rule` 该套哪套骨架？**
> 数据来源：`kingkare/-` 仓库的 `海阔4904个小程序.json`（去重后 **2070 条**规则，其中 `find_rule` 以 `js:` 开头 **1828 条**）。
> 所有占比都是在这 2070/1828 条上实测，不是估计。

## 0. 先看骨架分布：生态里到底怎么写

| 骨架 | 条数 | 占比 | 什么时候用 |
|------|-----:|-----:|-----------|
| `hiker://` 协议驱动（跨规则/子页面/工具类） | 404 | 19.5% | 工具类、模块化引擎、多子页宿主 |
| **stui / 苹果CMS**：`getResCode()` + `parseDomForArray` | 393 | 19.0% | **影视站点第一梯队**：stui 模板站满地都是 |
| Q模板：`require(config.模板)` | 360 | 17.4% | 你已选定依赖「模板·Q」时 |
| JSON 接口：`JSON.parse(getResCode())` + `res.data` | 264 | 12.8% | 站点/App 有现成 JSON API（最省事） |
| 原生 DOM 链（`find_rule` **不是** `js:`） | 242 | 11.7% | 极简单列表页，不值得写 JS |
| 其它（`parseDomForArray` 系 71 + 通用 `parseDom`/`$()` 46 + 未归类 285） | 402 | 19.4% | 长尾，按下面骨架 A/B 的思路现场拼 |
| 加密代码 `evalPrivateJS` | 5 | 0.2% | 见 `crypto_sign.md`（小众，别默认用） |
| **合计** | **2070** | 100% | |

**结论**：影视站先用**骨架 C（stui）**试，接口站先用**骨架 A（JSON `res.data`）**，两者覆盖约 1/3 的生态；都不行再按 B/D 现场拼。

---

## 骨架 A：JSON 接口页（最省事，优先试）

**判据**：站点/App 走 XHR 返回 JSON（打开 F12 → Network → 看有没有 `*.json` / `api/` 返回 JSON）。
**占比**：264 条（12.8%）。

```json
"find_rule": "js:var json=JSON.parse(getResCode());var res={};\nvar d=json.data.list.map(function(x){return {title:x.name,pic_url:x.pic,desc:x.remarks,url:'/detail/'+x.id}});\nres.data=d;\nsetHomeResult(res);"
```

真实样例（500px，图片站，注意它连分号都省了但仍是合法 JS）：

```
js:var json=JSON.parse(getResCode());var res={};
var d=json.map(x=>({pic_url:x.url.p1,desc:x.uploaderInfo.nickName,title:x.id,url:x.url.p4}));
res.data = d;setHomeResult(res);
```

**要点**：
- `res.data = d; setHomeResult(res)` 是**分页/含头信息接口**的写法；单纯数组直接 `setResult(d)` 也行（官方文档：`setHomeResult`/`setSearchResult`/`setResult` 效果一致，App 自动识别回调类型）。
- 字段名用 `pic_url`（801 次）或 `img`（523 次）——**这两个都认**；`cover`/`image`/`thumb`/`picUrl` 在语料里**0 次**，别自创。

## 骨架 B：原生 DOM 链（不写 JS，规则里直接填选择器）

**占比**：242 条（11.7%）。**注意：这是少数派**，88% 的源都写 `js:`。
**判据**：单页纯 HTML 列表、无分页逻辑、字段一一对应。

```json
"find_rule": "div.stui-vodlist__box&&a&&title,0&&Text--a&&href--a&&data-original--span&&Text"
```
（`--` 依次对应 `title` / `url` / `pic_url` / `desc`，详见 `selector_syntax.md`）

## 骨架 C：stui / 苹果CMS 模板站（影视站第一梯队，19.0%）

**判据**：URL 形如 `/index.php/vod/show/id/1.html`，或页面含 `stui-vodlist` / `vodlist_item` class。
**占比**：393 条（**19.0%**），是影视源里最大单一骨架。

```json
"find_rule": "js:var d=[];\nvar html=getResCode();\nvar list=parseDomForArray(html,'.stui-vodlist&&li');\nfor(var i in list){\n  d.push({\n    title: pdfh(list[i],'a&&title'),\n    desc:  pdfh(list[i],'span,1&&Text'),\n    pic_url: pd(list[i],'a&&data-original'),\n    url: pd(list[i],'a&&href')\n  });\n}\nsetResult(d);"
```

真实样例（文学网，`#readTheme#` 是阅读类特有标签）：

```
js:
var d=[];
var html=getResCode();
var list=parseDomForArray(html,'div.main&&li');

for(var i in list){
d.push({
       title: pdfh(list[i], 'a&&Text'),
       desc: pdfh(list[i], 'p&&Text'),
       img: pd(list[i], ''),
       url: pd(list[i], 'a&&href') + "#readTheme#",
})
}
setResult(d);
```

**stui 常见二级/详情配套**（`sdetail_find_rule: "*"` 占全语料 60%，优先考虑免嗅）：
- 列表：`.stui-vodlist&&li` → `a&&title` / `a&&href` / `a&&data-original`
- 详情线路：`.stui-content__playlist&&li` → `a&&href` + `a&&Text`
- 详情简介：`.detail-content&&Text` 或 `.stui-content__desc&&Text`

> ⚠️ **`pd` 和 `pdfh` 不一样，这里最容易踩**：`pd`（=`parseDom`）会自动补全域名与 http 前缀，
> 而 `pdfh`（=`parseDomForHtml`）**不会**，原样返回。
> 所以**取链接一律用 `pd`**；取文本用 `pdfh`（文本不需要补全）。
> 本项目 PC 桩已按此行为对齐（见 `scripts/test_rule.js` 的 `joinUrl`）。

## 骨架 D：`hiker://` 协议驱动（工具 / 模块化 / 多子页）

**占比**：404 条（19.5%）。用来**拼装其它规则**而不是爬站。

```
js:
var newWindow = true
var homePage = JSON.parse(request('hiker://page/home?rule=' + MY_RULE.title)).rule
eval(homePage)
```

**要点**：
- `MY_RULE.title` 取当前规则标题，`hiker://page/<path>?rule=<标题>` 调同包内其它页面。
- 常用于「模块化单例引擎」（见 `rule_patterns.md` 模式 I）：主规则 `eval` 出引擎，所有入口转发到同一份解析逻辑。
- 这类规则通常配合 `type: tool` / `type: all`。

---

## 返回结果 API 怎么选（实测）

| API | 语料出现 | 用途 |
|-----|--------:|------|
| `setResult(d)` | **761 次（41.6%）** | **万能**：首页/搜索/二级/详情都用它，App 自动识别回调类型 |
| `setHomeResult(res)` | 6+ | 首页；接 `{data:[...]}` 对象 |
| `setSearchResult(res)` | 3+ | 搜索；与 `setHomeResult` 同构 |
| `return JSON.stringify(...)` | 81 | 等价于 `setResult`（少见，但可行） |
| `return d` 直接返回数组 | **5（0.3%）** | ⚠️ 几乎没人这么写，**别用** |

> 官方文档明确：`setHomeResult` 与 `setSearchResult` **可混用**，两者效果和 `setResult` 一致（软件自动识别回调类型）。
> 所以**拿不准就用 `setResult(d)`**。

## API 使用率（写源时按需查，1828 条 js: find_rule 实测）

| API | 次数 | 占比 | 说明 |
|-----|-----:|-----:|------|
| `setResult` | 761 | 41.6% | 返回结果（首选） |
| `require(` | 673 | 36.8% | 依赖/模块（Q模板等） |
| `JSON.parse` | 516 | 28.2% | 接口站 |
| `parseDom` | 475 | 26.0% | DOM 解析 |
| `MY_URL` | 447 | 24.5% | 当前真实 URL |
| `fetch(` | 413 | 22.6% | 规则内二次请求 |
| `pd` / `pdfh` / `pdfa` | 329 / 263 / 241 | 18/14/13% | 三个 DOM 解析 |
| `getMyVar` / `putMyVar` | 257 / 118 | 14.1 / 6.5% | 跨页面变量 |
| `request(` | 249 | 13.6% | 同 `fetch` |
| `try{` / `catch` | 215 / 338 | 11.8 / 18.5% | **容错，只有 18% 的源写了** |
| `refreshPage` | 199 | 10.9% | 动态刷新 |
| `getItem` / `setItem` | 59 / 45 | 3.2 / 2.5% | 持久化 |
| `getParam` | **4** | **0.2%** | 主用 `MY_URL` + 自己切；`getParam` 很少见 |
| `getCryptoJS` | 3 | 0.2% | 加密站（见 `crypto_sign.md`） |

> 📌 **两个反直觉结论**：
> 1. **`try/catch` 只有 18% 的源写** —— 但**建议你写**（失败降级比裸崩好，见 `pitfalls.md`）。
> 2. **`getParam` 只有 0.2% 用** —— 语料里大家直接用 `MY_URL` 字符串切分。
>    本库推荐 `getParam`（更安全），但遇到他人规则读不懂时，别以为它调错了。

## 列表项字段（语料合计出现次数）

| 字段 | 次数 | 备注 |
|------|-----:|------|
| `title` | 2752 | 必需 |
| `url` | 2670 | 必需 |
| `col_type` | 2038 | 逐项设布局（见 `col_type.md`） |
| `desc` | 1392 | |
| `pic_url` | 801 | **与 `img` 二选一** |
| `img` | 523 | **与 `pic_url` 二选一** |
| `extra` | 499 | 透传参数给详情页 |
| `headers` | 223 | 单条自定义请求头 |
| `id` | 82 | 配合 `updateItem` |
| `name` / `type` / `click` / `group` | 30 / 17 / 7 / 4 | 冷门 |

## 骨架代码的通用约定（跑过 PC 桩）

- **`d.push({...})` 是绝对主流**（1817 次），`var d=[]` 起手（972 次）。
- **`for(var i in list)`** 比 `.forEach` 更常见（1183 vs 309）——`for...in` 是老写法，对数组也能用，且**兼容旧版引擎**。
- **函数体直接写，不要包 `$.toString`**：`find_rule` 里 `$.toString` 只有 **181/1828（10%）**，
  且**几乎都用在别处**——实测出现最多的场景是 `addListener('onClose', $.toString(()=>{...}))`(30)、
  `push($.toString(...))`(24) 这类**需要把函数序列化成字符串存起来/当参数传的场合**；
  `js:` 后面直接写语句即可。（官方文档也只在 `@rule=js:`、`setLastChapterRule('js:'+...)`
  这类**需要嵌进 url 字符串**的场景才要求 `$.toString`。）
- 语言特性其实**新旧混用**（ES5 是书里写的约定，不是生态铁律）：含箭头函数 `=>` 的 **25%**、
  含 `let` 的 **35.8%**、含 `const` 的 **16.7%**、含模板字符串的 **5.0%**。
  → 结论：**ES5 写法（`var` + `function`）最保险**，但看到别人用 ES6 别惊讶，也不是不能用。
- `hiker://empty` 出现 836 次：用作「纯 JS 首页」的占位 url（见 `rule_format.md` §7）。
- 剥掉自己拼的 `##` 前缀取真实地址，主流是 **`MY_URL = MY_URL.replace('hiker://empty##','')`（181 次）**，
  其次 `MY_URL = MY_URL.split('##')[1]`（101 次）。两者都是传参常用套路（见 `pitfalls.md` §二）。

## 自检

写完 `find_rule` 后，**先在本机跑一遍**再谈真机：

```bash
node scripts/test_rule.js 你的规则.json --html 保存的页面.html --top 5
```

看到「提取条数」与字段对得上再继续；链接应是**补全后的绝对地址**（若原样 `/xxx` 说明你误用了 `pdfh` 取 href）。
