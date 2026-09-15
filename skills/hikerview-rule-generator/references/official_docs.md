# 官方文档地址与快照说明

## 在线文档
- 主页：<https://docs.189.tyrantg.com/>
- 常用规则：<https://docs.189.tyrantg.com/docs/hikerview/help_rules.html>
- JS 指南（内置 API）：<https://docs.189.tyrantg.com/docs/hikerview/help_js.html>
- 全部样式 col_type：<https://docs.189.tyrantg.com/docs/hikerview/help_col_type.html>
- 链接协议：<https://docs.189.tyrantg.com/docs/hikerview/help_link.html>
- `#标签#`：<https://docs.189.tyrantg.com/docs/hikerview/help_tag.html>
- 二级列表/动态解析：<https://docs.189.tyrantg.com/docs/hikerview/help_film_list_rules.html>
- 网页接口（fy_bridge_app）：<https://docs.189.tyrantg.com/docs/hikerview/help_web_bridge.html>
- 导入格式/口令：<https://docs.189.tyrantg.com/docs/hikerview/help_auto_import.html>
- 开放接口（投屏/WebDav/EPUB）：<https://docs.189.tyrantg.com/docs/hikerview/help_api.html>
- `$` 工具：<https://docs.189.tyrantg.com/docs/$/static_method.html>、`static_property.html`、`method.html`

## 源仓库（**首选**，比网页文档更全更稳）
官方文档的 Markdown 源在：<https://github.com/ReflectionLab/Documents>
（`docs/hikerview/*.md` 与 `docs/$/*.md`，共 12 篇 hikerview 文档 + 3 篇 `$` 工具文档）。
需要完整内容、防止网页改版、或要 grep 时，**直接克隆该仓库**：

```bash
git clone --depth 1 https://github.com/ReflectionLab/Documents.git
```

### 🔴 但官方文档 + 网页**都不是最全的**：App 内置资源才是权威
`help_*.md` 只是文档，**App 里还打包了一套更全的 `help_*.json`**，两者会不一致。已知差异：

| 主题 | 官方文档 | App 内置资源（更全） |
|------|---------|---------------------|
| `col_type` 样式 | 遗漏 `icon_3_fill`/`icon_3_round_fill`/`card_pic_3_center` | `app/src/main/assets/help_col_type.json` 收录 **48** 个 |
| 规则字段 | 无 `firstHeader`/`titleColor`/`proxy` | App 默认模板 `home.json` / `homeSubView.json` 里在用 |

**遇到争议时，权威顺序是：App 源码/内置资源 > 官方在线文档 > 第三方资料。**

App 源码：<https://github.com/qiusunshine/hikerView>（Java，757★）
```bash
git clone --depth 1 https://github.com/qiusunshine/hikerView.git   # 约 470MB，浅克隆
```
可查的关键位置：
- `app/src/main/assets/help_*.json` —— App 内置文档（**比在线文档全**）
- `app/src/main/assets/home.json` / `homeSubView.json` —— 默认首页规则模板
- `app/src/main/java/com/example/hikerview/constants/ArticleColTypeEnum.java` —— col_type 枚举
- `app/src/main/java/com/example/hikerview/service/parser/` —— 解析器（`HttpParser`/`JSEngine` 等）

## 本 skill 的蒸馏文件
以下文件已把官方文档按主题整理，日常生成规则看它们即可，省去翻长文档：
- `col_type.md` ← help_col_type（**已按 App 源码校准**）
- `url_tags.md` ← help_rules / help_link / help_tag（**已按 App 内置 help_tag.json 校准**）
- `js_api.md` ← help_js / $ 系列 / App 内置 help_js.json
- `link_protocols.md` ← help_link / help_auto_import / help_film_list_rules
- `selector_syntax.md` ← help_rules / help_film_list_rules
- `rule_format.md` / `rule_patterns.md` ← 真实规则逆向 + 官方字段说明
- `community_repos.md` ← GitHub 社区仓库索引 + 2070 条真实规则统计

> ⚠️ 官网与 App 都可能更新。若发现本 skill 与它们不一致，**以 App 为准**，并顺手更新这里的蒸馏文件。
> 未收录进 `help_tag.json` 的 `#标签#`（如 `#concat#`、`#memoryPage#`）**不要凭网上资料直接采用**。
