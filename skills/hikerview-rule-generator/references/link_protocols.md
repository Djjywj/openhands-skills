# 链接协议 / 子页面 / 导入格式（官方 help_link / help_auto_import / help_film_list_rules 蒸馏）

## 1. hiker:// 与其它伪协议
| 链接 | 作用 |
|---|---|
| `hiker://home@规则名` | 展开首页频道（小程序内；支持 `规则1‖规则2‖http://...` 补偿） |
| `hiker://bookmark` / `history` / `collection` / `download` | 书签/历史/收藏/下载页 |
| `hiker://search?s=词[&group=分组][&rule=规则][&simple=false]` | 打开搜索 |
| `hiker://empty` | 返回空字符串（进二级不自动请求，再用 `@rule` 拉） |
| `hiker://page/xxx` | 子页面（可加 `?rule=规则名` 跨规则） |
| `hiker://debug` / `setting` / `js` / `adUrl` / `adRule` / `webdav` / `webRule` | 调试/设置/插件/拦截/备份/Web编辑 |
| `rule://<base64完整口令>` | 点击导入规则口令 |
| `海阔视界，...` 开头 | 识别为口令，提示导入 |
| `toast://文本` | 提示 |
| `input://{json}` | 弹输入框，`{"value":"默认","js":"'toast://'+input","hint":"提示"}` |
| `confirm://提示.js:'...'` | 弹确认框 |
| `select://{json}` | 下拉选择框 |
| `copy://内容.js:'...'` | 复制到剪贴板 |
| `pics://url1&&url2` | 多图模式（漫画），下拉自动下一章 |
| `javascript:...` | 彩蛋模式（跳浏览器执行 JS） |
| `x5://url` | X5 全屏打开网页 |
| `web://url` | 强制用网页打开，忽略二级解析 |
| `x5Play://url` | 强制 X5 播放器播放 |
| `x5WebView://url` | 刷新当前页 X5 链接 |
| `webRule://url@JS` | 系统内核网页嗅探（不依赖 X5） |
| `x5Rule://url@JS` | X5 内核网页嗅探，JS 每 250ms 执行，返回非空即取到资源，30s 超时 |
| `video://url` | 直接进播放器并自动嗅探网页视频；extra 支持 `blockRules/js/videoRules/videoExcludeRules/cacheM3u8` |
| `download://url` | 下载文件（视频/音频/APK） |
| `share://hiker://files/a.txt` | 分享文件 |
| `fileSelect://JS代码` | 选文件，JS 内用 `input` 取路径 |
| `editFile://hiker://files/a.txt` / `openFile://...` | 编辑 / 第三方打开 |
| `func://background` | 新窗口隐藏到后台 |

## 2. 子页面（hiker://page）
- 按钮 `url` 设为 `hiker://page/index.html` 即进入子页面（界面优化过的二级）。
- 传参方式一：URL 带 query，子页面用 `getParam('type')` 取；含 `?`/`&` 冲突用中文 `？`/`＆`。
- 传参方式二：上级按钮 `extra:{key:'1'}`，子页面用 `MY_PARAMS.key` 取（哪怕一个参数也要对象）。
- 进入子页面默认加载 `hiker://page/xxxx`；要加载别的链接用 `?url=` 参数，或 `extra:{url:'...'}`。
- 跨规则子页面：`hiker://page/index?rule=规则名`。
- `request('hiker://page/detail')` 返回子页面定义对象字符串。

## 3. 二级列表 / 动态解析（help_film_list_rules）
- 语法：`列表;标题;图片;描述;链接;显示样式`（后两项可省，样式缺省继承上级）。
- 深层嵌套：多条规则用 `==>` 连接；链接位置写 `*` 表示继承上级链接。
- 按点击位置用不同规则：`fyIndex`。
- 搜索的二级规则若与首页完全相同，直接写 `*`。
- 动态解析：链接后加 `@lazyRule=选择器`（选择器内 `&&` 用中文 `＆＆＆＆` 代替）或 `@lazyRule=.js:代码`；纯 JS 深层嵌套用 `@rule=...`。
- 用 `$()` 工厂书写更清晰：
  ```js
  d.push({url: $('url').lazyRule(() => setError(input))})
  d.push({url: $(parseDom(key,'a&&href')).lazyRule((obj)=>{ var h=fetch(input); }, {word:'x'})})
  d.push({url: $('url').rule(() => setError(input))})
  ```
- `#noLoading#` 可加在动态解析链接上不显示 loading。

## 4. 导入格式（help_auto_import）
口令统一形如 `海阔视界，<标识>￥<内容>`：
| 标识 | 用途 |
|---|---|
| `home_rule_url` | 首页频道合集（json 地址） |
| `home_rule` | 单条首页频道（json 对象字符串） |
| `search_engine_url` / `search_engine_v2` | 搜索引擎合集 / 单条 |
| `js_url` | 网页插件（`名称@地址`） |
| `ad_url_rule` | 广告网址拦截 |
| `bookmark` / `bookmark_url` | 书签规则 / 合集 |
| `file_url` | 本地文件 |
| `home_sub` | 合集规则订阅 |
| `require_url` | 更新依赖 |
| `web-proxy` | 浏览器代理规则（`{"name","match"}`） |

**云口令自动导入**：`@import=js:`，前面换行后的内容为 `input`。
```
云口令，复制整条口令打开软件即可导入\nhttps://xxx.cn/test.json@import=js:fetch(input)
```
返回获取到的规则口令即可导入；也可用 `writeFile` 落地文件。

## 5. 规则内点击导入 / 仓库型规则
- 按钮 `url` 用 `rule://` + base64（完整口令，含"海阔视界"字样）即可点击导入。
- 或 `url` 以 `海阔视界` 开头，视界识别为口令。
