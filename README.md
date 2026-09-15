# OpenHands Skills

个人技能仓库，存放可复用的 OpenHands 技能。

## 目录结构

```
skills/
  <skill-name>/
    SKILL.md          # 目录式技能：启动时只加载「名字 + 描述」，用到时才读取全文
  <skill-name>.md     # 顶层式技能：每次对话完整加载（常驻规则类）
```

把 `skills/` 下的内容整体复制到本机 `~/.openhands/skills/` 即可启用全部技能。

## 技能列表

### Superpowers 技能集

移植自 [obra/superpowers](https://github.com/obra/superpowers)（v6.3.0），工具名已翻译为 OpenHands 版本。
入口是常驻引导 [superpowers.md](skills/superpowers.md)。

| 技能 | 说明 |
|------|------|
| [superpowers](skills/superpowers.md) | 超级技能集常驻引导：每次对话自动加载，决定何时用哪个技能 |
| [using-superpowers](skills/using-superpowers/SKILL.md) | 技能系统本身的使用方法（含 OpenHands 工具映射） |
| [brainstorming](skills/brainstorming/SKILL.md) | 做新功能/改行为前，先问清需求、给设计、等确认 |
| [writing-plans](skills/writing-plans/SKILL.md) | 把需求拆成多步实现计划 |
| [executing-plans](skills/executing-plans/SKILL.md) | 按计划执行，带评审检查点 |
| [subagent-driven-development](skills/subagent-driven-development/SKILL.md) | 在当前会话里用子代理执行独立任务 |
| [dispatching-parallel-agents](skills/dispatching-parallel-agents/SKILL.md) | 并行派发多个互不相关的任务 |
| [test-driven-development](skills/test-driven-development/SKILL.md) | 先写会失败的测试，再写实现 |
| [systematic-debugging](skills/systematic-debugging/SKILL.md) | 遇到 bug 先找根因，禁止瞎猜乱改 |
| [verification-before-completion](skills/verification-before-completion/SKILL.md) | 说「做完了」之前先跑验证、拿证据 |
| [requesting-code-review](skills/requesting-code-review/SKILL.md) | 完工/合并前请人审查代码 |
| [receiving-code-review](skills/receiving-code-review/SKILL.md) | 收到审查意见后严谨评估、不盲从 |
| [using-git-worktrees](skills/using-git-worktrees/SKILL.md) | 用独立工作区/分支隔离开发 |
| [finishing-a-development-branch](skills/finishing-a-development-branch/SKILL.md) | 收尾、合并、提 PR |
| [writing-skills](skills/writing-skills/SKILL.md) | 新建或修改技能 |

### 个人常驻规则

| 技能 | 说明 |
|------|------|
| [默认助手](skills/默认助手.md) | 全程简体中文、面向电脑小白的交流规则 |
| [自动识别图片](skills/自动识别图片.md) | 每轮自动检查消息里的图片并静默处理 |
| [每周自我复盘](skills/每周自我复盘.md) | 每周自动复盘：采集活动 → 提炼经验 → 更新技能 |

### 其他技能

| 技能 | 说明 |
|------|------|
| [github-gem-seeker](skills/github-gem-seeker/SKILL.md) | GitHub 寻宝器：优先复用成熟开源项目，而不是从零写代码。适用于格式转换、媒体下载、文件处理、网页抓取/存档、自动化脚本、CLI 工具等通用问题。 |
| [web-design-engineer](skills/web-design-engineer/SKILL.md) | 网页设计工程师：用 HTML/CSS/JavaScript/React 构建或重设计精致的可视化网页产物（页面、仪表盘、原型、幻灯片、动画、UI 稿、数据可视化），含设计评审与浏览器验收。来源：[ConardLi/garden-skills](https://github.com/ConardLi/garden-skills) |
| [agent-reach](skills/agent-reach/SKILL.md) | 互联网能力路由器：统一访问 15 个平台的调研/搜索能力（小红书、推特、B站、Reddit、YouTube、GitHub、V2EX、雪球、RSS 等）。来源：[Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) |
| [scrapling](skills/scrapling/SKILL.md) | 网页抓取：用 scrapling 自动选择最佳 Fetcher，绕过 Cloudflare/WAF，支持登录后抓取与结构化数据提取。来源：[Cedriccmh/claude-code-skill-scrapling](https://github.com/Cedriccmh/claude-code-skill-scrapling) |
| [hikerview-rule-generator](skills/hikerview-rule-generator/SKILL.md) | 自动生成、校验、迭代海阔视界（Hiker View）观看规则 rule.json / 小程序规则 / 聚阅子程序。 |
| [chinese-beginner](skills/chinese-beginner/SKILL.md) | 为电脑小白提供简体中文、少量步骤、清楚易懂的操作指导。 |
| [deliver-files-as-attachments](skills/deliver-files-as-attachments/SKILL.md) | 把生成/导出的文件保存为真实工作区文件并提供下载，而不是只在对话里打印。 |
| [image-processing](skills/image-processing/SKILL.md) | 确定性处理图片文件：缩放、裁剪、格式转换、压缩、传统 CV（读取/描述图片请看 see-images）。 |
| [see-images](skills/see-images/SKILL.md) | 读图：把图片交给视觉模型，返回文字后回答；含长截图/全景图切片（必要时）与聊天图片定位。 |
| [imagegen](skills/imagegen/SKILL.md) | 文生图：用文字描述生成新图片，免 API Key。来源：[pollinations/pollinations](https://github.com/pollinations/pollinations)（5070★，MIT；本仓库仅封装其 HTTP 接口，未复制其代码）。 |
| [agent-canvas-upload-limit](skills/agent-canvas-upload-limit/SKILL.md) | 按需解除 Agent Canvas 前端的上传体积限制（默认 3MB）。用户升级镜像后说一声再调用；含安全校验，结构变了会拒绝动手。 |

## 如何添加新技能

在 `skills/` 下新建一个以技能名命名的文件夹，放入 `SKILL.md` 即可；常驻规则类技能则直接放 `skills/<名字>.md`。
