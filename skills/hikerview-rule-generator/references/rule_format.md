# 海阔视界（Hiker View）规则格式规范

本文件是生成规则时必须遵循的字段与语法参考。所有字段均来自真实可用的 `rule.json`（视频站 360、Q站 等）逆向整理，**已验证有效**。

## 1. 完整字段表

| 字段 | 含义 | 示例 / 说明 |
|------|------|------------|
| `last_chapter_rule` | 上集记忆规则 | 通常为 `""` |
| `title` | 规则显示名 | `"示例视频站"` |
| `author` | 作者 | `"WorkBuddy"` |
| `url` | 首页/列表/分类 URL | 支持占位符，API 需加修饰符，见 §4 |
| `version` | 版本号 | 整数或 `25090800` 这类日期串 |
| `col_type` | 列表页布局类型 | 见 §3 |
| `class_name` | 分类显示名 | `电影&剧集&动漫`（用 `&` 分隔） |
| `type` | 站点类型 | `video` / `audio` / `image` / `other` / `tool` |
| `class_url` | 分类对应 ID | `1&2&3`，与 `class_name` 一一对应 |
| `area_name` / `area_url` | 地区筛选（可选） | 通常为 `""` |
| `sort_name` / `sort_url` | 排序筛选（可选） | 通常为 `""` |
| `year_name` / `year_url` | 年份筛选（可选） | 通常为 `""` |
| `find_rule` | 列表解析规则 | DOM 链 或 `js:`，见 §5 |
| `search_url` | 搜索 URL | 用 `**` 占位关键词 |
| `group` | 规则分组显示 | `②视频` / `③动漫` / `工具` |
| `searchFind` | 搜索结果解析规则 | 同 `find_rule` 语法 |
| `detail_col_type` | 详情页布局类型 | 视频站推荐 `text_3`（选集列表），见 §3 |
| `detail_find_rule` | 详情页解析（提取选集/播放地址） | 同 `find_rule` 语法 |
| `sdetail_col_type` | 二级详情（播放页）布局 | 通常 `movie_1` |
| `sdetail_find_rule` | 二级详情解析规则 | `"*"` = 让 app 自动嗅探播放页媒体，见 §5.4 |
| `ua` | 请求 UA 标识 | `pc` / `mobile`，视频站常 `pc` |

> `class_name` / `class_url` 必须数量一致、顺序对应。`area/sort/year` 留空字符串即可，不影响基本功能。
> 完整字段以 EcoHub 为基准（纯规则无依赖模板见 `assets/templates/video_rule.json`），`sdetail_col_type`/`sdetail_find_rule`/`ua` 是可选的二级详情嗅探字段。

## 2. 四类规则对应的 `type` 与 `group`

| 用户选择 | `type` | `group` | `detail_col_type` | 详情要点 |
|---------|--------|---------|-------------------|---------|
| 视频 | `video` | `②视频` | `movie_1` | 播放地址加 `#isVideo=true#` |
| 音频 | `audio` | `④音频` | `movie_1` | 直链 mp3/m4a，一般无需标记 |
| 图片 | `image` | `①图片` | `pic_1` | 详情只展示大图 `pic_url` |
| 杂类 | `other` | `⑤杂类` | `text_3` | 文本/网页型，按需自定义 |

> 分组序号是约定俗成的展示顺序，不影响功能，照填即可。

## 3. 常用 `col_type` 取值

- 列表页：`movie_3`（海报网格+信息）、`movie_1`、`movie_3_marquee`（滚动海报）、`text_3`（剧集列表）、`pic_1`（大图网格）
- 文本类：`text_1`（分组标题）、`text_2`（单行文本项）、`text_center_1`（居中说明）、`input`（输入框）
- 详情页：`movie_1`、`pic_1`、`text_3`

## 4. URL 占位符与修饰符

- `fyclass`：分类 ID（由 `class_url` 代入）
- `fypage`：页码（列表/搜索翻页）
- `fyarea`：地区筛选值（由 `area_url` 代入，点击筛选时替换）
- `fysort`：排序筛选值（由 `sort_url` 代入）
- `fyyear`：年份筛选值（由 `year_url` 代入）
- `**`：搜索关键词占位（URL 编码后代入）

> ⚠️ **筛选必坑**：只要定义了 `area_name`/`area_url`、`sort_name`/`sort_url`、`year_name`/`year_url` 这些筛选字段，**`url` 里必须放置对应的 `fyarea`/`fysort`/`fyyear` 占位符**，否则点击筛选时 app 无处填充、直接丢弃，筛选"看起来不生效"。占位符名与 `fyclass`/`fypage` 同源，是 Hiker 引擎内置约定（非自定义参数名）。
- **API 类必加修饰符**：在 URL 末尾追加 `;get;UTF-8;{referer@https://站点域名}`，例如：
  ```
  https://api.x.com/list?cat=fyclass&page=fypage;get;UTF-8;{referer@https://x.com}
  ```
- **图片防盗链**：封面地址后加 `@Referer=https://站点域名`（或 `@Referer=` + 图片自身域名）。

## 5. `find_rule` 两种写法

### 5.1 原生 DOM 链（适合简单 HTML 站点，无需写 JS）

格式：`容器&&列表项;标题字段&&Text;图片字段&&src;简介字段&&Text;链接字段&&href`

字段按位置映射：①标题 ②图片 ③简介 ④链接。`Text`=取文本；`src`/`href`/`data-original`=取属性；可链式 `a&&href` 钻取子元素属性。

真实例子（Q站）：
```
.fed-list-info&&li;.fed-list-title&&Text;a&&data-original;.fed-text-center&&Text;a&&href
```

### 5.2 `js:` JavaScript（最灵活，推荐用于 JSON API 与复杂页面）

> ℹ️ **JS 语法版本**：新版海阔 JSEngine 支持 ES6+（官方示例即用 `let`/`const`/箭头函数），**旧版仅支持 ES5**。本库默认用 `var` / `function` / 普通 `for` 以兼容所有版本——这是**兼容性约定，不是语法禁令**；真机实测 ES6 可用则可放开。`scripts/test_rule.js` / `validate_rule.py` 的 ES6 探测仅作提示，不判错。
>
> 取响应文本建议用三级兜底，兼容海阔 / 嗅觉(Feather) 等不同引擎的全局变量差异：
> `var raw = (typeof getResCode === 'function') ? getResCode() : ((typeof result !== 'undefined' && result) ? result : (typeof input !== 'undefined' ? input : ''));`

```js
js:
var d = [];
var json = JSON.parse(getResCode());      // 取响应文本并解析
var list = json.data.list || json.data || [];
for (var i = 0; i < list.length; i++) {
  var it = list[i];
  d.push({
    title: it.title || it.name || '',
    desc:  it.remarks || it.year || '',
    img:   (it.cover || it.pic || '') + '@Referer=https://x.com',
    url:   'https://x.com/detail?id=' + it.id,
    col_type: 'movie_3'
  });
}
setResult(d);   // 输出；老版本若报错改 setHomeResult(d)
```

关键 API：
- `getResCode()`：获取当前请求的响应（HTML 或 JSON 文本）
- `setResult(d)` / `setHomeResult(d)`：输出解析结果（数组）
- `parseDom(html, sel)`、`parseDomForArray(html, sel)`、`parseDomForHtml(html, sel)`：原生 DOM 解析
- `fetch(url, {headers})`、`base64Decode(str)`、`MY_URL`、`getParam('id')`
- 视频直链后加 `#isVideo=true#` 让 app 识别为可播视频
- 详情 url 可加 `#immersiveTheme#` 进入沉浸播放

> ⚠️ **海阔 lazyRule 正确写法**（海阔工具文档）：`$(url, param).lazyRule(func)` 工厂，等价字符串 `url + '@lazyRule=' + param + '.js:' + $.toString(func)`。`param` 是"解析 url 的表达式"（选择器，可空字符串 `''`），`func` 是处理响应的函数，函数内 `input` = 当前 url 响应、`fetch` 同步可用。**不要在普通字符串上直接 `.lazyRule()`**（会报 `TypeError: 对象 ... 不存在方法 lazyRule`——字符串没这方法，得用 `$()` 工厂或 `$.toString`）。
>
> ❌ **`@lazyRule=` 形式实际不可用**：func 内含 `#isVideo=true#` 等 `# ? ; &` 字符会被海阔 url 解析器截断（`#` 截 fragment、`?` 截 query、`;` 截修饰符），导致 lazyRule 解析失败报"链接为空，规则有误"。海阔的 `$().b64()` 也不支持编码 func 本身。
>
> ✅ **按需取真实地址（进详情 0 秒）实际不可行**（海阔 API 限制）。
> ✅ **推荐方案：detail_find_rule 同步 `fetch`**：进详情多等几秒，但无 lazyRule 语法风险。手机/电影（≤4 集）≈2-4 秒，电视剧（≥16 集）≈16-32 秒。配合 `try/catch` 兜底，失败降级中转页直链。

### 5.3 详情页取真实播放 / 音频地址的常见套路

- **直链在 `<video src>` / `<audio src>`**：`detail_find_rule` 里用 `parseDom(html, 'video&&src')` 取出直链；或设 `sdetail_find_rule: "*"`，让 app 默认嗅探页面里的媒体标签。
- **直链在 JS 变量**（如 `var now='...'`、`videourl:"..."`、`"playUrl":"..."`）：从 `html` 用正则提取。注意 SSR / JSON 里常把 `"` 转义成 `\"`，要先 `html.replace(/\\"/g, '"')` 再 `JSON.parse` 或匹配。
- **直链需二次请求**（中转页 → 播放器 → m3u8）：`fetch` 拿到的中转页可能是多种播放器：① `<iframe src="...">`（再 fetch iframe 取 m3u8）；② 阿里云 Aliplayer `new Aliplayer({"source":"...m3u8"})`（直接正则 `["']?source["']?\s*:\s*"([^"]+\.m3u8[^"]*)"` 提取，注意 `"source"` 和 `source` 两种写法都要兼容）。整体套 `try/catch`，失败降级回中转页直链。
- 任何视频直链末尾都要加 `#isVideo=true#` 让 app 识别为可播视频。

> ⚠️ **详情页「链接为空，规则有误」排查**：如果详情项由列表跳转带入 id，且详情 url 是 POST，
> 列表项 url 里的英文 `?` 会把 `;post;` 截断，导致 id 传不进去、详情 API 返回「缺少参数」，
> 最终详情页所有项都没有 url → app 报「链接为空，规则有误」。
> 修复：POST 链接的参数分隔符写中文 `？？`（见 `url_tags.md` §2），并在规则里用
> `MY_URL.match(/[?？&]vid=(\d+)/)` 兜底取 id（同时优先 `getParam`、再 `MY_PARAMS`）。

### 5.4 二级详情嗅探（X5 免嗅）：`sdetail_find_rule: "*"` + `sdetail_col_type`

当选集 url 指向一个「播放页」（点进去后页面里直接含 m3u8 或 `<video>`/`<audio>` 标签），可以让海阔**自动嗅探**，不必自己写二次请求。这正是 EcoHub 的做法：

```json
"detail_col_type": "text_3",          // 详情页=选集列表
"detail_find_rule": "js:...顶部 pic_1 卡 + 线路 text_1 + 选集 text_2，url 指向播放页...",
"sdetail_col_type": "movie_1",        // 二级详情=播放页布局
"sdetail_find_rule": "*",             // 让 app 自动嗅探播放页里的媒体
"ua": "pc"
```

- 点选集 url → 海阔请求播放页 → `sdetail_find_rule="*"` 让 X5 内核自动嗅探页内 m3u8 → 播放。
- **适用**：播放页直接返回 m3u8 / `<video>` 标签（JSON API 站如 EcoHub）。
- **不适用**：播放页是 `<iframe>` 内嵌第三方播放器、或 m3u8 藏在 JS 变量里（如帝国CMS 的 `/e/DownSys/play/` 中转页、阿里云 Aliplayer `"source"`）。**海阔嗅探不穿透 iframe、不执行 JS**，这类站点只能用 §5.3 的 detail_find_rule 同步 fetch。

## 6. 完整视频规则示例（JSON API 型）

```json
{
  "last_chapter_rule": "",
  "title": "示例视频站",
  "author": "WorkBuddy",
  "url": "https://api.x.com/list?cat=fyclass&page=fypage;get;UTF-8;{referer@https://x.com}",
  "version": 1,
  "col_type": "movie_3",
  "class_name": "电影&剧集&动漫",
  "type": "video",
  "class_url": "1&2&3",
  "area_name": "", "area_url": "",
  "sort_name": "", "sort_url": "",
  "year_name": "", "year_url": "",
  "find_rule": "js:\nvar d=[];var j=JSON.parse(getResCode());var l=j.data.list||[];for(var i=0;i<l.length;i++){var it=l[i];d.push({title:it.title,desc:it.remarks,img:(it.cover||'')+'@Referer=https://x.com',url:'https://x.com/detail?id='+it.id,col_type:'movie_3'});}setResult(d);",
  "search_url": "https://api.x.com/search?wd=**&page=fypage;get;UTF-8;{referer@https://x.com}",
  "group": "②视频",
  "searchFind": "js:\nvar d=[];var j=JSON.parse(getResCode());var l=j.data.list||[];for(var i=0;i<l.length;i++){var it=l[i];d.push({title:it.title,desc:it.remarks,img:(it.cover||'')+'@Referer=https://x.com',url:'https://x.com/detail?id='+it.id,col_type:'movie_3'});}setResult(d);",
  "detail_col_type": "movie_1",
  "detail_find_rule": "js:\nvar d=[];var html=getResCode();\n/* TODO: 从 html 提取 m3u8/播放地址，每行一项 */\nd.push({title:'第1集',url:'https://x.com/play/1.m3u8#isVideo=true#',col_type:'text_2'});\nsetResult(d);"
}
```

## 7. 生成与校验要点

1. 生成前先用 `curl -L -A "Mozilla/5.0" 站点URL` 抓首页，确认是 HTML 还是 JSON API。
2. 若返回 JSON：直接写 `js:` 规则解析 `data` 数组；API URL 必须加 `;get;UTF-8;{referer@...}`。
3. 若返回 HTML：优先用原生 DOM 链；结构复杂再用 `js:` + `parseDomForArray`。
4. 详情页必须实测：视频能否播放（看 `#isVideo=true#` 是否生效）、图片防盗链 `@Referer=` 是否正确。
5. 写完后用 `scripts/validate_rule.py` 校验字段完整性，再用 `scripts/test_rule.js` 在 PC 上模拟 JSEngine 验证 `find_rule`/`searchFind`/`detail_find_rule` 的解析逻辑与占位符 URL（详见 SKILL.md「PC 端测试方法」）。UI 渲染与播放嗅探仍需真机确认。

> ✅ **海阔「点一级列表 → 触发二级解析」的真正条件（2026-09-11 用真实样例 + 本地桩确认）**：
> **列表项 `url` 必须带规则修饰符**（`;get;UTF-8;{referer@…}` 或 `;post;…`），海阔才会把它当
> 「规则链接」交给规则引擎请求，进而执行 `detail_find_rule`；**没修饰符就一律当普通网页用 WebView 打开**。
>
> 三个实测对照：
> | 列表项 url 写法 | 点进去的结果 |
> |---|---|
> | 纯 HTML 详情页 `https://www.mdzyapi.com/vod/89447/` | ❌ 直接打开网页，规则不执行 |
> | 纯 JSON 接口 `…/provide/vod?ac=detail&ids=89447` | ❌ 弹出接口 JSON 原文 |
> | 接口地址 **+ `;get;UTF-8;{referer@…}`** | ✅ 走规则引擎 → `detail_find_rule` 解析出选集 |
>
> 权威依据：`examples/4e63v.rule.json`（version 9，真机跑通）的 `find_rule` 里
> `url:'https://a37p.oqd79.com/base/getTimeStamp？？vid='+it.id+';post;UTF-8;'+'{Content-Type@application/json&&Did@1&&…}'`
> —— 详情链接就是**带修饰符的接口地址**，交给 `detail_find_rule`（`detail_col_type: text_3`）解析。
> GET 用英文 `?`；POST 的参数分隔符必须用中文 `？？`（否则 `;post;` 被截断，见 url_tags.md §2）。
> `detail_find_rule` 内用 `getResCode()` 取响应；推荐结构：`pic_1` 头图卡 + 简介 + `text_1` 线路名 +
> `text_2` 选集（`extra:{cls:'playlist'}` 标记连续选集）。
>
> 另：`url = JSON.stringify({urls:[…],names:[…]})`（官方「视频多线路」）在纯规则真机上**不被识别**，
> 别指望它当选集用；要选集就走上面的修饰符 + `detail_find_rule`。
> `@rule=js:` 内联二级也能用，但代码里 `; ? & #` 要转义（官方写法 `；；`/`＆＆＆＆`），非必要不用。

## 8. 小程序依赖打包（require.json + libs.zip）——「聚阅/juyue 框架」规则

部分规则（尤其来自 `gitee.com/zetalpha/hikerview` 等仓库的「聚阅」框架规则）导出时**不止一个 `rule.json`**，还会带两个文件。这正是第 2 步「规则是否依赖程序/模板」要追问的来源。

### 8.1 三个文件的角色
| 文件 | 作用 |
|------|------|
| `rule.json` | 规则本体。此类规则通常用 `hiker://empty`（伪协议，不走普通网页列表）、`$.require(...)` 加载外部库、`#@rule=js:...` 内联 lazyRule、`hiker://page/<名>` 子页面。 |
| `require.json` | **依赖声明清单**（数组）。每项：`{"url":下载源, "file":设备本地安装路径(含 md5 哈希), "proxy":"", "accessTime":时间戳}`。告诉 app 规则需要哪些外部 JS 库、装到设备哪个 `libs/<md5>.js`。 |
| `libs.zip` | **打包好的依赖库真身**。内部文件名 = `require.json` 各 `file` 字段的 md5 哈希（一一对应）。导入时 app 按 `require.json` 的 `file` 路径解压安装到设备，使 `$.require` 离线可用，无需联网下载。 |

> ⚠️ **只导入 `rule.json` 会失败**：`$.require` 找不到 `require.json`/`libs.zip` 声明的库（如 `x5ui.js`、`Ver.js`）→ 规则直接跑不起来。必须连包一起导入。

### 8.2 常见被依赖的库（聚阅框架）
- `x5ui.js`：聚阅 UI 框架库，提供自定义页面渲染（卡片、轮播、图片服务器 host 等 UI 能力）。
- `Ver.js`：版本/资源清单字典，声明 SlideX 轮播等子资源（jquery、slick 等）的版本号与本地/网络路径。
- 规则内部自带的 `hiker://page/erji`（「二级」详情页）是 **rule.json 内子页面**，不是外部库，`libs.zip` 里没有也正常，**不是缺失依赖**。

### 8.3 与 PC 测试桩的兼容
`scripts/test_rule.js` 模拟纯 `find_rule`/`searchFind`/`detail_find_rule` 的 `getResCode`/`setResult`，并内置轻量 DOM 引擎（支持 `parseDom`/`parseDomForHtml`/`parseDomForArray`/`xpath`）与同步 `fetch`/`request`，因此**普通爬虫规则（含用 `parseDom`、`fetch` 的 JS 规则）可在 PC 验证解析**。但**不支持** `$.require`、`hiker://` 伪协议、`#@rule=js:` 内联、`aes/rsa/CryptoJS`、`startProxyServer` 等平台能力。因此「聚阅框架 / 跨规则程序 / 库打包」这类规则**无法在 PC 完整验证**，只能海阔视界 app 真机测试；收到此类包时，直接交真机验证 UI/播放，不要硬套 test_rule.js。聚阅子程序（`parse` 对象）改用 `scripts/test_juyue.js` 单独验证。

### 8.4 跨规则「程序/模板」依赖（hiker:// + $.exports）—— `type: tool` 程序
与 8.1 的「库打包」**无关**的另一种依赖：主规则依赖另一个 **`type: tool` 的「程序」规则**，通过**跨规则 hiker:// 调用**复用其导出的函数（典型如「解析助手 / 配置助手」类工具）。
- **主规则侧引用**：`$.require("hiker://page/mulParse?rule=配置助手").mulParse(vipUrl)`，或 `request('hiker://page/home?rule=配置助手&type=设置')`。
- **程序侧导出**：在 `pages` 里 `path` 为 `mulParse` 的页面 rule 中写 `$.exports.mulParse = function(vipUrl, ...){...}`。
- **识别特征**：主规则 `rule.json` 里出现 `hiker://page/...?rule=<某标题>` 或 `$.require("hiker://...")`；被依赖的程序 `type: tool`、`url: hiker://empty##`、`pages` 数组定义若干 `path` 页并用 `$.exports` 导出函数。
- ⚠️ **查找键是标题（title）**：`?rule=配置助手` 按程序规则的 `title` 精确匹配，所以被依赖的程序**必须按原标题安装**，改名或没装都会导致主规则「解析」失败。
- **典型分工**：主规则（如「360魔改」）负责列表/搜索/详情；「解析」（视频页→可播直链）委托给「配置助手」的 `mulParse`。
- PC 测试桩同样不支持（`$.require` hiker://、`$.exports`、`hiker://page`），只能真机验证。

### 8.5 聚阅（juyue）框架宿主 + 子程序（本 skill 依赖机制的集大成）

`聚阅`（`type: all`）是一个**模块化框架宿主**：它本身不抓具体站点，而是提供运行时 + UI +「子程序」加载器，让第三方「子程序」（每个=一个站点爬虫，如「多多影视」「360魔改」）插进来用。前面 §8.1/§8.4 那些包都跑在它上面。

**包结构（4 件套）**：
| 文件 | 作用 |
|------|------|
| `rule.json` | 框架宿主。`preRule` 用 `@include importGM` 并初始化 `config.聚阅`（经 `$.require('ghproxy').getSrcHome()` 取得远程源码源，cnb.cool 的 JuyueTest 仓库）；`find_rule` 为 `if(config.聚阅){ require(config.聚阅); yiji(); }`——加载真实运行时后调 `yiji()` 渲染子程序列表；`searchFind` 调 `sousuo()`。 |
| `require.json` + `libs.zip` | 框架运行时核心库（如 `SrcJu.js`/`SrcJuMethod.js`/`SrcJuPublic.js`/`ghproxy.js`/`global` 插件，共 19 个），见 §8.1 打包机制。 |
| `data.zip` | 框架数据/资源：`plugins/`（hikerPop、pinyin-match、gzip 等插件）、`template/`（**子程序模板**：`采集cms.js`/`parseCode.js`/`GetAppApi.js`）、`juItem.json`（**子程序注册表**，初始 `{}`，导入后写入）。 |

**「导入子程序」机制**：宿主 `pages` 里提供 `name:"云口令导入", path:"import"` 与 `name:"导入确认页", path:"importConfirm"` 两个页面——用户拿到某子程序的「云口令」（分享码）后，在聚阅内「云口令导入」粘贴，经「导入确认页」确认即安装进 `juItem.json`，子程序随即出现在列表。开发者也可用 `data.zip/template/` 下的模板新建子程序。

**完整生态关系**：
```
聚阅（框架宿主, type:all, 含运行时+UI+子程序加载器）
 ├─ 子程序：每个 = 一个站点爬虫（多多影视 / 360魔改 / …），经「云口令导入」装入 juItem.json
 └─ 配套工具：配置助手（type:tool 解析引擎），子程序用 hiker:// 调其 mulParse 做解析（见 §8.4）
```
> ⚠️ 聚阅宿主、子程序、配置助手**三者需配套安装**。子程序依赖 `config.聚阅` 指向的远程运行时，且常 `$.require` §8.1 的库；调解析则依赖 §8.4 的 `配置助手` 按标题安装。整条链 PC 测试桩均不支持，只能真机验证。

### 8.6 自包含聚阅子程序（如「阅动漫」）—— 运行时打进自己包里

与 §8.5 宿主、§8.1 纯库打包都不同，存在一种**子程序把自己需要的聚阅运行时一起打包**的变体，代表即「阅动漫」：

**包结构（3 件套，无 data.zip）**：
| 文件 | 作用 |
|------|------|
| `rule.json` | `type: all`、`url: hiker://empty`，是个**聚阅子程序**（动漫聚合）。`preRule` 用 `putMyVar('remoteUrl','https://14719.kstore.space/阅动漫.json')` 指向云端源；靠 `MY_RULE`/`getMyVar`/`putMyVar`（由打包进来的运行时库提供）运行。`config.聚阅` 计数为 0——它**不桥接宿主**，自己定 `remoteUrl` 拉云端内容。 |
| `require.json` + `libs.zip` | 仅 1 个库 `bd834…js`（约 400KB），正是**聚阅框架运行时本体**（含 `MY_RULE`/`config`/`getMyVar`/`hiker://` 全套基础设施）。即「子程序 + 它依赖的运行时」合并成一个包，可脱离宿主独立跑。 |

**「里面包含子程序」的含义**：该子程序从云端 `阅动漫.json` 聚合了 9 类资源（`types`：漫画/视频/短剧/新增/音乐/直播/书/图/无搜索/下载），等于把多个子源打包进一条规则。

**「不能导入」的常见根因**：它是 `type: all` + `hiker://empty` 的**框架型规则**，不是普通 `video/image/audio/other` 爬虫规则。海阔视界标准「本地导入/订阅」通常**不接收 `type: all`**——要么直接报"导入失败"，要么导入了但 `all` 无对应分组、列表空白。所以**不能像 EcoHub 那种普通规则一样直接导入**。

**正确用法（二选一）**：
1. **作为聚阅子程序导入（推荐）**：先装 §8.5 的 `聚阅` 宿主（带「云口令导入」入口），在聚阅内用云口令/远程源添加，把云端源 `https://14719.kstore.space/阅动漫.json` 喂进去，阅动漫即以子程序形式加载。
2. **独立导入（取决于 app 版本）**：因本包自带运行时，若你的海阔视界版本支持导入 `type: all` 的 `.hk小程序.zip`，它可独立跑（导入后自己从 `remoteUrl` 拉云端源）。但多数版本不支持，故第 1 种更稳。

> 收到此类包时：先 `grep type: all` + `url: hiker://empty` 判断是否为框架型；再 `grep config.聚阅`——为 0 即"自包含子程序"（用自己 `remoteUrl`），非 0 即"宿主依赖型"。两者都只能真机验证，PC 测试桩不支持。

### 8.7 小程序包（`.hk小程序.zip`）导入无反应的常见原因

真机反馈实录（2026-09，dmhyy 站点）：用户把打包好的规则 zip 丢进海阔视界「导入」，**毫无反应**。根因不是规则内容，而是**包内文件名不对**。

- **硬性要求：包（zip）根目录下的规则文件必须叫 `rule.json`**，海阔导入器按这个名字找规则。若 zip 里是 `xxx_rule.json`、`站点名.json` 等自定义名 → 导入器扫不到 → 静默无反应、不报错。
- **正确包结构**（参考真机可用包 `壹影视.hk小程序.zip`、`云帧享.hk小程序.zip`）：zip 根目录直接放
  ```
  rule.json          # 规则本体（名字必须精确为 rule.json）
  require.json       # 有依赖时才要；无依赖可省
  libs.zip           # 有依赖时才要；无依赖可省
  ```
  不要多套一层同名文件夹（`站点名/rule.json` 在 zip 里也算多了层级，部分版本不认）。
- **打包命令**：`zip -j 站点名.hk小程序.zip rule.json`（`-j` 丢掉路径），或用 Python `zipfile` 指定 `arcname='rule.json'`。
- **单条规则的另一条路**：不进「小程序」入口，走「首页频道 / 添加规则 / 本地导入」，此时文件名不叫 rule.json 也能读（读的是内容）。两条入口混淆是用户「导入没反应」的另一大来源。
- **口令导入**：单条首页频道口令格式 `海阔视界，首页频道￥home_rule￥<紧凑 JSON 一行>`；小程序整包用口令则走 `home_rule_url` / `home_sub`（指向 zip 或 json 的**可访问 URL**，不能是本地路径）。

> 排查顺序：先确认 zip 内是否 `rule.json` → 再确认用户进的是「小程序」还是「首页频道/本地导入」（两处入口要求的文件形态不同）→ 最后才怀疑规则内容。
> 另：真机 Hiker JSEngine（Rhino）**可用 Java 类**，如 `Packages.java.security.MessageDigest`、`Packages.javax.crypto.Cipher`、`Packages.java.lang.StringBuilder`、`Packages.java.net.URI`、`Packages.java.util.TreeMap`（参考包 `壹影视`/`云帧享` 即用 Java 做 SHA/GCM 签名）。纯 JS 能算的（如 SHA-256）优先纯 JS——PC 测试桩可验证；只有 Java 加密（GCM/PBE）才必须用 `Packages.*`，但那样 PC 桩测不了、只能真机验证。
