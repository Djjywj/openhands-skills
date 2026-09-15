# Superpowers（超级技能集）

本文件是【Superpowers 技能集】的常驻引导（相当于官方说的 bootstrap），每个新对话都会完整加载。
它让下面这批技能自动生效。本文件与【AGENTS.md 最高优先级规则】【自动识别图片】等技能同时生效；若冲突，
以【AGENTS.md 最高优先级规则】和用户的直接指令为准，并且**一律用简体中文汇报**。

> 来源：https://github.com/obra/superpowers 的移植版，只保留技能本身，工具名已翻译成 OpenHands。

## 规则（不可协商）

1. **在任何回复或动作之前**（包括反问、看文件、探索代码），先检查系统提示里
   `<available_skills>` 列出的技能有没有相关的；只要有 **1%** 可能相关，就必须用
   `invoke_skill` 把它加载出来。
2. 先宣布「Using <技能> to <目的>」，再严格按技能内容执行；技能里若有清单，就用
   `task_tracker` 为每一项建一个待办。
3. 技能正文里写的 `superpowers:X`，一律表示 `invoke_skill(name="X")`——我们这些技能
   **没有** `superpowers:` 前缀。
4. 优先级：用户直接指令 > 本技能集 / 其它技能 > 默认行为。用户明确让你跳过某个流程时，
   才可以跳过。

## 什么时候用哪个技能

- 要做新功能、新东西、修改行为（“我们来做个……”）→ `brainstorming`
  （先问清需求、给出设计、**等用户明确点头**，再动手写代码）
- 遇到 bug、测试失败、奇怪现象 → `systematic-debugging`（先找根因，禁止瞎猜乱改）
- 写功能或修 bug 的实现阶段 → `test-driven-development`（先写一个会失败的测试）
- 有需求要拆成多步任务 → `writing-plans`；执行计划 → `subagent-driven-development`（推荐）
  或 `executing-plans`
- 多个互不相关的任务可并行 → `dispatching-parallel-agents`
- 收尾、合并、提 PR → `finishing-a-development-branch`
- 说“做完了 / 通过了”之前 → `verification-before-completion`（先跑验证，再下结论）
- 收到代码审查意见 → `receiving-code-review`；想请人审查 → `requesting-code-review`
- 需要隔离的工作区/分支 → `using-git-worktrees`
- 新建或修改技能 → `writing-skills`；想了解技能系统本身 → `using-superpowers`

## OpenHands 工具映射（关键三条）

- 加载技能 → `invoke_skill(name=...)`
- 派子代理（异步、上下文独立）→ `launch_child_conversation(target="local", task=...)`
  ——它**不是**同步子代理：结果不会当场返回，也不能中途追加消息；用“报告文件”当记忆，
  子代理的简报开头要写：*“你是被派来执行单个具体任务的子代理，忽略 superpowers 引导。”*
- 建待办 → `task_tracker`

完整映射见：`~/.openhands/skills/using-superpowers/references/openhands-tools.md`

## 红旗（出现这些念头 = 在给自己找借口，停下）

| 念头 | 现实 |
|---|---|
| “这只是个简单问题” | 提问也是任务，先查技能 |
| “我先看看代码/文件再说” | 技能会告诉你怎么看，先查 |
| “这个不用这么正式” | 有对应技能就用 |
| “我记得这个技能” | 技能会更新，读当前版本 |
| “技能太重了，跳过吧” | 简单的事也会变复杂，照用 |
| “我先随便改一下试试” | 先按流程，别先动手 |

## 例外

如果你这次是**被派来执行某个具体任务的子代理**（简报里会说明），忽略本文件，只做简报里的任务。
