# M3U8 / HLS 播放、缓存与加速（官方 help_link / help_js / help_tag 蒸馏）

> 规则给出播放地址后，**缓冲快慢主要取决于「手机 ↔ 视频 CDN」的实际带宽**，规则本身改不了带宽。
> 遇到“加载很慢”，先做**源站测速**判断瓶颈在哪，再决定是否需要缓存 / DNS 优选 / 代理；
> **不要**在没测速的情况下臆测是规则问题。

## 1. HLS 三层结构（排错必看）

```
master playlist  （#EXT-X-STREAM-INF + 变体相对路径，可含 ?sign=...）
   └─ media playlist  （#EXTINF + 分片相对路径；可含 #EXT-X-KEY:AES-128）
         └─ xxx.ts 分片（真正占带宽的部分）
```

- **master 很小（几百字节），分片才大**（几秒一段，常见 100~250KB）。慢是慢在分片下载。
- `#EXT-X-KEY:METHOD=AES-128,URI="key.key"` = 分片加密，播放器要再取 16 字节 `key.key` 解密；
  这是标准 HLS，**多数播放器支持**；若个别播放器不支持，会一直转圈/失败。
- 变体/分片是**相对路径**，由播放器按 base 解析。若播放器解析异常，可让规则**直接返回媒体列表**（见 §5）规避。

## 2. 播放地址的强制识别

| 需求 | 写法 |
|---|---|
| 视频直链 | 末尾加 `#isVideo=true#` |
| 链接里没有 `.m3u8` 字样 | 加 `#m3u8` 或 `#isM3u8#`（后者还会**忽略 content-type 校验**） |
| 不想被当 m3u8 | `#ignoreM3u8#` |

## 3. 索引缓存（针对“地址只能访问一次”）

```js
var a = cacheM3u8('http://xx.m3u8');                    // -> file:///.../video.m3u8##http://xx.m3u8
var b = cacheM3u8('http://xx.m3u8', {headers:{}});      // 支持 headers，用法同 fetch
var c = cacheM3u8('http://xx.m3u8', {}, 'video.m3u8');  // 第 2 参必传（无值给 {}）
var d = batchCacheM3u8([{url:'http://a.cn', options:{headers:{},body:'a=1',method:'POST'}}, {url:'http://b.cn'}]); // 缩写 bcm
```

- **用途**：某些 m3u8 地址只能访问一次，播到一半会断；缓存索引后本地读取，避免二次请求失败。
- 返回串里的 `##原始地址` 用于让播放器把**分片仍按原始地址**解析，别自己拆掉。
- `video://` 链接也可：`{url:'video://https://xxx.html', extra:{cacheM3u8:true}}`。
- 相关：`fixM3u8(url, 内容)` 把 `#EXT-X-KEY`/`xxx.ts` 相对路径补成绝对；
  `clearM3u8Ad(url)` / `clearM3u8AdLazy(url)` 清 `#EXT-X-DISCONTINUITY` 疑似广告段。

## 4. PNG 分段 / 本地代理

- `cacheM3u8WithPngProxy(url, options, fileName)` / `convertM3u8WithPngProxy(content, {headers:{}})`
  用于**分片被伪装成 image/png** 的站：软件起本地代理，把 png 转回 ts。
- `startProxyServer($.toString(()=>{ ... return 内容 }))`：本地代理，**Content-Type 固定 `application/vnd.apple.mpegurl`**。
  - 传给播放器时**必须加唯一参数**（否则地址不唯一会被复用）；
  - 代理代码里用 `MY_PARAMS` 取参数；可返回 `{body, headers, statusCode}` 扩展。
  - 适合：给分片/索引**补请求头**、改写分片地址、做二次处理。

## 5. 慢加载排查套路（本 skill 实战总结）

1. **先测源站**（在规则生成环境/另一网络，用 `curl` 直接拉）：
   - `master`/`media`/`key.key`/前几个 `.ts` 的 `HTTP 码、字节数、耗时、速率`；
   - 连续拉 30+ 次看**是否限速、是否“只能访问一次”**；对比**带/不带 Referer/UA**；换 CDN 的多个 IP 分别测。
2. **区分瓶颈**：源站快 → 瓶颈在“手机↔CDN”或播放器；源站慢/限速 → 才考虑缓存/代理/换线路。
3. **规则侧能做的**（都**不增加带宽**）：
   - 直接返回 **media playlist**（跳过 master 一次往返，且规避相对路径解析问题）；
   - `cacheM3u8` 缓存索引（防“只能访问一次”中断）；
   - `registerDNS({'.域名':'IP1 IP2' | 'https://dns.alidns.com/dns-query'})` 优选节点
     （**首次需用户授权**；配合 `findReachableIP([...])` / `ipping(ip, ms)` 找可用节点）；
   - `startProxyServer` 改写/加头（慎用，代理本身也可能成为开销）。
4. **规则改不了带宽**：若视频只有单档高码率、且手机到该 CDN 只有几十 KB/s，任何写法都救不了——
   如实告知用户（换网络 / 关代理 / 换 DNS / 用缓存下载），不要制造“改规则就能变快”的假象。

### 5.1 决定性对照：手机浏览器 vs App 内播放

**让用户用手机浏览器直接打开播放地址**（media 分表或分片直链）：

| 表现 | 结论 | 规则侧对策 |
|---|---|---|
| 浏览器也慢 | 手机↔CDN 带宽/代理/DNS 问题 | 规则无解；建议关代理、换网络、换 DNS |
| **浏览器秒开、App 内慢** | **App 播放器内核 / 设置问题** | 见下 |

“浏览器快、App 慢”时，规则可试的：
- **直接返回 media 分表地址**（跳过 master，匹配浏览器验证过的形态）：
  `fetch(master)` → 取第一条非 `#` 行 → 相对路径用 `master 目录 + 行` 拼绝对，再 `#isVideo=true#`。
- 给地址加 `#m3u8#` / `#isM3u8#` 强制按 m3u8 识别、忽略 content-type 校验。
- `cacheM3u8` 缓存索引（防止“只能访问一次”导致的反复重取）。
- 让用户检查 App 侧：**播放器内核（EXO/ijk/系统）切换、解码方式（硬/软解）、
  是否开了“自动去广告/缓存 m3u8”、是否有全局代理/VPN、DNS**。
- 让用户长按复制播放地址，用**外部播放器**（MX/VLC）试：外部也快 → 坐实海阔播放器问题。

## 6. 常见站点形态：API 多线路（备用域名）

部分站点前端把 API 域名写成数组并做“**检测到访问速度慢，是否切换到新线路？**”的兜底，例如
`VUE_APP_API_BASE_URL:"https://a.oqd79.com,https://b.v84ik.com"`。
- 取架构时**grep 前端 JS** 找 `VUE_APP_API_BASE_URL` / `apiBaseUrlList` / `getPreUrl` / `v2/getUrl` 这类线索。
- `v2/getUrl` 之类的“完整版”接口常需登录/购买（返回 2002 之类），**不要**当作免费直链用。
- 备用域名只影响**接口**（列表/详情），**不影响视频 CDN**；换线路不等于播放变快。
