# 选择器语法（官方 help_rules / help_film_list_rules 蒸馏）

## 1. 基本格式
- 列表规则：`列表;标题;图片;描述;链接`（小程序/首页频道）
- 二级列表：`列表;标题;图片;描述;链接;显示样式`（可嵌套，见 link_protocols.md）
- 搜索规则：`列表;标题;链接;描述;详情;图片`（前三必选，后三可 `*` 占位）

## 2. 选取操作符
| 写法 | 含义 |
|---|---|
| `&&` | 取子元素（向下一层） |
| `--` | 排除：`body--a&&a&&href` 排除第一个 a 后取下一个 |
| `,n` | 取第 n 个（从 0 开始）：`body&&a,1`；`,-1` 倒数第一个 |
| `Text` | 取文字 |
| `Html` | 取含标签的文本 |
| 其它 | 默认取属性（`src`/`href`/`data-original`…） |
| `+` | 多选择器结果拼接：`a,0&&title+'--'+a,1&&title`（拼接串用单引号包） |
| `||` | 或：`body&&#app||#app2&&Text`（先 #app 找不到再 #app2） |
| `.js:代码` | 取到值后再用 JS 处理：`a&&href.js:'https://x.com/?id='+input` |
| `js:` 开头 | 整段规则用 JS 写 |
| 中文 `＋` | 末尾要用 `.js:` 处理时的连接符 |

## 3. 选择器本身
- `#id`、`.class`、`tag`，类似 `querySelector`。
- 支持 Jsoup 原生语法：`body img[src$=.png]&&src` 等。
- 更多：<https://www.open-open.com/jsoup/selector-syntax.htm>（只要不与 `&&`/`||` 冲突即可用）。

## 4. 示例
```
# 小程序/首页频道
body&&#post-list&&li;a&&title;img&&src;.index-intro&&Text;a&&href
# 二级列表（按点击位置）
body&&.stui-content__playlist,fyIndex&&li;a&&Text;*;*;a&&href;text_3
# 搜索
.list-content&&.u-movie;h2&&Text;a&&href;.pingfen&&Text;.meta&&Text;img&&data-original
# 链接继承（二级直接用上级链接）
body&&li;a&&Text;*;*;*
```

## 5. 与 JS 的取舍
- 简单/结构规整的 HTML：优先原生 DOM 链（无需写 JS，直观）。
- JSON API、SSR/Next.js、结构复杂或需拼接字段：用 `js:` + `getResCode()`/`parseDomForArray`。
- 注意 ES5 限制（见 `rule_format.md` §5.2 与 `js_api.md` 开头）。
