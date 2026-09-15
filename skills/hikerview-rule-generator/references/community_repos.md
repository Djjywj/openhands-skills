# 海阔视界 GitHub 社区仓库索引（写源时去哪抄、去哪找现成规则）

> 2026-09 用 GitHub Search API 多关键词（`hikerview` / `海阔视界` / `hiker rule` / `topic:hikerview` …）扫描 215 个仓库后筛出的**有用**索引。
> 用途：① 找**同类型现成规则**当参照（第 2 步「有没有参照规则」的答案来源）；② 找**已沉淀的经验文档**别重复踩坑；③ 找**源码/工具**验证行为。
> ⚠️ 这些是**第三方**内容，抄之前按 `pitfalls.md` §八 的「不要照抄」原则核对：能在**官方文档**找到出处的才当铁律，否则标"待验证"。

## 1. 规则集合仓库（可直接拆包当参照）

| 仓库 | 星 | 内容 | 怎么用 |
|------|----|------|--------|
| `TyrantG/hikerViewRules` | 51 | **海阔规则源码集合**（原「海阔视界规则源码集合」，分 `VIDEO/IMAGE/LIVE/READ/COMIC/TOOL/HOME/GHS` 等目录，`.js` 源文件） | 作者侧写法，**最权威的社区参照**；按类型目录找同类型源。注意此仓库属 `TyrantG`，`qiusunshine/hikerViewRules` **不存在**（易记混） |
| `qiusunshine/hiker-rules` | 128 | 官方账号的示例小程序规则（`示例/batchExecute.js`、`urlInterceptor.js`、`imageDecode.js`、`rules/sub/adblock.txt`、`live/视界世界*.js`） | 学官方 API 用法（批量任务/URL 拦截/图片解码/直播源） |
| `RebornQ/HikerDepotRules` | 41 | 仓库型规则（`manifest.json` 带「分类仓库模板」，内含 base64 口令式规则） | 看**仓库/合集**型规则的 manifest 结构与更新机制 |
| `xyq254245/HikerRule` | 27 | `ZYWCJ.txt`（自用仓库合集）、`m3u8_ad_rule.json`（**m3u8 去广告规则**）、`hikermovie.js` | m3u8 广告片段剔除的现成规则（配 `clearM3u8Ad`） |
| `lzk23559/rulehouse` / `dzhiker/house` | 5 | 仓库规则 / 道长仓库 | 仓库型合集参照 |
| `ThomasBy2025/hikerview` | 12 | 小程序集合，含 `gcsp1999/config/*`（global/preRule/getMusicInfo/ruleInstallPop/themeList/collectionList/putImportCode） | **主题/收藏/音乐信息/规则安装弹窗**等工具型源码，模块化写法参考 |
| `supermiee/hairu` | 0 | 海阔小程序规则（重构版） | 重构后的写法参考 |
| `hjdhnx/hiker` / `hjdhnx/hikerPy` | 24 / 5 | 海阔视界静态资源 + `libs/dr.js` 依赖库 + Python 规则 | 「道长 DR 模板」依赖库真身；看 `proxy` 字段的真实用法 |
| `Fanc9527/zytvbox` | 6 | 自收集的一些**海阔能用且比较优质的 TVBox 源** | TVBox 系规则参照 |
| `ZGQ-inc/source` / `source_repo` | 1268 / 18 | 大型整合：书源/图源/订阅源/规则/直播源 | 找各类源的大型整合库 |
| `oevery/Source` | 267 | 阅读书源、**海阔阅览器搜索源、插件** | 网页插件（`js_url`）参照 |
| `kingkare/-` | 1 | **`海阔4904个小程序.json`（14.7MB 原始 / 2070 条去重规则全量语料）** | **最有价值的统计样本**：能直接量出字段使用率、col_type 分布、`preRule` 用法占比（见下方 §4） |

## 2. 他人写的「写源 skill」（可对照，注意甄别）

| 仓库 | 说明 |
|------|------|
| `wsh-feiyu/hikerskill` | 竞品技能库（`SKILL.md` + `references/`），自述基于 **2070 个真实源语料**蒸馏。有 `layout-design.md`(1030行)、`ui-template.md`(869行 UILib 渲染引擎)、`production-patterns.md`、`search-implementation.md`、`examples/qingdou-architecture.md`(青豆剧场剖析) 等 |

> ⚠️ **该库已知问题**（已在本库 `pitfalls.md` §八 记录）：① 其自身定义 `setDesc` 辅助函数却当成内置 API 写；② 示例混用 ES6（与本库 ES5 约定冲突）；③ 库内提到 `list_1` 这类**非官方 col_type**；④ **无 PC 验证能力**（自述"不内置模拟器"）。
> ✅ **可采信的部分**：与**官方文档**一致的结构化整理（`col-types.md` / `link-schemes.md` / `selector-syntax.md` / `js-api.md` / `checklist.md`）——本库已逐条对官方文档核验后采纳。

## 3. 源码与工具（验证行为 / 开发辅助）

| 仓库 | 星 | 说明 |
|------|----|------|
| `qiusunshine/hikerView` | 757 | **海阔视界 App 源码**（Java）。想确认某个字段/参数的真实行为（如 `getParam` 默认取 `MY_URL`、`HttpParser` 如何切 `;post;`）**看源码最准**，本库多条「源码结论」即出自此 |
| `Lingyan000/hikerview-player` / `air` | 71 / 25 | 电脑版播放器 / 海阔电脑版（Electron + TS） |
| `Lingyan000/hiker-nice` | 5 | **Node.js 写海阔规则的工具包**（TS，`lib/http/*` 实现了一套 fetch/请求封装） | 想在 PC 端用 TS 写规则时参考 |
| `Gumingjie0312/Hiker_Tool` | 0 | VSCode 插件：**编辑海阔规则** |
| `qiusunshine/hikerview-old` | 2 | 老版本源码 | 排查"旧版引擎只支持 ES5"这类版本差异时对照 |
| `yijun01/com.fuck.risk`（+ Xposed 仓库） | 31 | 解除导入文件检测校验（**与本技能无关，仅为说明存在该生态**；自行判断风险） |

## 4. 从 2070 条真实规则语料量出的**事实**（写源时的取值依据）

来源：`kingkare/-` 的 `海阔4904个小程序.json`（去重后 2070 条，2026-09 抓取）。

**字段使用率**（`str(v).strip() not in ('','[]','{}')` 计为已用）：

| 字段 | 使用率 | 备注 |
|------|--------|------|
| `preRule` | 2055/2070 存在（其中非空 **731**，35%） | 443 条含 `require`（远程库为主）、89 条 `initConfig`、25 条 `eval(`、16 条 `confirm(` |
| `pages` | 1912/2070 存在（其中非空 **480**，23%） | 模块化/多子页面源 |
| `titleColor` | 563 条存在（非空 **384**） | 非空值里 312 条是 8 位、316 条以 `#ff` 开头 → **8 位 ARGB 是主流写法** |
| `icon` | 2001/2070 存在 | 列表卡片角标/图标 |
| `proxy` | 1154 条存在 → **真用 `=` 语法的仅 5 条** | 绝大多数是**空字符串占位**，实际极少用 |
| `firstHeader` | 304 条非空，值只有 `class`(301) / `year`(2) / `sort`(1) | 见 `rule_format.md` §1.1 |
| `area_name`/`sort_name`/`year_name` | 非空 508 / 248 / 431 | 筛选字段用得比想象中多 |
| `sdetail_find_rule == '*'` | **1240/2070（60%）** | "三级继承二级/自动嗅探"是主流 |
| `detail_col_type` 非空 | 1789/2070（86%） | |
| `chapter_find` / `movie_find` | 各 3 / 2 条 | 极冷门 |

> ⚠️ **口径说明**：早期统计把"键存在"当成"已使用"，会把 `preRule`/`proxy` 这类**普遍存在但多为空串**的字段算高。
> 上表同时给出两种口径，**"非空"才是真实使用率**。
> 分母是 2070（去重后的规则数）；原始文件约 4900 条、14.7MB，含大量重复与失效源。

- `find_rule` 以 `js:` 开头：**1828/2070（88%）** —— **主流写法就是纯 JS**，原生 DOM 链是少数派。
- **分页参数名没有统一约定**（语料内 `fypage` 赋值共 968 处）：`page=`（465）、`pg=`（320）、`p=`（73）、`pn=`（17）、`start=`（15）、`mid=`（14）…——**照站点真实接口字段写**，别默认套 `fypage=...`。

**`type` 实际取值**（2070 条）：

| type | 条数 | | type | 条数 |
|------|------|---|------|------|
| `video` | 1013 | | `read` | 33 |
| `other` | 327 | | `live` | 31 |
| `tool` | 91 | | `news` | 26 |
| `all` | 63 | | `cartoon` | 15 |
| `music` | 47 | | `''`(空) | 384 |
| `picture` | 40 | | | |

> ⚠️ **`audio` 与 `image` 在真实语料里是 0 条**！音频类用 `music`、图片类用 `picture`。本库早期模板用了 `audio`/`image`（官方文档未明列 `type` 取值），**照真实生态应以 `music`/`picture` 为准**——`audio`/`image` 仅作兼容保留，新写规则请优先填写语料中实际存在的值。

**`preRule` 用法分布**：远程库加载 443（最多）、`initConfig` 89、`eval(` 25、`confirm(` 16。

## 5. 检索技巧（下次要再扫一遍时）

```bash
# 仓库搜索（中文关键词必须 URL 编码，否则 API 报 JSON 解析错误）
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/search/repositories?q=$(python3 -c "import urllib.parse;print(urllib.parse.quote('海阔视界'))")&sort=stars&per_page=50"
# 代码搜索（找具体字段/API 的真实用法）
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/search/code?q=firstHeader+hikerview"
```

**踩过的坑**：① 直接拼中文查询串会返回非 JSON（`Expecting value: line 2`），必须 `urllib.parse.quote`；② 用 `gh` 时别用 `--` 分隔中文；③ 搜索结果里混进大量无关仓库（hiking/FYP/subscription），按 `description` 含「海阔/hiker/视界」过滤。
