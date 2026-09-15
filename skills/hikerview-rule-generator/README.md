# 海阔视界规则生成器（hikerview-rule-generator）

根据一个网址，自动生成、校验并迭代海阔视界（Hiker View）的观看规则 `rule.json`；也支持生成聚阅子程序（`parse` 对象）。

## 能做什么

- **四类规则**：图片 / 视频 / 音频 / 杂类，套用现成模板快速起步。
- **先问清再动笔**：确认规则类型、有没有现成参照规则、用哪种架构写法（纯规则 / 聚阅 / Q模板 / 跨规则程序），把"写起来难不难、装起来麻不麻烦"讲清楚再让用户拍板。
- **本地先验证**：不用每次上手机，先在电脑上跑解析，确认"爬得对不对"；连 AES/CryptoJS 加密接口也能在 PC 端打真实接口验证。
- **支持加密/签名接口**：能从前端 JS 里逆出 AES 等加密逻辑，用 `eval(getCryptoJS())` 在规则里原地复刻（详见 `references/crypto_sign.md`）。
- **导入说明**：告诉用户该怎么装（直接粘 `rule.json` / 连包导入 / 云口令 / 先装底座）。
- **自动迭代**：按用户反馈定位修改，改前备份、改后升版本号。

## 目录结构

```
SKILL.md                     技能主流程（agent 先读这个）
README.md                    本文件
references/
  rule_format.md             字段规范、解析写法、详情取址、依赖打包
  rule_recipes.md            写法骨架速查（2070 条真实规则实测：四套骨架怎么选、API 使用率）
  rule_patterns.md           6 种真实架构写法与依赖识别
  col_type.md                全部布局样式（以 App 源码为准）
  community_repos.md         GitHub 社区仓库索引 + 真实语料统计数据
  url_tags.md                占位符、请求修饰符、#标签#、媒体扩展
  js_api.md                  JS 内置 API 速查
  link_protocols.md          hiker:// 等伪协议、子页面、导入口令
  selector_syntax.md         原生选择器语法
  crypto_sign.md             加密/签名接口实战（CryptoJS + AES + 加密图片）
  m3u8_playback.md           M3U8/HLS 播放、索引缓存与加载慢排查
  official_docs.md           官方文档地址与快照说明
  publish_to_git.md          推送到 Git 远端（PAT 生成、建仓、推送、免密）
assets/templates/
  video_rule.json            视频模板
  image_rule.json            图片模板
  audio_rule.json            音频模板
  misc_rule.json             杂类模板
  juyue_parse.js             聚阅子程序（parse 对象）模板
scripts/
  validate_rule.py           校验字段/依赖/ES5 语法
  test_rule.js               电脑上跑 find_rule/searchFind/detail_find_rule
  test_juyue.js              电脑上跑聚阅 parse 对象
  fetch_url.py               给测试桩做同步抓取（Node 调 Python）
  lib/mini_dom.js            轻量 DOM + 选择器引擎
```

## 环境要求

- Python 3（跑校验脚本与同步抓取）
- Node.js 16+（推荐 18+，跑测试桩）
- 无需安装任何第三方包

## 快速用法

```bash
# 1. 生成后先校验
python scripts/validate_rule.py rule.json

# 2. 电脑上验证列表解析（推荐先把页面存成本地 html）
node scripts/test_rule.js rule.json --rule find_rule --html 列表页.html --fyclass 1 --fypage 1

# 3. 验证聚阅子程序
node scripts/test_juyue.js parse.js --fn 主页
```

## 触发场景

用户提到"海阔视界规则/源"、"写个海阔小程序"、"聚阅子程序/接口"、"rule.json 报错/爬不到/放不了"等，即可使用本技能。

## 说明

参考文件内容来自海阔视界官方开发文档（<https://docs.189.tyrantg.com/>，源仓库 <https://github.com/ReflectionLab/Documents>）的结构化整理，以及真实可用规则的逆向经验。官网更新时以官网为准。
