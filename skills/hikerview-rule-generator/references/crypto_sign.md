# 加密 / 签名接口实战（CryptoJS + AES）

有些站点（尤其 Vue SPA 的私有接口）不在页面里出数据，而是把请求参数/响应体做 AES 加密、再带签名头。
这类站点**纯规则也能做**，思路是：先把前端 JS 的加密逻辑逆出来，再在 `find_rule` / `detail_find_rule` 里用 `eval(getCryptoJS())` 原地复刻。

> 适用：接口需要 `AES(参数)` 作为 body、`AES(时间戳)` 防重放、或封面图是 `.aes` 加密文件。
> 先在浏览器把 JS 扒下来（F12 → Sources，或直接下 `assets/*.js`），再按下面的套路定位。

## 1. 从前端 JS 里挖三样东西

1. **接口域名与路径**：搜 `baseURL`、`getTimeStamp`、`/videos/`、`/home/` 等明文；接口名常被 String 表混淆，可用 Node 脚本还原（见 §5）。
2. **加密方式与密钥**：搜 `CryptoJS`、`AES`、`encrypt`、`decrypt`、`mode`、`padding`、`Utf8.parse`。
   真实案例里密钥就明文写在配置对象里，例如：
   `'VITE_APP_AES_KEY': 'B77A9FF7F323B5404902102257503C2F'`、`'VITE_APP_AES_IV': 'B77A9FF7F323B5404902102257503C2F'`。
3. **签名/防重放头**：搜 `headers`、`Auth`、`Did`、`timestamp`。常见形如
   `headers: {Auth: token || 'null', Did: '1'}`，body 里再塞一个加密时间戳（本站是 `ents`）。

## 2. 在规则里复刻（ES5 + CryptoJS）

```js
eval(getCryptoJS());
var AKEY = 'B77A9FF7F323B5404902102257503C2F'; // 32 字节 -> AES-256
var IV   = AKEY.substr(0, 16);                  // 16 字节
function aesEnc(s) {
  return CryptoJS.AES.encrypt(
    CryptoJS.enc.Utf8.parse(s),
    CryptoJS.enc.Utf8.parse(AKEY),
    { iv: CryptoJS.enc.Utf8.parse(IV), mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }
  ).toString();                                  // 输出 base64 密文
}
```

时间戳要**用服务端的**：很多签名接口会校验时间窗口，客户端本地时区/时间不可靠。
先请求一个公开的时间接口，再用它构造：

```js
var ts = JSON.parse(fetch(BASE + '/base/getTimeStamp', {method:'POST', headers:HDR, body:'{}'})).data.timeStamp;
var body = JSON.stringify({ endata: aesEnc(JSON.stringify(params)), ents: aesEnc(String(ts)) });
var res  = fetch(BASE + '/videos/getList', {method:'POST', headers:HDR, body:body, timeout:15000});
```

> 💡 把「返回时间戳的接口」直接当作规则 `url`：`...getTimeStamp?t=fyclass&p=fypage;post;UTF-8;{Content-Type@application/json&&Did@1&&Auth@null}`
> 这样 `find_rule` 里 `JSON.parse(getResCode()).data.timeStamp` 就能白拿时间戳，省一次请求。

### 关键坑
- **海阔自带 `aesEncode/aesDecode` 实测是 AES/CTR，和 CryptoJS 的 CBC 不通用**；要精确复刻必须 `eval(getCryptoJS())`。
- **URL 参数名不要和占位符同名**：写 `?t=fyclass&p=fypage`，不要写 `?fyclass=fyclass`——占位符是整体替换，同名会把参数名也替掉。
- **`fetch` 是同步的**，可以在 `find_rule` 里连续请求：拿时间戳 → 加密 → 请求列表。
- 密钥长度决定 AES-128/192/256（16/24/32 字节），别硬编码成固定 128。

## 3. 加密图片（`.aes` 封面）也能还原

前端常见写法：`img` 的 `src` 以 `.aes` 结尾时，先带 `Did` 头 GET 密文，再客户端解密。
案例里图片是 **AES-ECB**（注意：和请求体的 CBC 不同！），解密结果本身就是一个 `data:image/jpeg;base64,...` 字符串：

```js
function decImg(u) {
  try {
    if (!u || String(u).indexOf('.aes') < 0) return u;
    var c = fetch(u, { headers: { Did: '1' }, timeout: 8000 });
    var s = CryptoJS.AES.decrypt(c, CryptoJS.enc.Utf8.parse('46cc793c53dc451b'),
             { mode: CryptoJS.mode.ECB, padding: CryptoJS.pad.Pkcs7 }).toString(CryptoJS.enc.Utf8);
    return (s && s.indexOf('data:image') === 0) ? s : u;
  } catch (e) { return u; }
}
```

- 图片密钥常和接口密钥**不是同一个**，要分别从 `Ze()` 之类解密函数里找。
- 解密得到 `data:` URI 可直接塞进列表项 `img`（真机渲染表现需实测；失败时 `catch` 回退原地址即可保底）。
- **别逐张同步解密**：一页 10+ 张封面串行 `fetch` 会明显卡顿。先用 `batchFetch([{url,options},...])` 并发取回全部密文，再统一解密，速度提升明显（真机 `batchFetch` 为多线程，最多 16 并发）。

## 4. 定位加密细节的土办法

1. 在 JS 里找解密函数，看它引用的 `mode`/`pad`/`parse` 字符串索引；
2. 用 §5 的解码脚本把索引还原成明文（`ECB`/`CBC`/`Utf8`/`Pkcs7`）；
3. 用 Node 的 `crypto` 试解一次密文（ECB 无 IV；CBC 试 IV=0、IV=密钥前 16 字节等），看明文是不是 `data:image/...` 或合法 JSON，就能确认 mode/IV。

## 5. 还原被混淆的 String 表（Node 片段）

Webpack/Vite 打包常见：字符串存在数组里，用 `_0xabc(0x12)` 取。把 chunk 里的数组函数、解码函数、旋转函数三段用 `new Function` 拼起来即可导出全部明文：

```js
// 关键：三段代码 + 一次自动旋转，然后 module.exports = 解码函数
const module_ = { exports: null };
new Function('module', arrSrc + '\n' + decSrc + '\n' + rotSrc + '\nmodule.exports=' + decodeName + ';')(module_);
const dec = module_.exports;
for (let i = 0; i < 4000; i++) { try { console.log('0x' + i.toString(16), dec(i)); } catch (e) {} }
```

- `arrSrc = function <数组名>(){...}`，`decSrc = function <解码名>(a,b){...}`，`rotSrc` 是紧随其后的 IIFE 旋转段。
- 解码器可能对每个索引都有效（不只数组长度），所以循环上限放宽到 4000，能多挖出后面追加的字符串。
- 本仓库工作流里 `/tmp/dump_strings.js` 即此用途的成品脚本。

## 6. PC 端怎么验证

`scripts/test_rule.js` 内置了 `getCryptoJS()` 垫片（用 Node `crypto` 还原 `CryptoJS.enc.Utf8` + `AES` 的 CBC/ECB/Pkcs7），
所以**含 AES 的规则也能在电脑上打真实接口验证**：

```bash
# 1) 先取一份「时间戳接口」的真实响应当 getResCode()（规则里会解析它拿 ts）
curl -s -X POST 'https://接口/base/getTimeStamp' \
     -H 'Content-Type: application/json' -H 'Did: 1' -H 'Auth: null' -d '{}' -o ts.json

# 2) 跑列表 / 搜索 / 详情
node scripts/test_rule.js rule.json --rule find_rule        --html ts.json --fyclass 4 --fypage 1
node scripts/test_rule.js rule.json --rule searchFind       --html ts.json --kw 日本
node scripts/test_rule.js rule.json --rule detail_find_rule --html ts.json --vid 77601
```

- 规则里 `getParam('t')` / `getParam('p')` / `getParam('k')` / `getParam('vid')` 分别用 `--fyclass` / `--fypage` / `--kw` / `--vid` 喂值。
- 桩的 `fetch()` 走 `scripts/fetch_url.py`，**真的会发 POST、带自定义头**，所以能端到端验证。
- 垫片只覆盖规则常用的 AES + `enc.Utf8` + `mode.CBC/ECB` + `pad.Pkcs7`；`aesEncode/aesDecode`（海阔版 AES/CTR）与 RSA 仍报"请真机测"。

## 7. 解锁「试看片段 / 需要会员」（删掉 start/end）

很多成人站/短剧站的播放接口会返回**带试看区间的地址**，形如：
`.../v.m3u8?start=600&end=630&sign=...&rSign=...` —— 只给中间 30 秒，前端就提示开通会员。
实测**把 `start`、`end` 两个参数删掉、保留同一 `sign` 签名**，即可直接播放完整全片（同一密钥签名通用）。
油猴「免费看」脚本的原理就是这一段：

```js
let splited = m3u8Url.split("?");
let p = new URLSearchParams(splited[1]);
p.delete("start");
p.delete("end");
return splited[0] + "?" + p.toString();   // 只留 sign/rSign
```

规则里用纯 ES5 复刻（不要用正则删，多层转义容易出错）：

```js
function stripTrial(u){
  var i=String(u).indexOf('?'); if(i<0) return u;
  var base=String(u).slice(0,i), parts=String(u).slice(i+1).split('&'), keep=[];
  for(var k=0;k<parts.length;k++){
    if(parts[k] && parts[k].indexOf('start=')!==0 && parts[k].indexOf('end=')!==0) keep.push(parts[k]);
  }
  return keep.length ? (base+'?'+keep.join('&')) : base;
}
```

验证方法：分别对「原地址」和「去 start/end 地址」数 `#EXTINF` 总时长。
真实案例里同一个视频原地址=30 秒、去掉后=1501 秒（501 段），差异一目了然。

> 另有接口 `/videos/v2/getUrl` 直接返回不带 start/end 的地址，但**部分视频返回 `2002 无权限获取`**，所以以「`getPreUrl` + 删 start/end」为主，`v2/getUrl` 仅作兜底尝试。

## 8. 实战样例

`output/4e63v.rule.json`（含羞草研究所 4e63v.com）就是按本文套路做的：
AES-256-CBC 加密请求体 + 服务端时间戳防重放 + AES-128-ECB 解密封面，列表/搜索/详情取 m3u8 全部在 PC 端打通。

## 9. 加密封面拖慢列表：落地文件 + 懒加载

**症状**：列表/分类能出图，但加载慢，**越下拉翻页越明显**。

**原因**：站点的封面是加密的（如 `xxx.aes`，明文走 AES 解出 `data:image/jpeg;base64,...`）。
若把 `data:` URI 直接塞进列表项 `img`，一页 11 张就要在规则数据里内嵌约 **438 KB** 的 base64，
海阔既要解析巨大的 JSON，又要逐张解码 base64；而且必须**全部下载+解密完**才能返回列表，
图片无法懒加载、无法复用，翻页（新封面）自然更慢。

**做法**：解密后把图片**写成本地文件**，列表只传 `file://` 路径（数据体积可降 ~90 倍）：

```js
var COVER_CACHE = true;
function coverPath(u){                       // 用密文文件名(32位hash)当缓存名，天然去重
  var m = String(u).match(/([0-9a-fA-F]{32})\.aes/);
  return 'hiker://files/cache/hx_' + (m ? m[1].toLowerCase() : 'h' + hstr(u)) + '.jpg';
}
// 命中缓存：fileExist -> getPath 直接用
// 未命中：batchFetch 并发取密文 -> AES 解密 -> base64 转 hex -> writeHexFile 写二进制 -> getPath
var b64 = plain.slice(plain.indexOf(',') + 1).replace(/\s+/g, '');
var hex = CryptoJS.enc.Base64.parse(b64).toString(CryptoJS.enc.Hex);
writeHexFile(coverPath(u), hex);
return getPath(coverPath(u));                 // 列表 img 用这个 file:// 地址
```

要点与避坑：
- **二进制写入必须用 `writeHexFile`**（`writeFile` 写的是文本，存 base64 文本不是图片）。
  `CryptoJS.enc.Base64.parse(...).toString(CryptoJS.enc.Hex)` 正好把 base64 转成 hex。
- `writeHexFile('hiker://files/cache/xxx.jpg', hex)`、`fileExist`、`getPath` 三个 API 配套使用；
  不能把绝对路径写死为 `file:///storage/...`（分身/多用户会失效），一律走 `getPath`。
- **必须 try/catch 兜底**：若设备不支持这些文件 API，就退回原来的 `data:` URI，保证图片照常显示。
- 好处：列表 JSON 只剩短路径（可懒加载、可复用、可被海阔图片缓存），二次进入/返回上一页**秒开**。
- 注意缓存只增不减，长期使用可定期清理 `hiker://files/cache/` 下对应前缀的 jpg（本规则为 `4e63v_*.jpg`）。

**测法（PC 桩）**：`scripts/test_rule.js` 已内置 `fileExist/getPath/writeHexFile/writeFile/saveImage`
垫片，会把 `hiker://files/` 映射到系统临时目录。跑一次 `find_rule` 后：
- 列表 `img` 应是 `file://.../hx_<hash>.jpg`；
- 临时目录里出现 11 个文件，且前 3 字节为 `ff d8 ff`（合法 JPEG）；
- 再跑一次，文件 mtime 不变 → 说明命中缓存、没有重新下载解密。

### 9.1 其它可选的图片加载方案（按风险从低到高）

1. **本地文件 + 懒加载**（本文方案，风险低，推荐）。
2. **官方「图片解密」`@js=`**：`img: '密文地址@js=' + $.toString(()=>{...})`，
   海阔下载密文后把 `input`（InputStream）交给这段 JS，返回解密后的 InputStream，
   由播放器/图片管线懒加载。属于官方设计用途，但需要在图片 JS 上下文里用 Java 字节流
   做 AES（示例见官方 `示例/imageDecode.js`：`JavaImporter` + `FileUtil.toBytes/toInputStream`），
   **该上下文没有规则环境**，复杂且易错，未在真机验证前不要贸然替换。
3. 内嵌 `data:` URI（最稳但最慢，仅在文件 API 不可用时兜底）。
