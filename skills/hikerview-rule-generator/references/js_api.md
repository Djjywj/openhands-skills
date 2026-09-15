# JS API 速查（官方 help_js / $ 文档蒸馏）

> ⚠️ 规则里的 `js:` 跑在 **ES5**（`var`/`function`/普通 `for`，禁 `let/const/=>/\``）；
> 聚阅子程序 `parse` 对象的运行时可支持 ES6（见 `rule_patterns.md`）。以下 API 两种环境大多通用。

## 1. 输出结果
- `setResult(d)`：通用输出（数组）。老版本报错改 `setHomeResult(d)`。
- `setHomeResult(d)`（首页）/ `setSearchResult(d)`（搜索）：与 `setResult` 效果一致，app 自动识别回调类型。
- `setError(msg)`（缩写 `error`）：打印调试信息。
- `log(x)`：记录日志（支持字符串/对象/数组）。
- `toast('文本')`：消息提示。

列表项常用字段：`title` `desc` `img`(或 `pic_url`) `url` `col_type` `extra`。

## 2. 请求
- `fetch(url, options)`：同步返回字符串。options 支持 `headers`、`body`、`method`、`timeout`(ms)、`withHeaders`、`withStatusCode`、`redirect:false`、`toHex:true`、`onlyHeaders:true`、`inputStream:true`、`dns`。
- `post(url, {body:{...}})`：body 自动序列化。
- `fetchPC` / `postPC`：电脑端 UA 版本。
- `fetchCookie(url, options)`：返回 cookie 数组的 JSON 字符串。
- `request(url, opt)`：海阔同步请求（webview/子程序环境常用）。
- `batchFetch([{url,options}])`（缩写 `bf`）：多线程批量，>16 个自动分批，返回字符串数组。
- 编码：`fetch` 返回默认按 UTF-8 解码；非 UTF-8 需在 `content-type` 指定 charset。不要对已解码内容二次 `decodeStr`。

## 3. DOM 解析
- `parseDom(html, sel)`（缩写 `pd`）：取单个，默认自动补全域名/http。
- `parseDomForHtml(html, sel)`（缩写 `pdfh`）：取一个块，**不自动补全**。
- `parseDomForArray(html, sel)`（缩写 `pdfa`）：取列表，返回数组。
- `xpath(html, expr)` / `xpathArray(html, expr)`（缩写 `xpa`）。

## 4. 编解码 / 加密
- `base64Encode` / `base64Decode`
- `encodeStr(input,'GBK')` / `decodeStr(input,'UTF-8')`
- `aesEncode(key,input)` / `aesDecode(key,input)`（海阔 aesEncode 实测为 **AES/CTR**）
- `rsaEncrypt(data,key,options)` / `rsaDecrypt(...)`
- `rc4.encode/decode(s,key,'UTF-8')`
- `md5(x)`（也支持取文件 MD5）；`hexToBytes` / `hexToBase64`
- `eval(getCryptoJS())` 后可用 `CryptoJS.*`（高级）
- `window0.btoa/atob` 或 `with(window0){...}`

## 5. 变量 / 存储
- 全局变量（重启失效）：`putVar/getVar/clearVar`；`storage0.putVar/getVar` 支持 JSON。
- 规则内变量：`putMyVar/getMyVar/clearMyVar/listMyVarKeys`；`storage0.putMyVar/getMyVar` 支持 JSON。
- 私有存储（规则删则丢，更新不丢）：`setItem/getItem`；`storage0.setItem/getItem` 支持 JSON。
- 公开存储（跨规则、不随删除丢失）：`setPublicItem/getPublicItem/clearPublicItem`；`storage0.setPublicItem/getPublicItem`。
- 私有文件：`saveFile(name,content[,0])` / `readFile(name[,0])` / `deleteFile` / `fileExist`（自动加解密，路径 `Documents/rules/files/<规则名>/`）。
- 配置管理：`initConfig({...})` 写入，`config.xxx` 读取。

## 6. 域内变量
- `MY_URL`：当前请求地址；`MY_HOME`：主页地址（由 MY_URL 推出）；`getHome(url)`。
- `MY_RULE`：当前规则对象（`MY_RULE.title` / `MY_RULE.find_rule`）。
- `MY_PAGE`：当前页数（第一页为 1）。
- `MY_TYPE`：页面类型（首页 `home` / 搜索 `search`）。
- `MY_PARAMS`：上一级 `extra` 传来的参数对象。
- `MY_NAME`：应用名（海阔视界 / 嗅觉浏览器）。
- `MOBILE_UA` / `PC_UA`；`getParam('key','default')`；`getRule()`。
- `getAppVersion()`、`getSearchMode()` / `setSearchMode(1)`、`searchContains(text,key,false)`。

## 7. 页面 / 导航
- `refreshPage(false)`：刷新（false 不滚到顶部）。
- `back()` / `back(true)`：关页并刷新上一页（仅二级）。
- `setPageTitle(t)` / `getPageTitle()` / `setPagePicUrl()` / `setPageParams({})`。
- `setLastChapterRule(rule)`：动态设最新章节规则（支持 `js:` + `$.toString`）。
- `request('hiker://page/detail')`：取子页面定义（对象字符串）。
- `addListener('onRefresh'|'onClose', $.toString(()=>{}))`：页面生命周期。
- `showLoading/hideLoading` / `confirm({...})`。
- `updateItem/deleteItem/addItemAfter/addItemBefore/findItem/findItemsByCls`：动态刷新界面（extra 需全局唯一 id/cls）。
- 打开新窗口：`extra:{newWindow:true, windowId:...}`；隐藏到后台 `func://background`。

## 8. 媒体 / 文件
- `downloadFile(url, path[, headers])` / `requireDownload(url,path)`。
- `saveImage(urls,'hiker://files/1.png')`；`fileExist`。
- `cacheM3u8(url[,opt][,name])` / `batchCacheM3u8`（缩写 `bcm`）；`fixM3u8`。
- `clearM3u8Ad(url)` / `clearM3u8AdLazy(url)`；`cacheM3u8WithPngProxy` / `convertM3u8WithPngProxy`。
- `startProxyServer($.toString(()=>{...}))`：代理服务器（m3u8 需带 m3u8 字样）。
- `fetchCodeByWebView(url, {headers,blockRules,timeout,checkJs})`；链接前缀 `webview://`。
- `getIP()` / `ipping(ip,timeout)` / `findReachableIP([...])` / `registerDNS({...})`。
- `copy(text)`；`convertBase64Image(url)`；`getPath('hiker://files/a.txt')`。
- 定时任务：`registerTask(id,timeMs,codeStr)` / `unRegisterTask(id)`。
- 批量任务：`batchExecute(tasks, listener, successCount)`（缩写 `be`，最大 16 线程）；`syncExecute({func,param})`（线程同步）。
- 本规则/历史/样式：`getRuleCount()`（返回**字符串**）、`getLastRules(count)`（常用历史规则）、`getColTypes()`（返回所有可选首页样式**字符串数组**）、`publishRule(rule)`（提交到云仓库）。
- X5 刷新：`refreshX5WebView('http://1.com')`（刷新整个 X5 链接）、`refreshX5Desc('float&&255')`（只刷新高度等 desc，**不重载网页**）。
- 加密代码：`evalPrivateJS(code)` 直接运行加密串 / `getPrivateJS(code)` 生成加密代码（**参数与返回都是字符串**）。加密串在「设置→开发者模式」里导出。
  > ⚠️ 加密代码块里**不要引用非顶层作用域的变量或函数**（例如在箭头函数 `()=>{}` 里定义变量、又在加密块里直接引用该变量名）——把变量定义一起加密，或改用传参。
- Java 字节码（**高危险，必须征得用户授权**）：`requireDownload(dexUrl,'hiker://files/cache/t.dex')` → `loadJavaClass('hiker://files/cache/t.dex','com.test.code.TestCode')`；携带 so 时第三个参数传 `'hiker://cache/dir/a.so'`（单个）或目录 `'hiker://cache/dir'`（多个）。`getCpuAbi()` 取手机 ABI（`arm64-v8a`/`armeabi-v7a`）。
- 下拉选择框：`showSelectOptions({title:'选择性别', options:['选项一','选项二'], col:3, js:"'toast://你点击的是' + input"})`（`col` 列数默认 3）。
- ajax 风格链式：`http.fetch(...).success(...).start()`。
- 聚合搜索代理（**仅首页**）：`{col_type:'input', url:"'hiker://search?s='+input", extra:{rules:"fetch('hiker://files/rules.json')"}}`
  - `extra.rules` 必须是**一段 JS 代码**（不是规则地址、也不是规则数组），执行后返回一个**数组字符串**（如 `JSON.stringify(data)`）。App 自带的搜索解析规则用不了此功能。
- ⚠️ **下面两个网上流传、但在官方文档与 App 内置资源里都查不到，属未证实，暂不要用**：
  `globalMap0`（声称"全局任意类型 Map"）、`shareDirectory`（声称"分享目录"）。
  本库早期版本误将其当作官方 API 收录，**2026-09 复核后标注为未证实**；需要全局存储请用官方的 `setItem/getItem` / `putVar/getVar` / `putMyVar/getMyVar`。

## 9. 模块（$ 工具 / require）
- `$.require(path, importParam)`：加载子页面/本地/远程模块，返回其 `$.exports`；path 支持 `hiker://page/xxx`（可省略 `hiker://page/`）。
- `$.exports = {...}`：模块导出（必须定义）。
- `$.toString(func, arg1...)`：把函数转成立即执行字符串（用于 lazyRule/rule/input 等）。
- `$.stringify(obj)` / `$.type(x)` / `$.dateFormat(date, fmt)` / `$.log(fmt,...)` / `$.hiker`。
- `$(url).rule(func)` / `$(url).lazyRule(func)` / `$(url).x5Rule(func)` / `$(url).input(func)` / `$(url).confirm(func)` / `$(url).select(...)` / `$(url).b64()`。
- `$(url, selector).lazyRule((obj)=>{...}, paramObj)`：动态解析，`input`=响应，可传参。
- `require(remoteUrl, {headers}, version)` / `requirejs`（CommonJS）/ `requireCache(url,hours)`（缩写 `rc`）/ `fetchCache`（`fc`）/ `deleteCache`。
- 远程模块更新需改 `?v=1` 或版本号。

## 10. 云剪贴板 / 口令
- `getPastes()`：返回可用云剪贴板数组。
- `sharePaste(content, paste)`：分享，返回云剪贴板地址（paste 空则用第一个）。
- `parsePaste(url)`：解析云剪贴板内容。
- `fba.parsePaste(url)`（网页环境）。

## 11. 网页桥接（`fy_bridge_app`，可简写 `fba`；仅网页/网页插件环境）
- `fba.playVideo(url)` / `fba.playVideos(JSON字符串)`（动态解析需 `codeAndHeader:";get"` + `originalUrl`）。
- `fba.showPic(url)` / `fba.setWebTitle` / `fba.setWebUa` / `fba.setAppBarColor`。
- `fba.importRule(rule)`：导入口令。
- `request` / `requestAsync(url,param,cb)`（网页内同步/异步请求；`javascript:` 模式先 `eval(fba.getInternalJs())`）。
- `fba.getCookie(url)` / `fba.getVar/putVar/clearVar` / `fba.refreshPage`。
- `fba.open(JSON字符串)`：跳原生二级详情页。
- `fba.parseLazyRule(url)` / `fba.parseLazyRuleAsync(url, cbStr)`。
- `fba.getHeaderUrl(url)` / `getRequestHeaders(url)` / `fba.getUa()` / `fba.newPage(title,url)` / `fba.openThirdApp(url)`。
- `fx_bridge` 方法列表见官方 help_web_bridge。
