# Superpowers 中文说明（安装记录）

## 这是什么

这是把 GitHub 上 `obra/superpowers` 这套「让 AI 写代码更有章法」的技能集，
移植到 OpenHands 后的本地版本。**放的位置**：`~/.openhands/skills/`。

## 它是怎么自动生效的

官方原本靠一个「会话开始钩子」把引导文字塞进模型上下文。OpenHands 没有这种钩子，
但 `~/.openhands/skills/` 下**顶层的 `.md` 文件会被当作“永久上下文”每次完整加载**，
效果一样。所以：

- 常驻引导文件：`~/.openhands/skills/superpowers.md`（每次对话都加载，就是它让技能自动触发）
- 14 个技能：`~/.openhands/skills/<技能名>/SKILL.md`
  （平时只把“名字 + 描述”列进 `<available_skills>`，用到时才由 `invoke_skill` 加载全文，省 token）

## 14 个技能一览

| 技能名 | 什么时候用 |
|---|---|
| `brainstorming` | 动手做任何新东西之前：先问清需求、给设计、等你点头 |
| `writing-plans` | 把需求写成详细的实施计划 |
| `executing-plans` | 在一个独立会话里按计划分批执行 |
| `subagent-driven-development` | 在**当前**会话里，每个任务派一个“新人”子代理去做并审查（首选） |
| `dispatching-parallel-agents` | 多个互不相关的任务并行处理 |
| `test-driven-development` | 先写会失败的测试，再写代码 |
| `systematic-debugging` | 遇到 bug 先系统找根因，不许瞎试 |
| `verification-before-completion` | 说“完成/通过”之前，必须先真跑一遍验证 |
| `requesting-code-review` | 主动请人审查代码 |
| `receiving-code-review` | 收到审查意见后如何严谨对待（不表演式附和） |
| `using-git-worktrees` | 用独立的工作区/分支干活，不动主分支 |
| `finishing-a-development-branch` | 收尾：合并 / 提 PR / 保留分支 |
| `writing-skills` | 新建或修改技能 |
| `using-superpowers` | 技能系统本身怎么用（常驻引导的内容就是它） |

## 改了什么（相对原版）

1. 删掉了原仓库里跟 Claude Code / Codex / Cursor 等工具相关的**插件外壳**（hooks、
   plugin.json、marketplace、移植文档、测试），只保留技能本身。
2. 正文里的 `superpowers:xxx` 前缀去掉了，改成 OpenHands 能直接识别的技能名。
3. 新增 `using-superpowers/references/openhands-tools.md`：把技能里的“动作”
   （加载技能、派子代理、建待办……）翻译成 OpenHands 的真实工具名。这是官方推荐的移植做法
   （“技能只描述动作，不写死工具名”）。
4. 常驻引导 `superpowers.md` 里补了中文说明，并写明：以【AGENTS.md 最高优先级规则】和用户指令优先。

## 注意 / 局限

- **子代理是“降级”的**：OpenHands 没有同步子代理。`launch_child_conversation` 是异步的，
  结果稍后才会回来，也不能中途追加消息。因此原版里“续用同一个实现者做修复轮次”改成
  “每轮新开一个子代理，用报告文件当记忆”。
- **视觉伴侣（visual companion）**：原版会在浏览器里跑一个 Node 服务看设计稿。这里更简单，
  直接生成 HTML 用 `canvas_ui_control` 预览即可。
- 这些技能正文是**英文**的（保留原版经过打磨的措辞，避免翻译走样）；但给你的汇报一律中文。

## 怎么临时关掉

- 想整个停用：删掉或改名 `~/.openhands/skills/superpowers.md` 即可（技能目录留着不影响，
  只是不再自动触发）。
- 想停用某个技能：把它的 `SKILL.md` 改名，或从 `~/.openhands/skills/` 移走。
