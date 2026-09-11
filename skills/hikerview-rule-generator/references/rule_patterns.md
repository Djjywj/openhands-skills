# 海阔视界规则写法 / 架构模式（来自真实逆向样例）

本文件按「规则架构类型」归类真实可用的写法骨架。生成规则时，先判断**目标站点 / 用户给的参照**属于哪种形态，再选用对应骨架。所有骨架均来自用户提供的真实包逆向整理，已验证有效。

> 一个规则最终落到哪种形态，取决于它**是否依赖框架、依赖什么**。生成完规则，务必按文末「依赖识别速查」判断并告知用户本次需要哪种依赖（`scripts/validate_rule.py` 现已自动打印该报告）。

---

## 各写法利弊速览（生成前必读，也用于"让用户选形态"时展示）

"简单"有两个维度：**写的人累不累** + **用的人装不装得动**。综合最常选的是 **A 纯规则（无依赖）**——单文件即导即用、零安装负担、PC 可完整测；但站点解析很复杂时，借现成底座（B/D/F）反而少写代码，代价是用的人必须按原标题装底座。

| 写法（模式） | 一句话 | ✅ 优点 | ❌ 缺点 | 何时选 |
|---|---|---|---|---|
| **A 纯规则（无依赖）** | 单文件自己爬自己解析 | 零依赖即导即用；PC 可完整测解析；改动直观 | 解析/UI 全自己写；加密直链/复杂播放要自己实现；无现成漂亮模板 | **绝大多数个人站点（首选）** |
| **D/F 跨规则程序·模板**（配置助手/模板·Q） | 复用现成解析+UI 底座 | 代码量骤减；解析能力强（能解很多加密直链）；Q 系现成主规则多可直接套 | 用户须按**原标题**装底座（『配置助手』『模板·Q』『XYQ推送』），缺一个就崩；跨规则调用 PC 测不了要真机；底座更新/下架会牵连 | 站点结构复杂、想少写代码、且用户愿意装底座 |
| **C 聚阅子程序（库打包）** | 跑在聚阅框架、libs 进包 | 生态成熟、作者维护；享框架运行时/插件；**主流用云口令导入超方便** | 需先装聚阅宿主；依赖库时要连包（require.json+libs.zip） | 已是聚阅生态、要用插件/现成能力 |
| **B 聚阅框架宿主** | 做成可装子程序的平台 | 功能最全、可聚合一堆子程序；生态活跃 | 要维护四件套+远程源（道长仓库已废弃，源以最新包为准）；比纯规则重 | 想做平台/框架给别人用 |
| **E 自包含聚阅子程序** | 自带运行时脱离宿主 | 可独立跑、不桥接宿主；仍走云口令导入 | 包大（含运行时）；需经聚阅宿主云口令导入 | 想独立分发又享聚阅能力 |
| **F Q模板体系（被依赖底座）** | 做 UI 渲染底座给别人用 | 统一漂亮 UI；被 Q 系广泛复用 | 它自己是底座不是站点；依赖它的主规则都要装它+配置助手 | 做通用模板/底座，非写具体站点 |

> 本 skill 目标是「做能导入即用的规则、借现成模板」：站点解析复杂或已有成熟底座（聚阅子程序 / 模板·Q / 配置助手）时，**优先借底座**（少写代码、UI/解析现成、导入即用）；仅当站点极简单、或无合适底座、或用户明确不要依赖时才用纯规则 A。聚阅生态成熟、作者维护、云口令导入方便，不是负担；Q 模板也常见。SKILL.md 第 3 步已用 `AskUserQuestion` 把上表利弊讲给用户、让其拍板后再动笔。

---

## 模式 A：普通网页爬虫规则（如 EcoHub / 360魔改的列表部分）

**适用**：站点直接返回 HTML 或 JSON API，无框架依赖，纯靠 `rule.json` 自己爬。
**关键特征**：
- `type`: `video` / `image` / `audio` / `other`（标准四选一）
- `url` 含占位符 `fyclass`/`fypage`，**筛选必须加 `fyarea`/`fysort`/`fyyear`**（铁律，缺一不可，否则筛选无效）
- `url` 必须带 `;get;UTF-8;{referer@站点域名}` 修饰符（Feather/嗅探等引擎无此修饰符会请求失败）
- **列表项 `url` 也必须带修饰符**：海阔只把「带修饰符的链接」当规则链接交给规则引擎请求、进而执行 `detail_find_rule`；
  写纯网页地址（无修饰符）会被当普通网页用 WebView 打开，点进去**不出选集**（详见 rule_format.md §5.3）
- `find_rule` / `searchFind` / `detail_find_rule` 用 `js:` 解析
- 三级兜底取响应：`var raw = (typeof getResCode==='function')?getResCode():((typeof result!=='undefined'&&result)?result:(typeof input!=='undefined'?input:''));`

**列表解析骨架（SSR/RSC HTML 站点，如 Next.js）**：
```js
js:
var raw = (typeof getResCode === 'function') ? getResCode() : ((typeof result !== 'undefined' && result) ? result : (typeof input !== 'undefined' ? input : ''));
var d = [];
if (raw) {
    var marker = '\\"list\\":[';          // SSR 页把 JSON 转义成 \"list\":[
    var idx = raw.indexOf(marker);
    if (idx >= 0) {
        var s = idx + marker.length - 1, depth = 0, inStr = false, esc = false, end = -1, j;
        for (j = s; j < raw.length; j++) {
            var c = raw.charAt(j);
            if (esc) { esc = false; continue; }
            if (c === '\\') { esc = true; continue; }
            if (c === '"') { inStr = !inStr; }
            else if (!inStr) { if (c === '[') depth++; else if (c === ']') { depth--; if (depth === 0) { end = j + 1; break; } } }
        }
        if (end > 0) {
            var arrStr = raw.substring(s, end).split('\\\\').join('\\').split('\\"').join('"'); // 反转义
            var list = []; try { list = JSON.parse(arrStr); } catch (e) { list = []; }
            for (var i = 0; i < list.length; i++) {
                var it = list[i];
                d.push({ title: it.name || '', img: (it.picture || '') + '@Referer=https://站点/',
                         desc: (it.cName || '') + ' ' + (it.remarks || '') + ' ' + (it.area || '') + ' ' + (it.year || ''),
                         url: 'https://站点/play?id=' + it.id, col_type: 'movie_3' });
            }
        }
    }
}
setResult(d);
```
> 视频直链（`detail_find_rule`）取出后务必加 `#isVideo=true#`；图片统一加 `@Referer=站点域名` 防盗链。

> **封面比例要跟 col_type 匹配**：很多影视站同时给横版（16:9）和竖版（3:4）封面
> （字段常叫 `coverImgUrl` / `coverImgUrlVertical`，或 `pic`/`verticalPic`）。
> 横版塞进 `movie_3`/`movie_2` 这类**竖格**会被裁掉两边，用户反馈就是
> 「图片太宽、显示不全」。优先选**与格子同向**的那张（竖格用竖图）；
> 详情大图若想让横图完整显示，用 `pic_1_full`（满宽、高按比例自适应），
> 别用固定高度会裁切的 `pic_1`。抓接口时先打印 item 全部字段，别漏掉竖版字段。

**依赖**：无（纯规则，可独立导入）。

---

## 模式 B：聚阅（juyue）框架宿主（如「聚阅」）

**适用**：想做一个"可以装子程序"的框架，提供运行时 + UI + 子程序加载器。
**关键特征**：
- `type: all`，`url: hiker://empty`（伪协议，自己画页面）
- `preRule` 初始化 `config.聚阅`（经 `$.require('ghproxy').getSrcHome()` 取得远程源码源）。⚠️ **道长仓库（cnb.cool 的 JuyueTest）已废弃**，远程源不要硬编码旧地址；生成时一律以用户提供的**最新聚阅包内 `preRule` 实际源**为准，或提示用户从聚阅官方渠道取当前源。
- `find_rule`：`if(config.聚阅){ require(config.聚阅); yiji(); }` —— 加载真实运行时后调 `yiji()` 渲染子程序列表；`searchFind` 调 `sousuo()`
- **四件套**：`rule.json` + `require.json` + `libs.zip`（运行时库 SrcJu 等 19 个）+ `data.zip`（`plugins/` 插件、`template/` 子程序模板、`juItem.json` 子程序注册表）
- `pages` 含 `name:"云口令导入", path:"import"` 与 `name:"导入确认页", path:"importConfirm"` —— 用户粘云口令即可装入子程序

**依赖**：§8.1 库打包（运行时库）+ 远程源码源（cnb.cool）。`config.聚阅` 在 rule.json 内出现 → 判定为宿主。

---

## 模式 C：聚阅子程序（两种写法）

聚阅子程序 = 跑在聚阅宿主上、实现某个站点的源。有**新旧两种写法**：

### C1. 新式：`parse` 对象（官方标准，推荐，云口令导入）

聚阅生态**现在的主流写法**（作者持续维护后演进，2026-08 实测确认）。子程序本质是**一个 `parse` 对象**（宿主的 `template/parseCode.js` 模板），实现 主页/二级/搜索/解析/最新 几个函数，宿主 `yiji()` 自动加载渲染。**无需 rule.json / pages / require.json / libs.zip**，一个 JS 文件即可（模板见 `assets/templates/juyue_parse.js`）。

```js
let parse = {
    作者: "xx", 版本: "1", host: "https://站点/",
    页码: { 主页:false, 分类:true, 排行:true, 更新:true },
    静态分类: { type:"主页", url:"...fyclass...fysort...fypage...", class_name:"", class_url:"", sort_name:"", sort_url:"" },
    频道: { 包含项:["分类","排行","周表"] },
    主页: function(){ let d=[]; ...; return d; },
    二级: function(url){ ...; return { detail1, detail2, desc, img, line, list }; },
    搜索: function(name){ let d=[]; ...; return d; },
    解析: function(url){ ...; return m3u8/直链; },
    最新: function(url){ return ''; }
};
```

**关键契约**（必须写对）：
- `主页()` 返回列表项数组（同海阔 d 数组：title/desc/img/url/col_type）
- `二级(url)` 返回结构化对象：`{detail1(封面上), detail2(封面下), desc(简介), img(海报), line(线路名数组), list(选集)}`；**多线路时 list 是 `[线路1选集数组, 线路2选集数组, ...]`，单线路 list 是一维选集数组**；选集项 `{title, url}`
- `搜索(name)` 返回列表数组；`解析(url)` 把选集 url 变成可播直链；`最新(url)` 返回最新章节名
- 可调海阔内置：`fetch/request(url[,opt])`（**同步返回字符串**，非 Promise）、`pdfa/pdfh/pd`（四大金刚 DOM 解析）、`getMyVar/putMyVar`、`getItem/setItem`、`getCookie/setCookie`、`base64Encode`、`MY_PAGE/MY_URL`、`refreshPage`、`$('').input/lazyRule`
- **运行时支持 ES6**（let/const/=>/模板字符串/map 均可，实测聚阅子程序普遍用 ES6），不必守 ES5

**五大必坑（2026-08 实战踩坑，写规则前必读）**：
1. **`#gameTheme#` 二级标识（最致命）**：`parse.二级标识` 声明后，**所有列表项（主页/分类/搜索）的 url 必须拼 `#gameTheme#` 后缀**。漏了 → 点击不进二级菜单（选集渲染）→ 选集没法播放。这是"主页进二级无法播放、分类能播"这类诡异 bug 的根因（分类加了、主页/搜索漏了）。
2. **验证码反爬**：站点有"系统安全验证/验证码"时，**所有 fetch/request 必须走 `_fetchSafe` 包装**（撞盾页自动弹图片输入框，见 `assets/templates/juyue_parse.js` 的 `_fetchSafe`/`_makeVerify`），不能裸 `request`。盾页正则：`/系统安全验证|mac_verify|访问此数据需要输入验证码|安全检测/`。
3. **cookie 持久化**：验证码通过后 `getCookie(host)` → `setItem('fy_cookie')`，重启后 `setCookie` 恢复，避免每次重启重输。
4. **云口令由用户在聚阅里生成**（不是自己拼）：真实云口令是"云剪贴板"模式，格式 `云口令：聚阅接口￥<aesEncode(pasteurl)>￥<源名>(云N)@import=js:$.require("hiker://page/import?rule=聚阅")`，其中 **aesEncode 加密的是 pasteurl（剪贴板短链 URL，约 40 字符），不是源内容**。海阔 `aesEncode` 是 **AES/CTR（无 padding，密文=明文长度）**，不是 AES/CBC。**不要自己实现云口令**（没有 sharePaste 后端 API），让用户在聚阅里"分享→云剪贴板"生成；自用导入走"新建接口→parseCode 模板→粘贴 parse 代码"即可。
5. **移动 UA**：很多站对移动 UA（iPhone Safari）不触发验证码，`parse.UA` 默认写移动 UA。

**导入（两种）**：
- **自用最可靠**：聚阅宿主「新建接口」→「parseCode」模板 → 粘贴 parse 代码 → 保存（"接口规则文件"是文件路径，点"新建"建 txt 粘代码）。
- **分享用云口令**：让用户在聚阅里"分享→云剪贴板（云 N）"自动生成云口令，粘贴给他人即可。不要自己拼 AES。

### C2. 旧式：rule.json + pages + libs 打包（如「多多影视」「枫叶4K」）

早期聚阅子程序写法，作为**独立"小程序"包**导入（不是云口令）：
- `type: video` 等标准字段，但 `url: hiker://empty##fypage`（自绘页面，不走 class_name/class_url）
- `find_rule` 用 `js:` + 手写渲染（request/pdfa/MY_PAGE/getMyVar + `$.require(x5ui)` 轮播）
- `pages` 定义子页面（解析库 hanshu、二级页 erji 等）
- `require.json` + `libs.zip`：依赖库（`x5ui.js` 轮播 UI + `Ver.js`），文件名 = md5（见下样例）
- ⚠️ 只导入 `rule.json` 会因 `$.require` 找不到库而失败，**必须连包整体导入**

**require.json 样例**：
```json
[{"url":"下载源(gitee)","file":"/storage/emulated/0/.../libs/<md5>.js","proxy":"","accessTime":0}]
```

**依赖**：C1 仅依赖聚阅宿主（无 libs，最简）；C2 依赖聚阅宿主 + 库打包（require.json + libs.zip）。生成时优先 C1。

---

## 模式 D：跨规则「程序 / 模板」依赖（如「360魔改」→「配置助手」、「Q系规则」→「模板·Q」）

**适用**：主规则把"解析"（视频页→可播直链）或"UI 渲染"（列表/详情页模板）等能力委托给另一个 `type: tool` 程序。这是海阔生态最常见的"底座 + 子规则"分工。
**两类典型被依赖程序**：
- **解析引擎型**（如「配置助手」）：导出 `$.exports.mulParse = function(vipUrl,...){...}`，主规则调 `$.require("hiker://page/mulParse?rule=配置助手").mulParse(vipUrl)` 把视频页地址变成可播直链。
- **UI/渲染模板型**（如「模板·Q」，作者发粪涂墙）：导出 `$.exports.autoPage` 并内置 `stui` 主题渲染页面（`stui-vodlist` 列表、`auto`/`autoPage` 自动详情页、`erji` 二级页、`yzm` 验证码、`jxhs` 解析、`Mapping` 映射）；主规则在 `detail_find_rule` 里 `$.require("hiker://page/auto?rule=模板·Q").autoPage(getResCode())` 复用其详情页渲染，在 `searchFind` 里 `$.require('hiker://page/yzm?rule=模板·Q')` 复用验证码处理。

**关键特征（两种通用）**：
- `?rule=` 后面是**被依赖程序的 `title`，按标题精确匹配** → 被依赖程序必须按原标题安装，改名/缺失则失效（如保留标题『模板·Q』『配置助手』）
- 被依赖程序自身是 `type: tool` 基础程序，通常自包含（`config.聚阅=0`，不依赖聚阅宿主），靠 `$.exports` 提供接口供调用

**依赖**：§8.4 跨规则程序（另一个 hiker:// 程序，按标题安装）。生成后必须提醒用户"还需安装名为『XXX』的程序（保留原标题）"。

---

## 模式 E：自包含聚阅子程序（如「阅动漫」）

**适用**：子程序把**自身依赖的聚阅运行时一起打包**，可脱离宿主独立跑。
**关键特征**：
- `type: all`，`url: hiker://empty`
- `require.json` + `libs.zip` 打包**聚阅框架运行时本体**（一个大 `.js`，约 400KB，含 `MY_RULE`/`config`/`getMyVar`/`hiker://` 全套）
- `config.聚阅` 计数为 0（**不桥接宿主**），`preRule` 用 `putMyVar('remoteUrl','https://云端/xxx.json')` 自拉云端内容
- 从云端聚合多类资源（`types`: 漫画/视频/短剧/新增/音乐/直播/书/图/无搜索/下载）

**依赖**：自带运行时，但属 `type: all` 框架型规则，标准"本地导入"通常拒收，需经聚阅宿主云口令导入，或少数 app 版本支持独立导入 `type: all` 包。

---

## 模式 F：Q模板体系（被依赖的 UI/渲染模板框架，如「模板·Q」）

**适用**：做一个供其他"Q系"规则挂载的 UI/渲染底座程序（不是具体站点，是模板）。
**关键特征**（基于 `模板·Q.hk小程序.zip` 逆向）：
- `type: tool`，`group: 工具`，`url: hiker://empty##fypage`，`config.聚阅` 计数为 0（**非聚阅系，独立体系**）
- 仅单 `rule.json`（79KB，无 require.json/libs.zip/data.zip）—— 自身自包含，不打包外部库
- 内部定义页面（`pages` 字符串）：`一级stui-vodlist`（列表）、`auto`（+ `$.exports.autoPage`）自动详情页渲染、`erji`（二级页）、`yzm`（验证码/登录处理）、`jxhs`（解析）、`Mapping`（映射）
- 通过 `?rule=模板·Q` **自引用**这些页面；其他规则按标题『模板·Q』调它
- 它自身又依赖 Q 系更底层的程序「XYQ推送」（`$.require('hiker://page/...?rule=XYQ推送')`）—— 即 Q 系生态层级：`XYQ推送`(底层) ← `模板·Q`(UI模板) ← 各 Q系主规则（外加解析引擎「配置助手」）
- `version` 为**日期编码**（如 `25090800` = 2025-09-08），而非简单递增——真实生态版本号常为 `YYMMDDxx`（我们 skill 第 5 步「逐次+1」仅为无既有约定的简便约定）
- 作者特征：发粪涂墙（与「360魔改」「配置助手」同源，属同一 Q 系作者家族）

**依赖**：作为被依赖的底座，它**自身通常无需其它程序即可运行**；但任何依赖它的"Q系"主规则都必须在设备上按原标题安装『模板·Q』（以及解析引擎『配置助手』）。

> ⚠️ 当 `validate_rule.py` 在一条规则里识别到 `?rule=模板·Q` 时，即判定其依赖 Q模板；而模板·Q 自身的自引用已被 detector 排除，不会误报"本规则依赖模板·Q"。

---

## 引入写法：依赖框架时怎么挂（生成规则必须写对）

做「能导入即用」的规则，光写对解析不够，还要写对"怎么挂到框架/底座上"。两种主流引入方式：

### 1. 聚阅子程序 → `parse` 对象 + 云口令导入（主流，最方便）
- 聚阅生态成熟、作者持续维护，子程序导入非常方便。**子程序本质 = 一个 `parse` 对象**（`let parse = {主页/分类/二级/搜索/解析/最新...}`，模板见 `assets/templates/juyue_parse.js`），不是标准 rule.json。
- 两种导入路径：
  1. **新建接口粘贴（自用最可靠）**：聚阅宿主 → 新建接口 → 「parseCode」模板 → 粘贴 parse 代码 → 保存（"接口规则文件"是文件路径，点"新建"建 txt 粘代码）。
  2. **云口令导入（分享用）**：让用户在聚阅里"分享 → 云剪贴板（云 N）"自动生成云口令，格式 `云口令：聚阅接口￥<aesEncode(pasteurl)>￥<源名>(云N)@import=js:$.require("hiker://page/import?rule=聚阅")`。**aesEncode 加密的是 pasteurl（剪贴板短链，约 40 字符），不是源内容**；海阔 aesEncode 是 **AES/CTR（无 padding）**。**不要自己拼云口令**（无 sharePaste 后端 API），交给用户在聚阅里生成。
- **所以生成聚阅子程序时，交付物优先是一段 parse 代码**（新式 C1），不一定要打成 zip；只有旧式 C2（rule.json+pages+libs）才连包。
- ⚠️ 道长仓库（cnb.cool JuyueTest）已废弃，远程源不要硬编码旧地址，以最新聚阅包内 `preRule` 实际源为准。

### 2. Q模板 / 配置助手 → `$.require` 跨规则调用（按标题）
- 主规则（站点爬虫）在 `detail_find_rule` / `searchFind` 里用 `$.require("hiker://page/<页面>?rule=<标题>")` 调被依赖程序导出的接口：
  - UI 渲染：`$.require("hiker://page/auto?rule=模板·Q").autoPage(getResCode())`
  - 解析：`$.require("hiker://page/mulParse?rule=配置助手").mulParse(vipUrl)`
  - 验证码：`$.require("hiker://page/yzm?rule=模板·Q")`
- `?rule=` 后是被依赖程序的 `title`，**按标题精确匹配** → 被依赖程序必须以原标题安装（『模板·Q』『配置助手』『XYQ推送』），改名/缺失即失效。
- 这类主规则本身是普通 `type: video` 等，**导入方式同模式 A**（粘贴/导入 `rule.json` 即可），只是**用之前要先按原标题装好底座**。

> 总结：借底座做规则 = "写好解析 + 写对引入写法 + 告知用户装底座"。聚阅走云口令、Q 系走 `$.require`，两条路都成熟好用，不是负担。

### 分类点了都显示「全部」怎么排查

> **头号坑（真机已验证）：分类所在 URL 若用 `post`，「分类传参」会被海阔吃掉。**
> 海阔请求 POST 规则时会在第一个**半角** `?` 处切开，把 query 当 POST body（源码
> `HttpParser.post()` 的 `onSuccess(finalUrl)`，而 `finalUrl = ss[0]` = 去掉 query 的 url）。
> 于是 JS 里 `MY_URL` 只剩 `https://host/path`，`getParam('t')` 读到空串，`typeIds:[]` → 永远「全部」。
> 现象就叫「标签都在，点了内容不变」。两种解法（任选其一）：
> 1. 该 URL 改用 **GET**（`;get;UTF-8;{...}`），query 会保留进 `MY_URL`；
> 2. 仍用 POST，但把问号/与号写成**全角** `？？`、`＆＆`：海阔先按半角 `?` 切分（全角不命中），
>    再在 `post()` 里 `decodeConflictStr` 还原成半角，`MY_URL` 因此带 query。
>
> 详情页/搜索同理。`scripts/test_rule.js` 现已**忠实模拟**这个顺序（POST + 半角 `?` 会复现丢 query；
> POST + `？？` 或 GET 则保留），本地就能提前抓到，不必等真机。

站点侧先确认，再怀疑规则：

1. **分类 id 对不对**：找站点自己的分类接口（如 `/videos/getType`）拿到 `id` + `name`，别凭猜。
   首页接口若返回 `typeIds`/`classId` 之类数组参数，用真实 id 直接打一次，比对不同分类返回的**内容（不是条数）**是否不同。
2. **小心「假重合」**：如果某分类（尤其是第一个/最大的那个）返回的内容和最热「全部」前几十条一模一样，
   很可能只是**站点最新内容恰好都属于该分类**，接口并没有忽略筛选——换个靠后的页或换个分类 id 就能区分，别误判成 bug。
3. **回调值可能是名字不是 id**：`class_url` 存在时海阔通常回传 id；但某些情况会回传 `class_name`。
   规则里一律 `parseInt(getParam('fyclass'))` 就会在名字上得到 `NaN`，**所有分类都退化成「全部」**。
   稳妥写法（数字/名字双兼容，并多取几处兜底）：

   ```js
   var CLASS_NAMES=['全部','国产','主播'];         // 与 class_name 保持一致
   var CLASS_IDS=[0,4,11];                          // 与 class_url 保持一致
   function resolveType(v){
     v=String(v==null?'':v); try{ v=decodeURIComponent(v); }catch(e){}
     v=v.replace(/^\s+|\s+$/g,'');
     if(!v||v===CLASS_NAMES[0]) return CLASS_IDS[0];
     if(/^[0-9]+$/.test(v)) return parseInt(v,10);
     for(var i=0;i<CLASS_NAMES.length;i++){ if(CLASS_NAMES[i]===v) return CLASS_IDS[i]; }
     return CLASS_IDS[0];
   }
   function pickClass(){                            // 依次尝试多个来源，取第一个可信值
     var cands=[];
     try{ cands.push(getParam('t','')); }catch(e){}
     try{ var m=String(MY_URL||'').match(/[?&]t=([^&;]+)/); if(m) cands.push(m[1]); }catch(e2){}
     try{ if(MY_PARAMS){ cands.push(MY_PARAMS.t||''); cands.push(MY_PARAMS.fyclass||''); } }catch(e3){}
     for(var i=0;i<cands.length;i++){
       var v=String(cands[i]==null?'':cands[i]);
       try{ v=decodeURIComponent(v); }catch(e4){}
       v=v.replace(/^\s+|\s+$/g,'');
       if(!v) continue;
       if(v==='fyclass'||v==='fypage') continue;    // 还是占位符 → 未被替换，换下一个来源
       return v;
     }
     return '';
   }
   var c = resolveType(pickClass());
   ```

   > 若某来源取到的仍是占位符本身（`fyclass`），说明它没拿到真实值，要**跳过换下一个来源**，
   > 否则会把「全部」误当唯一分类（点哪个都一样）。

4. **用本地桩验证**：`scripts/test_rule.js --fyclass 国产` 与 `--fyclass 4` 各跑一次，
   两次结果应完全一致；若名字那次和「全部」一样，就说明命中本坑。

---

运行 `scripts/validate_rule.py <rule.json>`，脚本会自动打印依赖报告。判据如下：

| 信号 | 判定 | 必须告知用户的配套要求 |
|------|------|----------------------|
| 同目录存在 `require.json` + `libs.zip` | **库打包依赖（§8.1 / 模式 C/E）** | 必须**连包整体导入**，不能只丢 `rule.json`；libs.zip 内库会自动装到设备 |
| `$.require("hiker://page/...?rule=XXX")` 或 `$.exports` | **跨规则程序依赖（§8.4 / 模式 D/F）** | 还需按原标题安装名为「XXX」的程序（如『配置助手』解析引擎、『模板·Q』UI渲染模板），否则解析/渲染功能失效 |
| `type: all` + `url: hiker://empty` | **框架型（§8.5 宿主 / 模式 E 自包含）** | 聚阅子程序主流用**云口令导入**（粘码→宿主确认即装，最方便）；部分 app 也支持直接导入 `type:all` 包；非宿主型需先装聚阅框架宿主 |
| 纯 `type: video/image/audio/other` 且无上述信号 | **无依赖（模式 A）** | 可直接导入，无需配套 |

> 若同时命中多条，逐条列出（例如"本规则=普通爬虫 + 跨规则依赖配置助手"），让用户一次装齐。

> **区分"依赖方"与"提供方"**：模板·Q、配置助手这类 `type: tool` + `$.exports` 的程序是**被依赖的底座（提供方）**，它们自身一般自包含、无需其它程序；真正需要告知用户"请安装 XXX"的是**依赖它们的主规则**。validate_rule.py 已对自引用（`?rule=` 后名字 = 本规则 title）做排除，不会对底座程序误报依赖。

## 模式 G：短视频流「筛选 + 凑数」写法（抖音/快手类 feed 接口）

适用：接口每次只回十几条、内容混杂（带货/短剧/AI 生成/低质），用户要「只看长视频/高赞」。

- **多档门槛用分类传参**：在 `url` 里加一个接口会忽略的参数名占位，如 `&min_sec=fyclass`，`class_url` 写 `300&600&1800`；
  JS 里 `try{ v=parseInt(getParam('min_sec'),10) }catch(e){}` 取值，取不到就退回默认值（**必须有兜底**，否则占位符没被替换时会拿到 `NaN`）。
- **翻页凑数 + 提前停止**：`for(p=2;p<=MAX_PAGES;p++){ if(cands.length>=TARGET) break; ... }`，避免为凑满一屏发太多请求（移动端每页 1 秒级）。
- **三道过滤**：时长硬门槛（`video.duration/1000`）、点赞门槛（`statistics.digg_count`）、关键词黑名单（`desc+nick` 统一转小写再 `indexOf`，中英混排关键词要写成小写形式）。
- **AI 生成内容有官方声明字段，优先用它**（2026-09 实测抖音 aweme）：`risk_infos.content` 里会出现「作者声明：内容由 AI 生成」「作品含AI生成内容」，另有 `aigc_info.aigc_sticker_id` / `aigc_type===-1`。feed 里约 **14%** 条目带该声明；用 222 条样本验证：0 漏判、0 误杀（关键词黑名单同期只能命中其中一小部分）。JS 里 `String((a.risk_infos||{}).content||'').toLowerCase()` 做 `indexOf('ai生成')`（记得同时匹配带空格的 `'ai 生成'`）。**不要把 `media_type` 当 AI 标识**——实测恒为 4，无区分度；带货 `anchors` 在 feed 里几乎恒空，`video_tag` 只有分类。
- **无分类（单列表）规则**：`class_name` 与 `class_url` 同时留空字符串即可，首页直接请求 `url`（顶部不显示分类栏）。validate_rule.py 已放行这种写法（只告警）。
- **单列表 + 提速**：`url` 里 `refresh_index=fypage` 只取第 1 页，其余页（2..MAX_PAGES）在 JS 里用 `batchFetch` 一次并发取回（`typeof batchFetch==='function'` 判断 + 逐个 `fetch` 兜底），实测 12 页 ≈1.0 秒、整体刷新 1.5~2 秒。
- **筛完为空要给人话**：`setResult([{title:'这次没筛到…，下拉刷新换一批',col_type:'text_3'}])`，别返回空列表让人以为规则坏了。

## 模式 H：短视频 App 的「真·搜索」（抖音类，2026-09 实测）

**结论先行：抖音搜索接口必须登录，匿名拿不到数据，别在这上面耗时间。**

- 实测 8 个端点（web `/aweme/v1/web/general/search/single/`、app `/aweme/v1/general/search/single/`、`/aweme/v1/search/item/`、话题 `/aweme/v1/challenge/aweme/` 等）：无 Cookie 时统一 `status_code=2483`，`data` 为 `null`，文案「请先登录，再继续搜索吧」。
  - 自己注册匿名 `ttwid`（`https://ttwid.bytedance.com/ttwid/union/register/`）拿到 cookie **也不行**，照样 2483。
  - 第三方镜像接口（pearktrue / 52vmy / tenapi 之类）当年可用，现已 SSL 过期 / 522 / 502，不要写进规则。
- 匿名**能**用的：`/aweme/v1/search/sug/`（下拉建议词，用来给"建议搜索"按钮）、`/aweme/v1/web/hot/search/list/`（热搜词）。
- 登录后的链路：规则里 `web://https://www.douyin.com/` 让用户在网页登录一次 → `getCookie('douyin.com')` 取 `sessionid`（`sessionid_ss`/`sid_tt` 也行）→ 拼 `Cookie@...` 请求头 → 搜索接口即可返回数据。cookie 取值要写成容错函数（`getCookie` 可能返回空串、`JSON.stringify` 形态、或抛错）。

**通用深搜解析器（一份代码吃三种结构）**：feed 是 `aweme_list`，搜索是 `data[].aweme_info`，话题是 `aweme_list`（带 `aweme_info`）。与其为每个接口写一套路径，不如写个栈遍历（子节点上限 ~16，深度设上限）找"带 `aweme_id` + `video` 的对象"：

```js
function _scanRaw(txt,minSec,minDigg,out){
  if(!txt) return; var j=null;
  try{ j=JSON.parse(String(txt).replace(/^\s+|\s+$/g,'')) }catch(e){ return }
  if(j && !j.aweme_list && !j.data && !j.aweme_info) return;      // 风控/错误结构直接丢
  var st=[j],n=0;
  while(st.length && n<4000){ var o=st.pop(); n++;
    if(!o || typeof o!=='object') continue;
    if(o.aweme_id && o.video){ _take(o,minSec,minDigg,out); continue }
    var keys=Object.keys(o), lim=0;
    for(var i=0;i<keys.length && lim<16;i++){ var v=o[keys[i]]; if(v && typeof v==='object'){ st.push(v); lim++ } }
  }
}
```

实测：feed 12/12 条、搜索桩数据 2/2 条有效条目全部命中，且不会把 `user_info`（`type:511`）之类的节点误当视频。

**登录入口必须放在用户一眼能看到、且登录后会自动消失的地方**（实测踩坑：只把「去登录」放在「没搜到」分支里，用户搜到结果就永远看不到它，直接来问「没看到去登录啊」）：

- 列表页（find_rule）**顶部**插一张卡片（`res.unshift(...)`），条件是「没读到 `sessionid`」；登录后 `getCookie` 有值 → 卡片自动消失，不会长期碍眼。这是唯一保证能被发现的写法。
- 搜索结果页：**「有结果」和「没结果」两个分支都要放**登录/重搜入口（模块化函数 `_loginItem()` / `_againItem()` 复用），别只放没结果那支。
- 判断登录要容错：`getCookie('https://www.douyin.com')` 之外再试 `fetchCookie(...)` 与网关域名；返回值可能是空串、`JSON.stringify` 数组（`[{name,value}]`）或抛错，统一包一层 `_ckStr()`。

**搜不到就降级，并且把"怎么解锁"直接做成列表项**（用户不会去翻帮助）：池内关键词匹配（召回率很低，7 个词 0 命中）+ 这三条入口：

| 入口 | 链接 | 说明 |
|------|------|------|
| 网页搜索 | `web://https://www.douyin.com/search/<kw>`（kw 需 encodeURIComponent） | 最稳，直接跳官方网页结果 |
| 登录解锁 | `web://https://www.douyin.com/` | 网页登录一次，cookie 就位 |
| 重新搜索 | `hiker://search?s=<kw>&rule=<规则标题>` | `rule=` 要用**原文**标题，别 encodeURIComponent |

**本地测试这类规则的技巧**：`scripts/test_rule.js` 的 `getCookie` 是返回 `''` 的桩，所以登录分支在本地永远走不到。想验证登录后的解析逻辑，就复制一份规则、把 `_ckStr` 里 `return out` 前强制写入假 cookie（如 `out='sessionid=fake'`），再用 `--html <桩 json>` 喂一个手造的搜索响应（`data[].aweme_info`），看解析/过滤是否正确。另外该脚本未实现 `fypage@-1@*20@`，`--url` 测试时把 offset 换成具体数字（如 `offset=0`）；该语法海阔本体是支持的（见 `url_tags.md`）。

## 登录态判定：结果导向 + 手动粘贴凭证（2026-09-11 抖音精选实测）

上面只按「cookie 里有没有 `sessionid`」判断登录，比赛站点会踩三个坑，导致「用户明明登录了，规则还说没登录」：

1. **webview 登录的 cookie 未必进 `getCookie`**：海阔可能用外部浏览器打开 `web://`，或 cookie 只存在 App 的 cookie manager，`getCookie(域名)` 读不到；`fetchCookie` 也未必有。
2. **cookie 有 `sessionid` 但已失效**：字段还在，接口却回 `status_code=2483 请先登录`。
3. **跨域不共享**：`www.douyin.com` 与 `api-play-zjg.amemv.com` 是两个域，读前者拿去请求后者经常不对。

v10 的改法：**用「搜索接口的实测返回」当唯一判据**，cookie 只作为传输手段。

```js
function _probe(ck){                     // 打一次真实搜索接口，只看 status_code
  var u='https://<api>/search/?keyword=%E7%83%AD%E9%97%A8&count=3&offset=0&ts=1700000000';
  var h=APP_UA; if(_has_sessionid(ck)) h=h+'\nCookie@'+ck;
  var r=''; try{ r=fetch(u,{headers:h}); }catch(e){ return {login:0}; }
  var c=-1; try{ c=JSON.parse(r).status_code; }catch(e){}
  if(c===0) return {login:0};            // 0 = 接口能用（有登录态）
  if(c===2483) return {login:1};         // 2483 = 明确说没登录
  return {login:-1};                     // 其它码（风控/限流）→ 不要下结论
}
```

- **判定要缓存**：探针每次多一次网络请求。成功缓存 10 分钟，失败缓存 5 分钟，避免下拉刷新反复打接口。
- **失败必须给可执行的下一步**，别只说「请登录」。按「能拿到什么凭证」给三条路：① 站内 `web://` 登录页 ② `input://` 粘贴 Cookie（最管用，配合抓包）③ 图文教程卡。
- **自检卡**（让用户截图发你即可定位）：输出 `判定 / 依据 / cookie 长度 / 含 sessionid / 键名 / 各来源凭证 / 接口 status_code+msg / getCookie 可用性`。`out.login===1` 且 cookie 含 `sessionid` 时文案要写「凭证已失效（过期）」，别写「没登录」——两者解决办法不同。
- **本地桩怎么测登录分支**：桩的 `getCookie` 恒为空，但 `--url` 的 query 会进 `getParam`，把 cookie 当参数传即可：`--url '...&ck=sessionid%3Dfake'` 配 `--html <桩 json>`；要测「没登录」就喂 `{"status_code":2483,...}`。


---

## 模式 I：模块化单例引擎（复杂站点推荐架构）

> 来源：开源技能库 wsh-feiyu/hikerskill（其称已用于 2070 个真实源）。**本库未在真机复现**，但架构本身与官方 `$.exports` / `$.require` 机制一致，逻辑自洽，复杂源可采纳。
> 适用：站点要**同时**支持 首页 / 分类 / 筛选 / 搜索 / 详情 / 播放，且这些页面**共用同一套解析逻辑**时。站点极简单就别上，单文件直写更省事。

### 1. 核心思路

**只有一个模块（`pages` 里只有一项），所有入口都转发到它**，避免"首页一套解析、搜索又抄一遍"造成的状态不一致：

```
顶层（每个规则入口）
  find_rule        : $.require('pages[0]', mod => mod.home())
  searchFind       : $.require('pages[0]', mod => mod.search())
  detail_find_rule : $.require('pages[0]', mod => mod.detail())

pages[0]（唯一模块）
  ├─ 自包含单例      var _inst = null; function ENGINE(){ if(!_inst) _inst = {...}; return _inst; }
  ├─ 原语层  getHTML / cleanText / absolutizeUrl / hashId / uniqBy
  ├─ 解析层  parseItems / parseDetail / parseEpisodes
  ├─ API 层  home / category / search / detail / play
  └─ $.exports = { home:…, category:…, search:…, detail:…, play:… }
```

**顶层只放一行转发**，别把逻辑写死在顶层字段里。

### 2. 为什么要"单例"

`$.require` 每次调用都会**重新求值模块代码**（模块是"代码"不是"已构造对象"），所以模块内部用单例持有跨调用的缓存：

```js
var _INST = null;
function ENGINE() {
    if (_INST) { return _INST; }
    var state = { detailCache: {}, lastError: '' };
    function getHTML(url) { /* ... */ }
    function parseItems(html) { /* ... */ }
    function home() { /* ... */ }
    function detail() { /* ... */ }
    function play() { /* ... */ }
    _INST = { state: state, home: home, search: search, detail: detail, play: play };
    return _INST;
}
ENGINE();                       // 模块加载时就构造好
$.exports = { home: ENGINE().home, detail: ENGINE().detail, play: ENGINE().play };
```

> ⚠️ **别指望单例做跨请求持久化**。`$.require` 的模块实例寿命不确定，重启 App 一定丢。
> 需要真正持久化的（token、账号 cookie）→ 用 `setItem`/`getItem`；会话内临时态 → `putVar`/`getVar`（见 `pitfalls.md` §六.20）。

### 3. 关键约定

- **每条卡片 url 上挂 `@rule`**（`@rule=js:$.require('pages[0]').detail()` / `.play()`），与顶层配置解耦，防止 fallback 成普通网页（见 `pitfalls.md` §一.1）。
- **回调里不许引用闭包变量**：`$.require` / `$.lazyRule` / `$.toString` / `registerTask` 的参数都是**序列化传递**，要用的东西一律**当实参传进去**（【官方】`help_js.md` 明文，见 `pitfalls.md` §三.8）。
- **搜索参数用 `MY_KEYWORD`，详情参数从 `MY_URL` 解析**，别信 `getParam`（见 `pitfalls.md` §二.6）。
- **自绘搜索框用 `@rule` 接本源 `search()`**，禁用 `hiker://search?s=`（§一.2）。
- ⚠️ 模块化写法的回调里**默认按 ES5 写**（`function` 而非 `=>`），与本库默认约定一致。

### 4. 什么时候**不要**用

- 站点简单（一个列表一个详情）：直接写纯规则 A，上这套架构属于过度设计。
- `type` 是 `image` / `misc` 且逻辑很轻的：同上。
- 要交付"单文件即导即用"给不折腾的用户，且顶层字段本来就能写清楚：**保持简单**。

---

## 模式 J：从「影视 App 安装包」反查后端（免抓包快速出源）

用户丢来一个 `.apk` 时**先别急着抓包**——影视类 App 十有八九后端是一台公开的 **苹果CMS(MacCMS)**，接口地址往往能从安装包里直接读出来。

**步骤**（灵虎视频 2.0.3 实战，约 10 分钟出源）：

1. 解包：`unzip -o app.apk -d apk_out`
2. **判断是否加壳**：若 `assets/SignatureKiller/origin.apk` 之类里**没有 `classes.dex`**，说明真身被壳压着。
   ⚠️ **别去啃 inner 包**——真代码在**外层** `classes*.dex`（常有多个，8~10MB 那种）。
3. 在外层 dex 上**直接正则扫字符串**：
   ```bash
   for d in apk_out/classes*.dex; do strings -n 8 "$d"; done \
     | grep -Ei 'https?://[a-z0-9.\-]+' | sort -u
   ```
   重点找**远程配置短链**（形如 `https://bind.aaa.xyz/89.txt,https://bind.bbb.xyz/r2.txt`）和 `api.php` / `provide/vod` 字样。
4. 拉那条短链 → 里面通常就是**主接口域名 + 备用域名**（如 `https://app7.555618.xyz`）。
5. 直接打标准接口验证，**免签名 / 免登录 / 无 UA·Referer 要求**：
   - 列表 `…/api.php/provide/vod/?ac=detail&t=<tid>&pg=<pg>`
   - 搜索 `…/api.php/provide/vod/?ac=detail&wd=<关键词>`
   - 详情 `…/api.php/provide/vod/?ac=detail&ids=<id>`
   - ⚠️ **必须 `ac=detail`**：`ac=list` 的返回里**没有 `vod_pic`**，海报会空。
6. 写规则：纯规则（模式 A）即可，要点如下。

**苹果CMS 出源要点**（配合 `references/pitfalls.md` §12 看）：

| 点 | 做法 |
|---|---|
| 分类 | `t=<tid>`：1电影 2连续剧 3综艺 4动漫 5短剧 6纪录片 7少儿（以实际返回为准） |
| 列表项 url | **必须带规则修饰符**：`…?ac=detail&ids=<id>;get;UTF-8;{referer@<host>}`，否则海阔拿 WebView 打开原网页 |
| 选集解析 | `vod_play_from` / `vod_play_url` 用 `$$$` 分线路、`#` 分集、`$` 分「集名 / 地址」 |
| 线路过滤 | **只留含 `.m3u8` 的线路**；`NBY`（加密解析）、`qq`（腾讯外链）等直连取不到的直接跳过 |
| 播放项 | `url + '#isVideo=true#'`；海报 referer 用**图片自身域名** `@Referer=https://<图床域名>/` 最稳 |

> 💡 同类推断：`bind.*` 域名 + `*.txt` 的**多域名逗号串**是这类 App 的典型"远程配置"，搜到它＝拿到接口清单；dex 里搜不到再回退抓包。
> ⚠️ 该接口若提示"系统安全验证"，多为**搜索**接口每次必现的图片验证码，规则内无法绕过——如实提示即可（见 `pitfalls.md` §12 末）。

