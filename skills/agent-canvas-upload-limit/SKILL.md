---
name: agent-canvas-upload-limit
description: 解除 Agent Canvas 前端的上传体积限制（默认 3MB）。当用户说"上传限制"、"3M 限制"、"传不上去大文件"、"解除上传限制"、"上传报错文件太大"，或升级 Agent Canvas 镜像后需要重新打补丁时使用。含安全校验，镜像结构变了会拒绝动手而不是改坏界面。
---

# 解除 Agent Canvas 上传限制

Agent Canvas 前端把上传上限写死在构建产物里（单文件 3MB）。后端和 agent-server 没有上限，
所以只要改掉前端那两个常量，就能传大文件。

**这个限制会随镜像升级回来**，因为镜像里没有任何启动钩子目录。所以本技能的核心动作是：
**用户升级镜像后主动来说一声**（或用户说上传传不上去时），才重跑一次脚本。

⚠️ **不要每轮自动检查、不要在用户没提的时候主动打补丁**——用户明确要求按需执行，不做自动维护。

## 第一步：先看现在是什么状态

```bash
python3 ~/.openhands/skills/agent-canvas-upload-limit/scripts/upload_limit_patch.py --check
```

- 打印「已经打过补丁」→ 说明当前已解除限制，**不需要做任何事**。
- 打印「找不到 ……-C5otVz4c.js」或「文件不是预期的原始构建」→ 走第二步。

## 第二步：打补丁（需要 sudo）

```bash
sudo python3 ~/.openhands/skills/agent-canvas-upload-limit/scripts/upload_limit_patch.py
```

看到最后一行「结果：全部通过」才算成功。然后让用户**按 Ctrl+Shift+R 强制刷新**浏览器。

升级镜像后补丁丢了，就重跑这一条。已打过再跑不会重复改（幂等）。

## 安全设计（这就是"判断能不能用这个补丁"）

脚本宁可不动，也不把界面改坏。它会依次判定，任何一条不过就停手、且不写任何文件：

1. **只认原始构建**：文件必须同时含两个常量标签和两条提示文案的原样。镜像若换了写法，
   直接报「文件不是预期的原始构建」并停下，同时打出现在文件里的上限是多少，方便判断
   新版是否已自带更大限制。
2. **冒烟测试**：临时起一个静态服务实测——服务是缓存启动时的长度，还是每次请求重新读。
   实测确认是「缓存长度」才继续；若新版改成每次重新读，说明等长改写不再必要，停下等人工确认
   （此时可加 `--force`）。
3. **等长改写**：改完字节数和原始完全一致（尾部补注释），既不改变运行时行为，也让静态服务
   缓存里的 Content-Length 仍然正确。
4. **五道自检**：等长、语义常量、`node --check` 语法、上传校验逻辑用例、线上字节数 == 磁盘字节数。
5. **自检不过就自动回滚**：只要有一道不过，脚本立刻把文件写回改动前的字节，界面不会停在坏状态。
6. **幂等 + 可还原**：已打过直接跳过；备份保留，`--restore` 一键回到 3MB。

实测记录（都跑过）：原始文件打补丁成功；`--check`、`--restore` 正常；把常量故意改错后，
自检报 FAIL 并成功回滚，文件 md5 与改动前完全一致。

## 判定为"不能用"时的表现

文件不匹配时脚本长这样（退出码 1，文件一个字节都没动）：

```
[FAIL] 文件不是预期的原始构建，缺标签：[b'exceeding the 3MB limit. Please select f']
[note] 单文件上限 Mr：3*1024*1024 = 3145728 字节（约 3.0MB）
[note] 合计上限 Nr：3*1024*1024 = 3145728 字节（约 3.0MB）
[FAIL] 为避免改坏界面，本次不动任何文件。
```

这时候要做的是**更新脚本里的标签**，而不是硬改。把新版文件里真正的常量和文案填进
`scripts/upload_limit_patch.py` 顶部的 `ORIGINAL_TAGS` 和 `REPLACEMENTS`，
注意配对后长度必须相等（不够就用 `--force` 前先想清楚）。

## 命令一览

| 命令 | 用途 |
|---|---|
| `sudo python3 upload_limit_patch.py --auto` | 一行输出模式，供用户要求自动化时使用；**平时不要主动跑** |
| `sudo python3 upload_limit_patch.py` | 人工打补丁，输出完整自检过程（已打过则转为检查） |
| `python3 upload_limit_patch.py --check` | 只看状态，不改文件，不需要 sudo |
| `sudo python3 upload_limit_patch.py --restore` | 还原成 3MB |
| `sudo python3 upload_limit_patch.py --force` | 跳过冒烟测试的安全判定（镜像已改版时用） |
| `node verify_upload_logic.js --expect-patched` | 单跑上传校验逻辑用例 |

`--auto` 保留着，但**不要主动跑**：用户明确说过升级后会自己来通知，不需要每轮自动检查。
只在用户主动提起上传限制时才动手。

## 文件说明

| 文件 | 内容 |
|---|---|
| `scripts/upload_limit_patch.py` | 主脚本：指纹校验、冒烟测试、等长改写、五道自检、还原 |
| `scripts/verify_upload_logic.js` | 从磁盘上真实的 bundle 里抽出 `Pr/Fr` 校验函数跑用例（上限、边界、合计超限、提示文案） |

## 已知事实（少走弯路）

- 目标文件是 `/opt/agent-canvas/frontend/assets/llm-not-configured-banner-*.js`，
  文件名带内容哈希，升级后可能变，所以脚本用通配符找，不是写死名字。
- 目录属 root，必须 `sudo`（容器内 sudo 免密）。
- 浏览器有缓存，改完必须 Ctrl+Shift+R，否则用户以为没生效。
- 静态服务缓存 Content-Length：改大文件会让响应被截断，所以只能等长改写。
