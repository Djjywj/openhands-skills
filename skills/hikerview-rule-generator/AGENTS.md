# AGENTS.md

本文件是本仓库的长期记忆与工作约定，供后续会话快速上手。

## 仓库用途

维护「海阔视界规则生成器」技能，位于 `.agents/skills/hikerview-rule-generator/`。
技能根据一个网址，生成、校验、迭代海阔视界的 `rule.json`，也支持聚阅子程序（`parse` 对象）。

## 目录约定

- `SKILL.md`：技能主流程，agent 首先阅读。
- `README.md`：技能说明（技能目录规范要求必须有）。
- `references/`：按主题整理的参考资料（字段、架构、样式、标签、API、协议、选择器、官方文档地址）。
- `assets/templates/`：四类 `rule.json` 模板 + 聚阅 `parse` 模板。
- `scripts/`：`validate_rule.py`（校验）、`test_rule.js`（普通规则 PC 测试）、`test_juyue.js`（聚阅子程序 PC 测试）、`fetch_url.py`（同步抓取）、`lib/mini_dom.js`（轻量 DOM 引擎）。

## 常用命令

```bash
# 校验一条规则（也支持传目录）
python3 .agents/skills/hikerview-rule-generator/scripts/validate_rule.py path/to/rule.json

# 电脑上验证普通规则的解析
node .agents/skills/hikerview-rule-generator/scripts/test_rule.js path/to/rule.json \
     --rule find_rule --html page.html --fyclass 1 --fypage 1

# 电脑上验证聚阅子程序
node .agents/skills/hikerview-rule-generator/scripts/test_juyue.js path/to/parse.js --fn 主页
```

环境：Python 3 + Node.js 16+，无需第三方包。

## 关键事实

- 官方开发文档：<https://docs.189.tyrantg.com/>，源仓库 <https://github.com/ReflectionLab/Documents>。
  遇到技能未覆盖的字段/API，先查官方文档，再回填到 `references/`。
- 海阔规则内的 `js:` 只支持 ES5（`var`/`function`/普通 `for`）；聚阅 `parse` 子程序运行时支持 ES6。`validate_rule.py` 与 `test_rule.js` 都会做 ES5 告警。
- 规则依赖分四类，导入方式不同：无依赖 / 库打包（连包） / 跨规则程序（按标题装底座） / 框架型（聚阅云口令）。`validate_rule.py` 会自动识别并给配套要求。
- PC 测试桩不支持 `$.require`、`hiker://` 伪协议、`startProxyServer` 等平台能力，遇到会明确报错，不要误判为解析失败。
  但**已支持 CryptoJS**：`scripts/test_rule.js` 内置 `getCryptoJS()` 垫片（Node `crypto` 还原 AES 的 CBC/ECB/Pkcs7），含 AES 加密接口的规则可在 PC 端打真实接口验证；`--vid` 喂详情参数。用法见 `references/crypto_sign.md`。
- `scripts/test_rule.js` 支持 `--vid <id>`，并把 `--fyclass/--fypage/--kw` 同时映射到规则里的 `getParam('t'/'p'/'k')` 别名。
- `scripts/test_rule.js` 的 `--url` 会同时作为 `MY_URL`（真机当前页地址），并把 URL 里的中文 `？？` 还原成 `?`，便于测 POST 详情页传参。
- 仓库还装有通用图像技能：`.agents/skills/see-images/`（读图：`scripts/look.py` 调视觉模型；长截图/全景图用 `scripts/slice_image.py` 切片，依赖 Pillow）与 `.agents/skills/image-processing/`（裁剪/缩放/格式转换/传统 CV 指引）。

## 已完成产出

- `output/4e63v.rule.json`：含羞草研究所（4e63v.com）视频源，纯规则自带脚本（无外部依赖）。
  加密链路：AES-256-CBC 请求体 + 服务端时间戳 `ents` 防重放；封面 AES-128-ECB 解密成 data URI；`/videos/getList` 列表、`/base/globalSearch` 搜索、`/videos/getInfo` + `/videos/getPreUrl` 取 m3u8。
  **解锁完整版（关键）**：`getPreUrl` 返回的是试看片段 `?start=600&end=630`（仅 30 秒），
  删掉 `start`/`end` 参数、保留 `sign` 即可播放完整全片（实测同一视频 30 秒 → 1501 秒）。此即油猴「免费看」脚本原理（脚本 146–183 行）。
  性能：一页封面用 `batchFetch` 并发取密文再统一解密，避免逐张串行 `fetch` 卡顿。
  **详情传参（关键）**：列表项 url 是 POST 请求，参数分隔符必须写中文 `？？`（写成英文 `?` 会截断 `;post;`，
  vid 传不进去 → 接口“缺少参数” → App 报「链接为空，规则有误」）；规则内 `getVid()` 按
  `getParam('vid')` → `MY_URL.match(/[?？&]vid=(\d+)/)` → `MY_PARAMS.vid` 三重兜底取 id。
  以上均已在 PC 端打真实接口验证通过（列表 11 / 搜索 20 / 详情 3，详情可播完整全片）。
  **起播优化**：详情直接返回 **media 分表地址**（master 只有一跳且浏览器验证秒开），并保留原始总表作备用线路；
  手机浏览器实测秒开而海阔内慢，属海阔播放器/设置侧问题（详见 references/m3u8_playback.md §5.1）。
  **播放慢的结论（勿重复排查）**：视频 CDN `t02h.beikept.com`（gccdn，3 个电信 IP）实测 ~1MB/s、
  无限速、无“只能访问一次”、签名长期有效；站点只有单档 720p/1Mbps（无低码率目录）。
  故“加载很慢（十几K/s）”是**手机↔CDN 的网络/代理问题或播放器问题，规则改不了带宽**。
  规则侧可选手段见 `references/m3u8_playback.md`（`cacheM3u8` 缓存索引、`registerDNS` 优选节点等）。
  站点 API 有备用线路 `a37p.oqd79.com` / `a69f.v84ik.com`（前端 JS `VUE_APP_API_BASE_URL`），
  仅影响接口、不影响视频 CDN；`/videos/v2/getUrl` 为付费完整版接口（返回 2002），不可当免费直链。
  **列表加速（关键）**：封面是 AES-128-ECB 加密的，若把解密后的 `data:` URI 内嵌进列表，
  一页 11 张约 **438KB**，海阔要解析巨大 JSON + 逐张解码 base64，且无法懒加载（下拉翻页更明显）。
  v5 起解密后用 `writeHexFile` 写成本地图片文件，列表 `img` 只传 `getPath()` 的 `file://` 短路径：
  **列表数据 438KB → 4.7KB（约 90 倍）**，图片可懒加载、可复用（二次进入/返回秒开）。
  文件 API 不可用时自动退回 `data:` URI（不会显示不出来）。缓存不清理，可删 `hiker://files/cache/4e63v_*.jpg`。
  **封面比例（v9 修复「图片太宽显示不全」）**：站点横版封面是 **800×450（16:9）**，塞进 `movie_3`
  三列卡片（竖格）会被裁掉两边 → 看着「太宽、显示不全」。接口另有 `coverImgUrlVertical`
  （500×720 / 540×720 竖图），正合三列卡片。v9 起列表与搜索一律优先用竖版
  （`it.coverImgUrlVertical || it.coverImgUrl`）；详情大图改用 `pic_1_full`（满宽、高按比例自适应），
  让 16:9 横版封面完整显示（不再用会固定高度裁切的 `pic_1`）。实测解密后尺寸：竖版 375–540×536–720。
  **分类（v6 修复）**：分类来自 `/videos/getType`（顶级 5 个：4=国产、11=主播、17=日韩、23=欧美、29=动漫，
  全部=0）。`getList` 的分类参数是 `typeIds`（数组）。注意 `typeIds:[4]` 与「全部」在首页前 33 条完全重合，
  是**因为站点最新内容恰好都是国产**，接口并没有忽略筛选（用子分类 5 或 11/29 可区分）。
  坑：若海阔传入的是分类**名字**而非 id，`parseInt('国产')` 得 NaN，会让所有分类都退化成「全部」。
  v6 起 `resolveType()` 同时兼容数字 id 与分类名；v7 起 `pickClass()` 依次尝试
  `getParam('t')` / `MY_URL` / `MY_PARAMS` 三个来源，并**跳过仍是占位符（`fyclass`）的来源**，
  取第一个可信值（含 `decodeURIComponent`，兼容 URL 编码的中文名）。
  **根因（真机 v8 定位，必看）**：分类传参失效**不是**取值逻辑问题，而是规则 `url` 用了
  `;post;`。海阔请求 POST 规则时会在第一个**半角** `?` 处切开、把 query 当 POST body
  （源码 `HttpParser.post()` 的 `onSuccess(finalUrl)`，`finalUrl = ss[0]` 已去掉 query），
  于是 JS 里 `MY_URL` 只剩 `https://.../base/getTimeStamp`，`getParam('t')` 恒为空 →
  `typeIds:[]` → 永远返回「全部」。真机调试规则实拍到：`1 T=[] C=0 P=1 TYPE=home`、
  `3 url=https://a37p.oqd79.com/base/getTimeStamp`（无 query）。
  修法（v8）：该 url 改用 **GET**（`;get;UTF-8;{...}`）；或仍用 POST 但把 `？`/`&` 写成全角
  `？？`/`＆＆`（海阔先按半角切分、后 `decodeConflictStr` 还原）。详情页原就用 `？？`+post，故一直正常。
  `scripts/test_rule.js` 已忠实模拟该顺序，本地即可复现/回归。
  真机若再遇「标签都在、点分类内容不变」，先跑 `output/4e63v.debug.rule.json`
  （调试规则，列表项标题直接显示：`T=[getParam('t')] C=解析出的分类 P=页 TYPE`、
  `FY=[getParam('fyclass')]`、`url`、`send=实际发送typeIds`、`got=条数+首条`；
  海阔列表只渲染 `title`，所以值必须放在 title，放 `desc` 会被吞）。
  读法：`T=[17] C=17` 正常；若 `T=[]` 且 url 无 query，即命中上面的 POST 坑。

  **源码结论**（github qiusunshine/hikerView）：
  - `JSEngine.getParam(key,default,urlKey)`：`urlKey` 参数默认 `= MY_URL`（注解生成代码
    `param[i] = param[i] || MY_URL`），所以 `getParam('t','')` 读的是当前页 URL 的 query；
    `HttpParser.getParamsByUrl` 先按 `;` 截断（去掉 `;post;...` 请求选项），再按 `?` & `&` 切。
  - `CommonParser.parsePageClassUrl`：请求前 `url.replace("fyclass", articleListRule.getClass_url())`，
    即 `fyclass` 会被换成当前选中分类的 `class_url`。`ArticleListFragment.onClassClick`
    在点分类时 `setClass_url(url); setFirstHeader("class")`。

## 维护约定

- 改技能内容时，同步更新 `SKILL.md` 的「资料索引」与 `official_docs.md` 快照说明。
- 改测试脚本后，用 `assets/templates/*.json` + 一段假 HTML 自测通过再提交。
- 新增规则形态/坑时，追加到 `references/` 对应文件，并让 `validate_rule.py` 的 `detect_dependencies()` 能识别。
- 提交信息使用简体中文，并附 `Co-authored-by: openhands <openhands@all-hands.dev>`。

## Git 远端

- 远端（私有）：`https://github.com/Djjywj/hikerview-rule-generator`，默认分支 `master`。
- `origin` 已配置；本机用 git 凭据存储（`~/.git-credentials`，权限 600）实现免密 `git push`。
- 该凭据来自一个 classic PAT（仅 `repo` 权限，30 天有效期）；过期后需重新生成并更新 `~/.git-credentials`。
