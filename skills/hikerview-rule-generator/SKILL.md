---
name: hikerview-rule-generator
description: 自动生成、校验、迭代海阔视界（Hiker View）观看规则 rule.json / 小程序规则 / 聚阅子程序。当用户说"帮我生成一个海阔视界规则"、"写海阔视界源/规则"、"做个海阔小程序"、"写聚阅子程序/接口"、"这个 rule.json 报错/爬不到/放不了"、或需要为某个影视/图片/音频/杂类网站生成海阔视界订阅源时使用。覆盖四类：图片、视频、音频、杂类，并支持生成后在电脑上先测试、按结果迭代修改。
---

# 海阔视界规则生成器

为指定网站自动生成可用的海阔视界 `rule.json`，并按用户测试结果迭代修正。

## 资料索引（先看这里，别重复造轮子）

| 文件 | 内容 |
|------|------|
| `references/rule_format.md` | 完整字段规范、`find_rule` 写法、详情页取址套路、依赖打包 |
| `references/rule_recipes.md` | **写法骨架速查**（从 2070 条真实规则实测）：四套主流骨架怎么选、返回 API 怎么挑、字段名/API 使用率、`pd` vs `pdfh` 补全差异 |
| `references/rule_patterns.md` | 真实架构写法（纯规则/聚阅宿主/子程序/跨规则程序/Q模板/自包含/模块化单例引擎/**从影视 APK 反查后端**）、短视频流与登录态判定、依赖识别 |
| `references/pitfalls.md` | **真机实战坑位速查**（症状→根因→修法，按链接接管/参数传递/JS作用域/解析/详情播放/持久化/调试/交付安装分类；附「外部经验不要照抄」清单与封面统一 16:9 手法） |
| `references/detail_layout.md` | **详情页布局硬性规范** + 可直接复制的 ES5 实现（海报卡 / 可折叠简介 / 线路切换 / 剧集动态列数 / 空态） |
| `references/checklist.md` | **交付前自检清单**（通用 / PC 验证 / 首页搜索 / 详情 / 播放 / 特殊站点 / 交付 / 真机六关） |
| `references/col_type.md` | 全部 `col_type` 布局样式（以 **App 源码** 为准，48+2 个） |
| `references/community_repos.md` | **GitHub 社区仓库索引**（规则合集/源码/工具去哪找）+ 从 2070 条真实规则量出的字段使用率、`type` 分布、检索技巧 |
| `references/url_tags.md` | 占位符、请求修饰符、`#标签#`、多线路/字幕/弹幕、进度记忆 |
| `references/js_api.md` | JS 内置 API 速查（请求/DOM/编解码/变量/页面/媒体/模块） |
| `references/link_protocols.md` | `hiker://` 等伪协议、子页面、二级列表、导入口令格式 |
| `references/selector_syntax.md` | 原生 DOM 选择器语法（`&&`/`--`/`,n`/`‖`/`.js:`） |
| `references/crypto_sign.md` | 加密/签名接口实战（AES-CBC 请求加密、`getCryptoJS` 用法、AES-ECB 加密图片、加密封面落地文件加速列表、PC 桩验证方法） |
| `references/m3u8_playback.md` | M3U8/HLS 播放、索引缓存（`cacheM3u8`）、本地代理、DNS 优选与“加载慢”排查套路；**第 7 章：直播流专章**——播放地址需重签（否则几秒就断）、海阔「断流即自动播下一条」陷阱、签名算法移植套路与两把验证尺子；**第 8 章：直播平台免登录取流 + 自绘首页（收藏/分类/开播置顶轮播大图）实战模板** |
| `references/official_docs.md` | 官方文档在线地址与本地快照说明 |
| `references/publish_to_git.md` | 把技能库/规则推送到 Git 远端（PAT 生成、建仓、推送、免密、坑） |
| `assets/templates/` | 四类 `rule.json` 模板 + 聚阅 `parse` 对象模板 |
| `scripts/validate_rule.py` | 字段/依赖校验 + col_type 合法性（含 JS 内 `col_type` 字面量）+ 常见反模式检测 + ES5 兼容性提示 |
| `scripts/test_rule.js` | 电脑上跑 `find_rule`/`searchFind`/`detail_find_rule`（内置 DOM 引擎） |
| `scripts/test_juyue.js` | 电脑上跑聚阅子程序 `parse` 对象 |

> ✅ **交付前必过 `references/checklist.md`**（自检清单）；排障必查 `references/pitfalls.md`（症状→根因→修法）。

> 📚 **官方文档**：<https://docs.189.tyrantg.com/docs/hikerview/help_rules.html>（源仓库 <https://github.com/ReflectionLab/Documents>）。
> 遇到本 skill 未覆盖的字段 / API 时优先查它，**不要臆测**。本 skill 的 `references/` 已是该文档的结构化蒸馏，但文档更新晚于快照时以官方为准。

> 🎯 **本 skill 目标：产出「导入即用」的规则**。能借成熟底座（聚阅子程序 / 模板·Q / 配置助手）就借——少造轮子、UI/解析现成、用户导入即用；仅当站点极简单或无合适底座时才纯手写。依赖框架时务必写对**结构和引入写法**（云口令 / `$.require`，见 `references/rule_patterns.md`「引入写法」一节）。

## 执行流程

### 第 1 步：确认规则类型与网址

> 💡 **给新用户的背景**：海阔视界「规则」本质就是一个 JSON 文件（`rule.json`），它告诉 app 如何去某网站抓取「分类列表 / 搜索结果 / 详情页」，以及怎么播放或展示。本 skill 就是帮你把这个 JSON 写出来，并尽量在电脑上先验证解析对不对。

先用 `AskUserQuestion` 询问规则种类（必问），同时索取目标网站网址：

- 选项：图片 / 视频 / 音频 / 杂类（四选一，可多选关闭）
- 若用户消息里已带网址，直接采用；未带则在本步一并询问。

类型与默认值对应关系（写进 rule.json 的 `type` / `group`，详见 `references/rule_format.md` §2）：

| 种类 | type | group | 模板 |
|------|------|-------|------|
| 图片 | picture | ①图片 | assets/templates/image_rule.json |
| 视频 | video | ②视频 | assets/templates/video_rule.json |
| 音频 | music | ④音频 | assets/templates/audio_rule.json |
| 杂类 | other | ⑤杂类 | assets/templates/misc_rule.json |

> ⚠️ **`type` 取值以真实生态为准**：App 源码不校验 `rule.type`，但 2070 条真实规则里**音频一律 `music`、图片一律 `picture`**（`audio`/`image` 各 0 条）。本表已按生态惯例更新；生态另有 `cartoon`（漫画）/`read`（阅读）/`live`（直播）/`news`（资讯）/`tool`（工具）/`all`（框架）。

> 📌 **生成后可在电脑上先验证（不必立刻上真机）**：本 skill 自带 `scripts/test_rule.js`（需 Node.js）。它能模拟海阔 JSEngine 跑 `find_rule` / `searchFind` / `detail_find_rule` 的 JS 解析逻辑，并模拟 `fyclass` / `fyarea` / `fysort` / `fyyear` / `fypage` 占位符替换拼出真实 URL，验证"爬得对不对"。
> - **能测**：列表/搜索/详情的提取条数、标题、海报、链接、简介；筛选/排序参数是否真的改变列表；占位符 URL 拼法；纯 JS 的密码学（`eval(getCryptoJS())` + AES）也能在 PC 端跑通。
> - **不能测**：UI 渲染长相（`movie_1` 纯海报 vs `movie_3` 海报+信息）、app 内置 `fetch` 修饰符是否生效、播放嗅探、`@lazyRule` / `x5Rule`。这些仍需海阔视界 app 真机确认（详见文末"PC 端测试方法"）。
> - **环境**：Node.js v16+（推荐 v18+），无需第三方包；`references/rule_format.md` 已记录筛选占位符必坑等要点。

### 第 2 步：确认是否有现成参照规则（可选但强烈推荐）

在动手分析站点之前，先问用户**手里有没有同类型 / 同站点的现成规则可当参照**（哪怕是从别处扒来的、或自己以前写的残缺版都行）。有参照能大幅减少逆向站点结构的工作量，也能直接复用字段命名与解析思路。

用 `AskUserQuestion` 询问（二选一即可）：
- 选项 A：**有，我发给你**（用户手头有现成规则包 / `rule.json`）
- 选项 B：**没有，从零开始**

> 🤖 **用户选 B 时，agent 应当自己去社区找参照**（不要空手就开写）：GitHub 上有大量现成的海阔规则合集，
> 找**同类型**（视频/图片/音频/杂类）或**同架构**（纯规则/聚阅/Q模板）的源读一遍，能省掉大量逆向工作。
> **索引与用法见 `references/community_repos.md`**（含各仓库定位、真实语料统计、GitHub 检索命令）。
> 分工建议：**官方 App 源码**（`qiusunshine/hikerView`）用来**验证行为**（字段存不存在、解析器怎么切分、有哪些 col_type）；
> **社区规则仓库**用来**找现成写法参照**（怎么组织 `find_rule`、分类栏、详情布局）。
> ⚠️ 社区内容是第三方，**不可直接当事实**：能在官方文档 / App 源码找到出处的才照搬，否则标为"待验证"并写进 `pitfalls.md` §八。

若用户选 A，告知其从海阔视界里**提取现有规则（小程序包）**的方法：

> 📤 **海阔视界提取现有规则步骤**：
> 1. 在海阔视界里**长按**小程序的名称；
> 2. 弹出的菜单选 **「更多分享」**；
> 3. 再选 **「小程序包」**，即可导出规则包；
> 4. 把这个包（通常是 `.zip` / `.hk小程序` 之类）**发给我**，我来拆包读取 `rule.json` 当作参照。

收到包后：解包取出 `rule.json`，通读其 `find_rule` / `searchFind` / `detail_find_rule` / `url` 修饰符 / 分类与筛选写法，作为下一步生成新规则的骨架或对照。若包结构与本 skill 模板差异大，以用户实际包为准；并**主动询问用户：这条规则是否依赖某个「程序 / 模板」（例如海阔里的「Q模板」之类的基础规则）**——若有依赖，请用户把所依赖的程序 / 模板也一并发来，连同本包一起参照，否则单独的规则可能无法独立运行。

> 📚 **官方开发手册（从零开始或查语法时必看）**：海阔视界规则字段与 JS API 的完整说明见官方文档
> `https://docs.189.tyrantg.com/docs/hikerview/help_rules.html`。当用户**没有现成参照规则**、或遇到本 skill 未覆盖的字段 / API（如 `parseDom`、`fetch`、`.lazyRule()` 等）时，优先查阅该手册，不要臆测。

### 第 3 步：选定规则架构形态（必问，先选再写）

> 🧭 **为什么先选**：不同写法对"你写起来难不难"和"用的人装起来麻不麻烦"影响巨大。一旦选错形态（本该纯规则却写了跨规则调用、或本该借底座却自己造轮子），后面要么全错、要么白写。所以**动笔前先用 `AskUserQuestion` 把利弊讲清楚、让用户拍板**。

用 `AskUserQuestion`（header 写"写法"，四选一）呈现，每个选项的 description **直接写清利弊**（要点见下，可精简）：

- **A. 纯规则（无依赖）**（Recommended）—— ✅ 单文件 `rule.json`，即导即用、零安装负担；PC 能完整验证解析；改起来直观。❌ 解析/UI 全自己写；加密直链、复杂播放解析要自己实现；无现成漂亮模板。
- **B. 借成熟底座（跨规则程序/模板，如「配置助手」「模板·Q」）** —— ✅ 复用现成解析引擎（解加密直链）+ 现成 UI 渲染，代码量骤减；Q 系有很多现成主规则可直接套。❌ 用的人必须按**原标题**装好被依赖程序（『配置助手』『模板·Q』『XYQ推送』），缺一个就崩；跨规则调用 PC 测不了要真机；被依赖程序更新/下架会牵连。
- **C. 上聚阅框架（子程序/自包含/做宿主）** —— ✅ 生态成熟、作者持续维护；子程序**用云口令导入超方便**（粘码即装）；主流写法是**一个 `parse` 对象**（`let parse={主页/二级/搜索/解析/最新}`，官方 parseCode 模板，最简、无需 rule.json/libs），可装插件、能做成平台。❌ 需先装聚阅宿主；旧式写法（rule.json+pages+libs）或做宿主时才需连包/维护四件套+远程源（道长仓库已废弃，源以最新包为准）。
- **D. 我不确定，你按站点情况推荐** —— 由 agent 结合第 2 步"是否有参照规则"决定，并遵循本 skill 目标「做能导入即用的规则、借现成模板」：优先看能否挂成熟底座（聚阅子程序 / 模板·Q / 配置助手）以拿到现成 UI+解析、实现导入即用；仅当站点极简单、或用户明确不要底座、或无合适底座时才退回纯规则 A。并向用户说明为何这么选。

> 用户选定后跳到对应骨架（详见 `references/rule_patterns.md` 与各写法利弊速览）：A→模式 A（无依赖纯爬虫）；B→模式 D/F（跨规则程序/模板）；C→模式 B（宿主）/ C（子程序-库打包）/ E（自包含）。**无论选哪种，写完跑 `validate_rule.py` 的 `[依赖识别]` 报告、并按报告告知用户配套安装要求，这一步不能省。**

### 第 4 步：分析站点并生成规则

0. **架构形态已在第 3 步与用户确认**，此处直接套对应骨架。详见 `references/rule_patterns.md`（已沉淀写法：A 普通爬虫 / B 聚阅宿主 / C 聚阅子程序 / D 跨规则程序 / E 自包含子程序 / F Q模板体系 / G·H 短视频流与真搜索 / I 模块化单例引擎 / J 从影视 APK 反查后端）。这一步决定要不要打 `require.json`+`libs.zip`、要不要 `type: all`、要不要 `hiker://` 跨规则调用——形态选错后面全错。**写聚阅子程序优先用新式 `parse` 对象**（模板 `assets/templates/juyue_parse.js`，无需 rule.json/libs）。
1. 以用户给的网址为基础，先抓取判断结构：
   - `curl -L -A "Mozilla/5.0" 网址` 看返回是 HTML 还是 JSON API（Windows 若无 curl，可用本 agent 代为抓取，或 `python -c "import urllib.request;..."`）。
   - 若是 SPA/Next.js，抓 `/_next/static/chunks/*.js` 找 API 端点与字段名。
   - ⚠️ 写 `js:` 时**默认用 ES5**（`var` / `function` / 普通 `for`）——兼容性约定，理由见文末注意事项「JS 语法版本」。
2. 读取对应模板（`assets/templates/<type>_rule.json`）作为骨架，把 `TODO_*` 占位替换为真实值：
   - `title`：站点名；`url`：列表/分类 URL，用 `fyclass`/`fypage` 占位，**API 必须加 `;get;UTF-8;{referer@站点域名}` 修饰符**。
   - `class_name` / `class_url`：分类显示名与 ID，用 `&` 分隔且数量一致；无法确定时先用一个分类占位并提示用户补充。
   - `find_rule`：列表解析。JSON API 用 `js:` + `getResCode()` 解析 `data` 数组；HTML 简单站点用原生 DOM 链（见规范 §5.1），复杂站点用 `parseDomForArray`。
   - `search_url`：搜索地址用 `**` 占位关键词，配套写 `searchFind`。
   - `detail_find_rule`：详情页。视频须提取播放地址并在直链后加 `#isVideo=true#`；图片用 `pic_url` 展示大图；音频取 mp3/m4a 直链。
   - 图片字段统一加 `@Referer=站点域名` 防盗链。
3. 写完后运行校验：
   ```
   python <skill>/scripts/validate_rule.py <输出路径>
   ```
   修复所有 `[错误]`，`[警告]` 尽量处理（尤其是视频 `#isVideo` 与 API 修饰符）。
   - ⚠️ **该校验脚本现已自动打印 `[依赖识别]` 报告**（无依赖 / 库打包 / 跨规则程序 / 框架型）。**若报告命中任何依赖，必须在交付时明确告知用户：本次规则需要哪种依赖、以及配套安装要求**（例如"需按原标题安装『配置助手』，否则解析失效"或"必须连包整体导入，不能只丢 rule.json"）。不要让用户自己从规则里猜依赖。

### 第 5 步：存档并提醒测试

- 将最终 `rule.json` 保存到 `<当前工作区>/海阔视界规则/<title>_rule.json`（目录不存在则创建）。
- 明确告知用户存档路径。
- **建议先在本 PC 用 `scripts/test_rule.js` 跑一遍解析逻辑**（见文末"PC 端测试方法"），确认提取条数、标题、海报、链接无误后再交真机，能省掉大量来回。
- 提醒测试清单（真机侧）：
  - 首页/分类列表是否正常出片与标题；
  - 搜索是否可用；
  - 详情页是否能进入、选集是否齐全；
  - 视频能否播放（看 `#isVideo=true#` 是否生效）、图片/音频防盗链是否正常；
  - 列表项 UI 长相是否符合预期（`col_type` 样式）。
- **告知导入方式（新用户重点）**：
  - **单条规则**（图片/视频/音频/杂类，非工具类）：打开海阔视界 → 底部「我的」→「订阅」/「规则」→「添加规则」→ 直接**粘贴本 `rule.json` 全文**，或选「导入」本地 `.json` 文件（菜单名称随版本略有差异，找不到时搜「添加 / 导入规则」）。仅当第 3 步 `[依赖识别]` 报"无依赖"时适用。
  - **工具 / 小程序类 / 含依赖的规则**：
    - **聚阅子程序**：主流写法是**一个 `parse` 对象**（`let parse = {主页/分类/二级/搜索/解析/最新...}`，模板 `assets/templates/juyue_parse.js`），**不是标准 rule.json**。导入两条路：① **自用最可靠**——聚阅宿主 → 新建接口 → 「parseCode」模板 → 粘贴 parse 代码 → 保存；② **分享用云口令**——让用户在聚阅里"分享→云剪贴板（云 N）"自动生成云口令（格式 `云口令：聚阅接口￥<aesEnc(pasteurl)>￥<源名>(云N)@import=...`），**不要自己拼 AES**（海阔 aesEncode 加密的是 pasteurl 短链、算法是 AES/CTR，无 sharePaste 后端 API 打不了）。旧式 C2（rule.json+pages+libs）才需连包整体导入 `type:all` 包。⚠️ **列表项 url 必加 `#gameTheme#`（二级标识），否则进不了二级菜单选集**。
    - **跨规则程序（Q模板 / 配置助手等）**：主规则本身是普通 `type: video` 等，导入方式同单条规则（粘贴/导入 `rule.json` 即可），但**用之前必须先按原标题装好被依赖程序**（『模板·Q』『配置助手』『XYQ推送』）。
    - **库打包（require.json+libs.zip）**：把 `rule.json` + `require.json` + `libs.zip` 放进 `<站点名>.hk小程序/` 目录整体打包成 zip（参考第 2 步导出的包结构），到 app 里导入该 `.zip`，不能只丢 `rule.json`。
    - **无论哪种**：`[依赖识别]` 命中任何依赖时，必须在交付时明确告知用户"需要哪种底座 / 是否连包"，别让用户自己猜。
  - 导入后**先清一次缓存 / 重启 app**，避免旧规则残留导致"改了没反应"。

### 第 6 步：按测试结果修改

- **改前先备份、改后升版本号**：每次按反馈动手改之前，先把当前 `rule.json` 复制为同目录的 `rule.json.bak`（覆盖式备份，保留上一版即可，便于回退）；改完并校验通过后，把字段 `version` 在原有基础上 **+1**（如 `1` → `2`），再覆盖写入存档路径，并**明确告知用户当前版本号**（例如「已更新到 v2」）。这样既能追溯改动，也方便在 app 里区分新旧规则。
- 用户反馈问题（列表空、播放失败、图片裂图、搜索无结果等）时，回到对应 `find_rule` / `detail_find_rule` / `url` 修饰符定位修正。
- 常见修正方向（见规范 §7）：API 缺 `referer` 修饰符、字段名与站点真实 JSON 不符、`#isVideo=true#` 漏写、图片缺 `@Referer=`、详情需二次请求取真实地址（用 `.lazyRule()`）。
- 每次修改后重新运行 `validate_rule.py`，覆盖写入同一存档路径，并请用户复测。

## PC 端测试方法（test_rule.js）

规则"爬得对不对"可在电脑上用本 skill 的 `scripts/test_rule.js` 预先验证，再上真机。它模拟 Hiker JSEngine 执行规则里的 JS，并模拟占位符替换。

**环境**：Node.js v16+（推荐 v18+），无需第三方包。

**基本用法**（在 rule.json 所在目录执行）：
```bash
# 用本地抓来的 HTML 验证列表解析（最确定，推荐先把页面存成 .html）
node <skill>/scripts/test_rule.js rule.json --rule find_rule --html 列表页.html --fyclass 1 --fypage 1

# 在线抓取并验证（自动忽略 SSL、跟随重定向、带 referer）
node <skill>/scripts/test_rule.js rule.json --rule find_rule \
     --url "https://站点/filmClassifySearch?Pid=1&current=1" --fyclass 1 --fypage 1

# 验证搜索解析（--kw 替换 search_url 的 **）
node <skill>/scripts/test_rule.js rule.json --rule searchFind --html 搜索页.html --kw 钢铁侠

# 验证筛选占位符是否真的改变列表（拼出真实 URL 后抓取）
node <skill>/scripts/test_rule.js rule.json --rule find_rule \
     --url "https://站点/...?Pid=1" --fyclass 1 --fyarea 美国 --fysort hits --fyyear 2024
```

**参数**：
- `--rule`：find_rule（默认）/ searchFind / detail_find_rule
- `--html <file>`：本地 HTML 喂给 `getResCode()`（推荐，离线确定）
- `--url <https>`：在线抓取（忽略 SSL、跟随重定向、带 referer）；**同时把该地址作为 `MY_URL`**（模拟真机当前页地址）
  - URL 里的中文问号 `？？` 会被还原成英文 `?`（与海阔 app 行为一致），便于测 POST 详情传参
- `--kw`：搜索关键词，替换 `search_url` 的 `**`

**规则 JS 内部自己多次请求（如 `batchFetch` 并发拉多页）时，请改用 `scripts/run_rule_js.mjs`**：`test_rule.js` 的沙箱会把这类规则的结果算少（实测同一规则 5 条 vs 真实 11 条）。`run_rule_js.mjs` 先把规则需要的各页并发抓下来做缓存，再把 `fetch`/`getResCode`/`getParam`/`MY_URL` 原样注入规则 JS 执行，输出可信的「条数 / 网络耗时 / JS 耗时 / 未命中的请求数」：
```bash
# 列表：走 batchFetch 并发路径（第 2 参数是分类值，第 3 参数 batch）
node <skill>/scripts/run_rule_js.mjs rule.json 300 batch
# 老版本兜底路径：不注入 batchFetch，规则退化为逐个 fetch
node <skill>/scripts/run_rule_js.mjs rule.json 300 nobatch
# 搜索
RULE_JS=searchFind RULE_KW=钓鱼 node <skill>/scripts/run_rule_js.mjs rule.json 300 batch
```
- `--fyclass/--fypage/--fyarea/--fysort/--fyyear`：占位符取值（拼真实 URL 并打印）
- `--vid <id>`：详情页参数，喂给 `getParam('vid')`（验证 `detail_find_rule` 取播放地址用）
- `--top N`：打印前 N 条样例（默认 5）

**能测 / 不能测**：
- ✅ 能测：提取条数、标题/海报/链接/简介、占位符 URL 拼法、筛选/排序是否真的改变列表。
- ✅ 能测：规则里 `parseDom`/`parseDomForHtml`/`parseDomForArray`/`xpath` 等原生选择器（本桩内置轻量 DOM 引擎 `scripts/lib/mini_dom.js`，支持 `&&`、`--`、`,n`、`\|`、`Text`/`Html`/属性、`[attr=v]` 等）。
- ✅ 能测：规则内用 `fetch()`/`request()`/`batchFetch()`（批量，缩写 `bf`）继续抓下一层页面（本桩用 `scripts/fetch_url.py` 同步抓取，`batchFetch` 逐项串行）。
- ✅ 能测：`base64Encode/Decode`、`md5`、`getParam`、`getVar/putVar/getMyVar/getItem`、`$().lazyRule/rule` 字符串生成、`MY_URL/MY_PAGE/MY_RULE` 等常用量。
- ✅ 能测：**CryptoJS**——本桩内置 `getCryptoJS()` 垫片（用 Node `crypto` 还原 `CryptoJS.enc.Utf8/Base64/Hex` + `AES` 的 CBC/ECB/Pkcs7），规则里 `eval(getCryptoJS())` 后调用 AES 加解密可在 PC 端完整跑通并打到真实接口（见 `references/crypto_sign.md`）。
- ✅ 能测：**本地文件/图片 API**——`fileExist` / `getPath` / `writeHexFile` / `writeFile` / `readFile` / `saveImage` 均已垫片，`hiker://files/` 映射到系统临时目录，可验证「加密封面落地文件加速列表」这类优化（见 `references/crypto_sign.md` §9）。
- ❌ 不能测：UI 渲染长相、播放嗅探、`aesEncode/aesDecode`（海阔版为 AES/CTR，与 CryptoJS 不同）、`rsaEncrypt`、`startProxyServer`、`cacheM3u8`、真机 header 修饰符是否生效、`@lazyRule`/`x5Rule` 在真实 WebView 的执行。
- ⚠️ 若规则用了上述平台专属 API，本桩会明确报错并提示用真机测，不会误判成"0 条"。
- ✅ `--dump out.json`：把解析结果存成 JSON，方便比对。

**工作流建议**：第 3 步与用户确认架构形态（AskUserQuestion 讲利弊）→ 写规则 → 跑 `validate_rule.py`（含 `[依赖识别]` 报告）→ 若命中依赖**必须告知用户依赖类型与配套要求** → 跑 `test_rule.js` 验证解析 → 存档 → 提醒用户真机复测 UI/播放。

### 聚阅子程序（parse 对象）的 PC 验证（test_juyue.js）

聚阅子程序本质是 `let parse = {主页/分类/二级/搜索/解析/最新...}`，不是标准 rule.json，用 `test_rule.js` 测不了。改用本 skill 的 `scripts/test_juyue.js`：

```bash
node <skill>/scripts/test_juyue.js parse.js --fn 主页
node <skill>/scripts/test_juyue.js parse.js --fn 搜索 --kw 关键词
node <skill>/scripts/test_juyue.js parse.js --fn 二级 --url "https://站点/detail/1.html"
node <skill>/scripts/test_juyue.js parse.js --fn 解析 --url "https://站点/play/1.html"
node <skill>/scripts/test_juyue.js parse.js --fn 分类 --fypage 2
```
- ✅ 能测：主页/分类/搜索提取条数、二级返回结构（`detail1/detail2/desc/img/line/list`，多线路是二维数组）、解析出的 m3u8、撞验证码时 `_fetchSafe` 是否返回 🔒 卡片。
- ❌ 不能测：验证码图片识别、`$().input` 用户交互、真机 cookie 持久化、UI 渲染。
- 本桩用 `test_juyue.js` + `fetch_url.py`（Python 同步抓取，含 URL 转码、自定义 UA、POST）+ `mini_dom.js`，与旧实例思路一致。

## 注意事项

> ⚠️ **JS 语法版本：默认写 ES5（兼容性约定，不是语法禁令）**
> **事实**：官方文档（`help_js.md` / `help_rules.md`）里的示例**大量使用 `let` / `const` / 箭头函数**，说明**新版海阔的 JSEngine 支持 ES6+**；但**旧版 App 的引擎只支持 ES5**（本库早期结论即来自此场景，未留存真机复现记录）。
> **本库约定**：规则里的 `js:` 代码**默认用 ES5 写**（`var` / `function` / 普通 `for`），这样任何版本都能跑；**不是"用了 `=>` 就一定报错"**。
> 若你手头的 App 版本实测 ES6 正常，或要移植的现成源本身就是 ES6，**可以放开**；拿不准就写 ES5。
> `scripts/validate_rule.py` / `scripts/test_rule.js` 的 ES5 检查结果按**兼容性提示**看待（不算错误、不影响退出码）。
> **补充实测（2070 条真实规则）**：含箭头函数 `=>` 的 **25%**、`let` **35.8%**、`const` **16.7%**、模板字符串 **5.0%** —— 印证 ES6 在新版引擎里普遍可用。详见 `references/rule_recipes.md`。
> ⚠️ **不要反过来"修"别人的 ES6**：看到他人规则用 `let`/`=>` 不代表写错。
> 💡 注意：本机 `test_rule.js` 跑在 Node 上，**ES6 在 PC 一定通过**，所以"PC 通过"不能证明"真机通过"——这也是本库仍推荐 ES5 的原因。

- 永远以真实站点响应为准，不要臆测字段名；抓取不到就问用户要接口或页面片段。
- 优先 `js:` 写法（灵活、对 JSON/HTML 通吃），原生 DOM 链仅作简单 HTML 站点的快捷选项。
- 老版本海阔视界若 `setResult(d)` 报错，改为 `setHomeResult(d)`。
- **布局逐项混用**：只有 `js:` 解析能对每一项单独设 `col_type`（如列表里第 1 项 `text_1` 当标题、后面 `movie_3` 当卡片）；原生 DOM 链只能用规则级统一值。样式全表见 `references/col_type.md`。
- **请求修饰符顺序固定**：`URL;请求方式;编码;{header}`；JSON API 记得 `;get;UTF-8;{referer@站点}`；URL 里的英文 `?`/`&`/`;` 在 POST 参数或 header 里冲突时用中文 `？`/`＆`/`；；` 代替。
- **二级解析触发铁律**：列表项 `url` 必须带请求修饰符（`;get;UTF-8;{referer@站点}` / `;post;…`），海阔才会当「规则链接」执行 `detail_find_rule`；**不带修饰符的网页地址会被直接当网页打开**，点进去不会出选集。现成范式：`examples/4e63v.rule.json` 的列表项 url = 接口 + `;post;UTF-8;{headers}`。
- **链接强接管（推荐）**：卡片 url 追加 `@rule=js:...`（如 `@rule=js:$.require('引擎').detail()`），让卡片**一定走你自己的 JS**，不会在解析为空时 fallback 成普通网页。剧集/播放项用 `play` 接管，别用 `detail`。——详见 `references/pitfalls.md` §一。
- **自绘搜索框禁用 `hiker://search?s=`**：那是系统级搜索协议，会丢掉本源；要 `@rule` 接回本源 `search()`（见 `pitfalls.md` §一.2）。
- **参数别信 `getParam`**：详情参数从 `MY_URL` 解析，搜索词读 `MY_KEYWORD`（见 `pitfalls.md` §二.6）。
- **序列化回调禁引用闭包变量**：`$.toString` / `$.lazyRule` / `$().rule` / `registerTask` 的回调体是**序列化后独立求值**的，拿不到外层变量（`_H`/`_UA`/循环变量…），要用的一律**当实参传进去**。官方 `help_js.md` 明文警告过。——这是"整页 `ReferenceError`"的头号原因。
- **`fetch` 失败返回字符串 `"error"`**：解析前必须先判 `htm !== 'error'`，否则 `JSON.parse`/DOM 解析整页崩（见 `pitfalls.md` §三.9）。
- **详情页要有样子**：返回顺序固定 `[海报卡] → [简介] → [（可选）线路] → [剧集]`；海报卡 `title` 单行 + `desc` 多行（防留白）；飞跳详情加 `#immersiveTheme#`；可折叠简介用 `rich_text` + `<a href='**单引号**…@lazyRule=.js:'>`。完整可复制代码见 `references/detail_layout.md`。
- **播放地址默认不加 `@headers=`**，确认防盗链再加（见 `pitfalls.md` §五.17）。
- **筛选铁律**：定义了 `area/sort/year` 就必须在 `url` 放 `fyarea/fysort/fyyear`，否则筛选不生效；`fypage` 不能放 URL 最末尾。
- **媒体标识**：视频直链加 `#isVideo=true#`、音频加 `#isMusic=true#`；不想被误识别用 `#ignoreVideo=true#` / `#ignoreImg=true#`。全部标签见 `references/url_tags.md`。
- **多线路/字幕/弹幕/歌词**：`url` 用 JSON 字符串 `{"urls":[...],"names":[...]}`，详见 `references/url_tags.md` §4。
- **进度记忆**：`extra:{id:'全局唯一值'}`，id 要全局唯一，否则多条规则串进度。
- **二级/动态解析**：`链接@lazyRule=选择器`（`&&` 写中文 `＆＆＆＆`）或 `@lazyRule=.js:代码`；`fyIndex` 表示点击位置；见 `references/selector_syntax.md` 与 `references/link_protocols.md`。
- **不要只会粘贴 rule.json**：`[依赖识别]` 命中依赖时，导入方式不同（连包 / 先装底座 / 云口令），务必按报告告知用户。

## 持续学习与自我维护

本 skill 不是写完就完，遇到新情况要把它变强：

1. **官方文档优先**：遇到本 skill 没写的字段/API/标签，先查 `references/official_docs.md` 里的官方链接；确认后**把结论沉淀回对应 references 文件**（不要只存在对话里）。
2. **真机反馈回填**：用户复测反馈的问题（列表空、播放失败、图裂、验证码、导入失败）修完后，把"症状 → 根因 → 修法"追加到 `references/rule_format.md` 的常见坑或本文件的注意事项，避免下次再踩。
3. **新规则形态**：遇到新的依赖/框架写法，追加到 `references/rule_patterns.md` 的模式列表，并让 `validate_rule.py` 的 `detect_dependencies()` 能识别它（补判据 + 配套安装要求）。
4. **脚本随规则进化**：PC 测试桩能覆盖的 API 越全，越省真机往返。遇到桩不支持的常用 API，优先在 `scripts/test_rule.js` / `scripts/lib/mini_dom.js` 补桩（补不了的要明确报"平台专属 API，请真机测"，不要静默返回空）。
5. **改脚本要自测**：改完用 `assets/templates/*.json` 与一段假 HTML 跑通再收尾；官方文档更新时同步 `official_docs.md` 的快照说明。
