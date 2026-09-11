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
