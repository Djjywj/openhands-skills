# col_type 布局全表（官方 help_col_type 蒸馏）

> 每个列表项都可单独设 `col_type`；不设则继承规则级 `col_type`。
> 仅 `js:` 解析支持逐项混用（`it.col_type='text_3'`），原生 DOM 链/普通规则只能用规则级统一值。

> 🔒 **权威清单**（2026-09 从 **App 源码 + App 内置资源**核对，比在线文档更全）：
> - `app/src/main/assets/help_col_type.json` 收录 **48** 个（在线文档 `help_col_type.md` 少 3 个：`icon_3_fill`、`icon_3_round_fill`、`card_pic_3_center`）。
> - `ArticleColTypeEnum.java` 另有 3 个**未进任何 help** 的：`pic_1_card`、`big_blank_block`（另 `header`/`footer` 是内部占位，不要手写）。
> - **本 skill 的 `scripts/validate_rule.py` 的 `VALID_COL_TYPES` 已按此补全**。在线文档与 App 不一致时**以 App 为准**。

## 影视频道类
| col_type | 说明 |
|---|---|
| `movie_3` | 一行三列，图+名+描述，圆角矩形图（**默认样式**） |
| `movie_3_marquee` | 同 movie_3，标题超长跑马灯 |
| `movie_2` | 一行两列，圆角矩形图 |
| `movie_1` | 一行一列，信息多时用；`extra:{lineVisible:false}` 隐藏分界线 |
| `movie_1_left_pic` | 一行一列，图左文右 |
| `movie_1_vertical_pic` | 图左文右，竖图（高>宽） |
| `movie_1_vertical_pic_blur` | 同上，背景为高斯模糊图；`extra:{gradient:true}` 背景渐变 |

## 文本类
| col_type | 说明 |
|---|---|
| `text_1` | 一行一列文本，支持红/橙混排；`extra:{lineVisible:false}` |
| `text_center_1` | 居中文本 |
| `text_2` / `text_3` / `text_4` / `text_5` | 一行 2/3/4/5 列文本；`extra:{textAlign:'left'}` 左对齐（默认居中） |
| `long_text` | 长文本不截断；`extra:{textSize:18}`（默认 16.5，须整数） |
| `rich_text` | 富文本（含 HTML）；`extra:{textSize:18, lineSpacing:10}`；小图加 `#originalSize#` |

## 图片类
| col_type | 说明 |
|---|---|
| `pic_3` | 一行三列，只显示图片（图站用） |
| `pic_3_square` | 一行三列正方形 |
| `pic_2` | 一行两列，直角矩形图 |
| `pic_2_card` | 一行两列竖图，壁纸类 |
| `pic_1` | 一行一列大图 |
| `pic_1_full` | 一行一列，宽度满屏、高度按比例自适应 |
| `pic_1_center` | 居中自适应（验证码等小图，勿放大图） |

## 图标类
| col_type | 说明 |
|---|---|
| `icon_4` | 一行四列，上图上标签 |
| `icon_4_card` | 同上，圆角矩形图 |
| `icon_small_4` | 上图上标签，小图 |
| `icon_small_3` | 一行三列，左图右标签 |
| `icon_round_4` | 圆形图，一行四列 |
| `icon_round_small_4` | 圆形小图，一行四列 |
| `icon_2` | 一行两列，左图右标题 |
| `icon_2_round` | 左圆图右标题 |
| `icon_3_fill` | 一行三列，左图标右文字（类似 `icon_2_round`，只是三列） |
| `icon_3_round_fill` | 一行三列，左**圆形**图标右文字 |
| `icon_1_search` | 单行"假输入框"，只能点击 |
| `text_icon` | 左文字右图标 |
| `avatar` | 头像样式，需 title+img，可选 desc 显示在右侧（支持富文本） |

## 分割/占位
| col_type | 说明 |
|---|---|
| `line` | 分割线 |
| `line_blank` | 空白分割线（同 pic_1 分割线） |
| `blank_block` | 空白块，宽=屏宽，高=1dp |
| `big_blank_block` | 更大的空白块（比 `blank_block` 高，做大型间隔用） |
| `pic_1_card` | 一行一列卡片式大图（`pic_1` 的卡片变体） |

## 按钮/输入
| col_type | 说明 |
|---|---|
| `flex_button` | 流式自适应布局，连续 push 多个自动聚合，标题支持 HTML |
| `scroll_button` | 滚动布局，连续 push 多个自动聚合，不换行，标题支持 HTML |
| `input` | 单行输入框。`{url:"'toast://'+input", col_type:'input', title:'搜索'}`；`extra:{onChange:"..."}`、`{titleVisible:false}`、`{defaultValue:'x'}`、`{type:'textarea'/'password'/'number'}`、`{type:'textarea',height:-1}`（-1 自适应，正整数为倍数，默认 3）、`{highlight:true}` |

## 卡片/网页/特殊
| col_type | 说明 |
|---|---|
| `card_pic_2` | 方形卡片，一行两列，背景高斯模糊；`desc` 填 0-25（默认 15，0 不模糊） |
| `card_pic_1` | 同 card_pic_2，独占一行 |
| `card_pic_2_2` | 一行两列、每列上下两卡（连续 push 两个自动聚合，超过 2 个不显示），只用于右侧；`desc` 可填高度数字 |
| `card_pic_2_2_left` | 同上，只用于左侧 |
| `card_pic_3` | 一行三列，圆角矩形图 |
| `card_pic_3_center` | 一行三列，圆角矩形图 + **文字居中**（`card_pic_3` 的居中版） |
| `x5_webview_single` | 腾讯 X5 组件，宽=屏宽，高默认 240（可写 desc，`auto` 自适应）。**一个页面只能有一行**。常用 extra：`canBack`、`ua`、`js`、`jsLoadingInject`、`blockRules`、`referer`、`urlInterceptor`、`floatVideo`、`showProgress`、`autoPlay`、`imgLongClick`。高度可用 `desc:'float&&240'`、`'list&&video'`、`'list&&screen-100'` |

## 常见搭配建议
- 影视列表：`movie_3`（默认）或 `movie_1_vertical_pic`
- 剧集选集：`text_3`（一行三列），每组线路前用 `text_1` 做线路标题
- 图片站列表：`pic_3` / `pic_2_card`；详情大图：`pic_1` / `pic_1_full`
- 分类筛选按钮行：`scroll_button` 或 `flex_button`
- 提示/空状态：`text_center_1`

## ⚠️ 颜色标记 `““””` / `‘‘’’` 只在 `text_1` 生效
官方文档：在 `text_1` 里，`““文字””` 让文字变**红**、`‘‘文字’’` 让文字变**橙**（例如 `““小棉袄””‘‘真帅’’啊`）。
- 这两个是**成对包裹内容**的标记，写空对（如 `‘‘’’` 后面没有内容）没有意义。
- **在 `rich_text`、`movie_*`、`scroll_button` 等其它 col_type 上不生效**，会原样显示成一串引号（用户会以为是乱码）。
- 上色要分布局：`rich_text` 用 HTML（`<font color="#RRGGBB">`），`text_1` 用引号混排。**绝不要把 HTML 塞进 `text_1`**（会原样显示成标签）。详见下方「`text_1` 不支持 HTML」。

## ⚠️ 颜色值只用 6 位十六进制；装饰符号用参考包验证过的
真机上遇到过两类「乱码」：
- **8 位颜色（ARGB，如 `#ff22d59c`、`#ff148e8e`）不被识别**，`scroll_button` 等布局会渲染异常；一律写成 **6 位**（`#22D59C`、`#8e8e8e`），格式 `color="#RRGGBB"`（参考包 `.fontcolor()` 产出的就是这个）。
- **`▐`（U+2590）等方块/制表符在部分机型字库缺失**，会显示成方块或问号；正文标题不要用它，纯色加粗即可。需要用符号时优先 ASCII 或常见中文标点。

## ⚠️ `text_1` 不支持 HTML（实锤截图证据）
- 官方文档：`text_1` 只支持**红/橙混排的引号写法**（`““红””‘‘橙’’`），**不支持 HTML**。
- 实机截图确认：往 `text_1` 里塞 `<font color="#8e8e8e">简介：…</font>`，**标签被原样显示**成
  `<font color="#8e8e8e">简介：…`，用户会当成乱码。
- `rich_text` 支持 HTML（文档示例 `<span>111<font color="#666666"></font></span>`）。
- `scroll_button`/`flex_button` 文档称“文本标题支持 html”，但为稳妥，顶部导航先用纯文本。
- **最保险策略**：拿不准时全部用纯文本。确认干净后，只在 `rich_text` 里加颜色。
- 自检：`python3 -c "import json,re;print(re.findall(r'<[a-zA-Z/][^>]{0,30}>',open('mini/rule.json',encoding='utf-8').read()))"`
  必须为空数组。

## 美化（安全上色手段，按可靠度排序）
1. **`rich_text` + HTML**：`{title:'<font color="#22D59C">剧集</font>', col_type:'rich_text', extra:{textSize:17, lineVisible:false}}`。
   支持 `<span>/<font>`、`textSize`、`lineSpacing`。分类标题、搜索结果标题用这个。
2. **`text_1` 引号混排**（官方文档明确支持）：`““红字””`、`‘‘橙字’’`。
   例：`'““简介：””' + 正文 + '““[详情]””'`；线路名 `'‘‘lzm3u8’’'`。
   **只在 `text_1` 生效**，用在别的 col_type 会原样显示引号。
3. 布局本身：`pic_1_full`（通栏大图横幅，副标题放 `desc`）、`movie_3`（一行三列卡片）、
   `text_4`（一行四列选集）、`movie_1_vertical_pic_blur` + `extra:{gradient:true}`（详情头图）。
   `extra:{lineVisible:false}` 去掉分界线更清爽。
4. 不要用的：8 位色值、`▐` 之类方块符号（字库可能缺）、把 HTML 塞进 `text_1`。

## 读取用户截图（本机无法直接看图时）
用户传的图会以 base64 存在事件里，可提取后用 OCR 读字：
- 提取：读 `/workspace/conversations/*/events/event-*.json` 的 `llm_message.content[*].image_urls`，
  按 `data:image/...;base64,` 解码存盘。
- 识别：`sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim`，然后
  `tesseract img.jpg - -l chi_sim --psm 6`。
- 这招能从截图里读出字面显示的乱码（如 `<font color=...>`），是定位渲染问题的最快路径。

## ⚠️ 改了规则但用户说“没变化”：先查版本号与残留
- 海阔按 `version`（或小程序名称）判断是否覆盖，**版本号不变会导入失败/看起来没更新**；生成器应每次自动 `version += 1`。
- 让小程序的 `title` 带上版本（如 `大马猴影视v5`），用户一眼能确认加载的是不是新版。
- 导入前让用户**先删除旧的小程序**再导入，避免打开旧副本。
