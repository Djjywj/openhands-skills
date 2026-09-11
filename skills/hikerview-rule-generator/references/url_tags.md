# URL 占位符、请求修饰符与 #标签#（官方 help_rules/help_link/help_tag 蒸馏）

## 1. 占位符
| 占位符 | 含义 |
|---|---|
| `fyclass` | 分类（由 `class_url` 代入） |
| `fypage` | 页码（从 1 递增） |
| `fyarea` | 地区筛选（由 `area_url` 代入） |
| `fysort` | 排序筛选（由 `sort_url` 代入） |
| `fyyear` | 年份筛选（由 `year_url` 代入） |
| `fyAll` | 同时替换分类/年代/地区（**有 fyAll 就不能再有其它替换词**） |
| `**` | 搜索关键词（URL 编码后代入）；若与站点冲突可用 `%%` |
| `fyIndex` | 二级列表里"点击位置"索引（同一条规则按点击项用不同选择器） |

**分页进阶**：`fypage@-1@*20@` 表示 0,20,40…；`fypage.html[firstPage=http://a.com/]` 表示首页特殊地址。
⚠️ `fypage` 不可放 URL 最末尾，否则加个无效串如 `?_t=0`。

**筛选铁律**：定义了 `area/sort/year` 字段，`url` 就必须放对应 `fyarea/fysort/fyyear`，否则筛选点了不生效。

## 2. 请求修饰符（`;` 分隔，顺序固定）
格式：`URL;请求方式;编码;{header}`
- 请求方式：`get` / `POST`（可省略，省略则默认 GET）
- 编码：`UTF-8` / `GBK` / `gb2312` 等
- header：`{Referer@https://x.com&&User-Agent@PC}`，值支持 js：`Cookie@id.js:input`
  - header 内含英文分号需用两个中文分号 `；；` 代替
- POST 传参：参数写 URL 里，app 自动转 body；URL 内含问号用两个中文问号 `？？` 代替
  - ⚠️ **踩坑实战**：`;post;` 的链接里如果写英文 `?`（例：`.../getTimeStamp?vid=123;post;...`），
    海阔 URL 解析器会把 `?` 当成查询串起点，`;post;` 修饰符被截断，**详情页参数传不进去**，
    表现为：进详情报「链接为空，规则有误」、接口返回「缺少参数」。
    正确写法：`.../getTimeStamp？？vid=123;post;UTF-8;{...}`。
  - 规则里读参数时两种问号都要兼容：`MY_URL.match(/[?？&]vid=(\d+)/)`。
- POST JSON：用 `JsonBody=` 参数，如 `http://x.com?JsonBody={"k":"**"};POST;UTF-8;{...}`
- 参数值支持 js：`http://x.com?ts=.js:new Date().getTime()`
- 链接本身支持 js：`http://a.com.js:input+'/'?a=b.js:input+'a'`

> `getResCode()` 取 HTML 的普通列表页**不需要** `;get;UTF-8;`；只有 JSON API（`JSON.parse`）或明确需要 referer/编码时才加。本 skill 校验脚本按此判定。

## 3. `#标签#` 全表（识别完自动清除，仅做标识）
| 标签 | 作用 |
|---|---|
| `#isVideo=true#` | 强制识别为视频 |
| `#ignoreVideo=true#` | 强制不识别为视频 |
| `#isMusic=true#` / `#ignoreMusic=true#` | 强制/禁止识别为音频 |
| `#ignoreImg=true#` | 强制不识别为图片 |
| `#immersiveTheme#` | 沉浸式（仅二级/子页面） |
| `#fullTheme#` | 全屏（仅二级/子页面） |
| `#readTheme#` | 阅读模式（电子书正文，支持翻页/进度记忆） |
| `#gameTheme#` | 游戏模式（全屏+右上角菜单，不显示状态栏） |
| `#autoPage#` | 自动翻页（小说章节） |
| `#autoCache#` / `#cacheOnly#` | 页面自动缓存 / 仅用缓存 |
| `#noRefresh#` | 禁止下拉刷新 |
| `#background#` | 后台播放音频 |
| `#pre#` / `#noPre#` | 强制/禁止预加载 |
| `#originalSize#` | 大图按原尺寸加载 |
| `#noLoading#` | 不显示 loading 弹窗 |
| `#noHistory#` | 不记录足迹（加在上一级跳转链接上） |
| `#noRecordHistory#` | 不记录历史记录 |
| `#ignoreM3U8#` | 不按 m3u8 处理 |
| `#m3u8` / `#isM3u8#` | 强制按 m3u8 识别 / 忽略 content-type 校验 |
| `#memoryPosition=full#` | 播放进度按完整 URL 记忆（区分不同 query） |
| `#noLoading#` | 见上 |

## 4. 视频多线路 / 字幕 / 弹幕 / 歌词（url 用 JSON 字符串）
```js
// 多线路
{url: JSON.stringify({urls:['http://x/1.mp4','http://x/2.mp4'], names:['超清','高清']})}
// 带 header（header 内英文分号用两个中文分号；；）
{urls:['http://x/1.mp4'], headers:[{'Referer':'xxx'}]}
// 外挂字幕 srt/vtt/ass
{urls:['http://x/1.mp4'], subtitle:'http://x/1.srt'}
// 弹幕（B站xml / JSON[{"text":"弹幕","time":5.23}] / web://自定义webview）
{urls:['http://x/1.mp4'], danmu:'http://x/1.xml'}
// 歌词
{urls:['http://x/1.mp3'], lyric:'http://x/1.lrc'}
// 音频分离：urls 与 audioUrls 数量一致（或 audioUrls 只有一个则复用）
{url: JSON.stringify({urls:[url], audioUrls:[audio]}), col_type:'text_3'}
```

## 5. 播放进度记忆
`extra:{id:'全局唯一值'}`。id 必须全局唯一（否则与其它规则串），常取唯一选集链接或"规则名+资源ID"。未设置则取无参数链接。

## 6. Cookie 管理
app 默认自动解析响应 `set-cookie` 并在后续请求自动携带；手动注入的优先。读取：`getCookie(url)`。
