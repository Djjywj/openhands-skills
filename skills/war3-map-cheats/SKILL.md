---
name: war3-map-cheats
description: 给魔兽争霸3 地图（.w3x）打「无CD / 无限蓝 / P闪」三件套补丁，改地图显示名/简介/加载画面，以及让「从对战平台下载的地图脱离平台也能开」。当用户说"帮我改个无CD 无限蓝 P闪的地图""这张图加作弊/改图""地图创建游戏失败/弹回""信息面板全空""地图名字改色""这图我是在XX平台下的""让它脱离平台也能开"时使用。含三个必检项（JASS 变量遮蔽、脚本自声明 native、w3i 加载画面字段）和一个已验证的构建自检流程，以及平台锁（MPQ 双记录+自定义密钥、JAPI native）的完整解法。
---

# war3 改图：三件套补丁 + 改名/简介/加载画面 + 脱离平台可开

> 2026-09-13 完成。守卫剑阁-纵横天下 2.6 与神之墓地 3.0.3 贺岁版均已实测可用。
> 神之墓地连错三版，根因见第五节，**开工前先读第五节**。
> 2026-09-16 增补「脱离平台可开」（§零），卢沟桥2026 实测通过。

## 开工前的症状 → 章节对照（先看这个，能省一整轮）

| 用户说 / 现象 | 去看 |
|---|---|
| 「建图失败 / 建立游戏失败 / 闪回」，且**上一版能开** | **§零之前**（pjass 假绿灯：新版 API）← 先看这条 |
| 「这图我是在 XX 平台下的」「让它脱离平台也能开」 | **§零**（两把锁） |
| 「无法创建 / 弹回上一级」，无红字 | **§0.3 第二把锁（native）** ← 最容易漏 |
| 报「文件损坏 / `File: war3map.j`」 | **§0.2 第一把锁（MPQ 容器）** |
| 进图崩溃，弹 `Object: WEPlayerData` | **§三.2**（w3i 加载画面字段被写坏） |
| 「弹回」且已确认补丁本身没问题 | **§三.1**（JASS 变量遮蔽）+ **§五** |
| 要「全解锁 / 破平台验证 / 默认拥有某特权」 | **§0.5** |
| 要改名字 / 简介 / 加载画面 | **§一** + **§四「改地图名有三处」** |

**三个必检项**（少一个就弹回或名不符实）：
① JASS 变量遮蔽（pjass `+shadow`=0）② 脚本声明的 native 全部真实存在（**pjass 查不出**）③ 不碰 w3i 加载画面结构字段（改 wts 文本）


## 开工前的效率纪律（**2026-09-17 实测复盘，改图慢的真正原因**）

> 数据来源：曹操Ⅱ v15 那次对话的完整事件流（147.6 分钟，603 个工具动作）。
> 结论：**慢的不是工具，是我的轮次。** 工具总耗时 **12.4 分钟**，等 LLM 往返 **94.5 分钟**。

| 项 | 实测 | 健康值 |
|---|---|---|
| 每轮动作数（并行度） | **1.00** | ≥ 2 |
| LLM 等待 / 工具耗时 | **7.6×** | < 3× |
| 终端中位耗时 | 0.66s（最快 416 次里最慢 88s） | — |
| 一次性 `.py` 脚本 | **62 个**（`dig1..dig28` / `show1..show9` / `fixv7..`） | < 10 |
| 同形状命令最高重复 | **27 次** `pythonN workP \| head -N` | < 3 |
| `read_archive()` 重复解包 | **67 次** | 1 次 |

**六条纪律（前三条本来就是执行契约明文，不是新规矩）**：

1. **一轮发多个互相独立的工具调用** —— 本次 603 个动作 = 603 次往返，**零并行**。
   每轮平均等待 9.4 秒；按平均 2.5 个/轮可省 **≈57 分钟**。这是最大的一笔。
2. **开工一次性全量解包**到 `work/blk/`（`war3map.j/.w3i/.wts/.w3u/.w3a/.w3t/.w3h/.w3q`
   + `(listfile)`），之后**只读本地文件**。别「想查 A 解一次、想查 B 再解一次」。
3. **取证脚本只留常驻的几个，禁止 `digN.py` 家族**。推荐形态：
   ```bash
   python3 work/probe.py j 8072 8138     # 打印脚本行区间
   python3 work/probe.py w3a A06H        # 打印某技能字段
   python3 work/probe.py w3u 'uabi' Hmbr # 打印某单位字段
   python3 work/probe.py grep KFE_       # 全成员关键字计数
   ```
   一次写 4 个子命令，胜过写 28 个 `digN.py`（每个 = create + run = 2 次往返 ≈ 28 分钟）。
4. **同一形状的命令第 3 次出现就停手**，抽成循环/函数。
   本次把同一段 SLK 解析代码在 `python3 -c` 里**重抄了 18 次**。
5. **优先改一行，别换架构**。v5~v9 里前四版每次换方案、重写 `build_poison2.py`（编辑 63 次），
   最后 **v9 只改一个参数**（选人圆心：主目标 → 攻击者）就通过。
   **换架构前先自问：一个参数能不能解决？**
6. **判据先立**（`scripts/api124.py` 门禁），不通过不写盘。v8 的假绿灯让整版白做
   （8 分钟测试 + 8 分钟返工 + 20 分钟回退核查）。

> 复现方法：解压对话 zip → `events/event-*.json` 按序号排序；
> LLM 等待 = 上一条 Obs/Message/Hook → 本次 Action 的时间差；
> 工具耗时 = Action → 同 `tool_call_id` 的 Observation；
> 并行度 = 同一 `parent_id` 下 ActionEvent 个数；用户耗时 = Stop 钩子 → 下条 user 消息。


### 0.0 先验一层：网上下的「正版图」也可能就是平台图（2026-09-16 实测）

**别假设只有「从对战平台下载的图」才带锁。** 3DM 下载的《人族无敌》V3.0.1
（`53BB021F299EA7993592D6AE7A719EF0.w3x`）照样带 **36 个平台专属 native**
（`DzAPI_Map_*` 一批 + `EX*` 若干）—— **网易官方对战平台（DzAPI）和 YDWE 一样往进程里注入 native**。
用户拿它单机玩 → 「没法建图」。

**硬规则：从 3DM / 破解站 / 论坛下完图，交给用户之前先跑一次 native 检查。**

- 判据：剥掉开头 512 字节 `HM3W` 头 → 当**裸 MPQ** 喂给 `mpyq` 读 `war3map.j` →
  `re.findall(r'^\s*native\s+(\w+)\s+takes', txt, re.M)`。
  **数量 > 0 且不在标准库 = 平台图**；正规单机图该值是 **0**（对照：神之墓地 / 守卫剑阁）。
- 旁证：脚本里出现 `hook` 声明，或名字带 `DzAPI_Map_` / `EXGet` / `EXSet` 前缀，都指向平台 API。
- 还有一层：平台图常在脚本**头部塞一坨二进制**（本次约 2KB），刻意让脚本没法直接反编译 ——
  脚本开头不像 JASS 就往这个方向想。

**交付纪律**：查出带 native 时二选一 —— ①当场按 §0.3 摘掉再交付；②明确告知
「这是平台图，单机开不了，要不要我解锁」。**别闷头下完就交**，让用户替你发现。


## 零之前：**「pjass 通过」是本技能最贵的假绿灯**（2026-09-17 二次实锤）

> ⚠️ **本技能服务的目标图版本区间 = 1.24 ~ 1.27**（用户 2026-09-17 明确要求）。
> 判据取最保守的 **1.24** 兜底。开工前若知道确切小版本（1.24a/1.24b/1.26/1.27），以它为准。

> **本机所有的 `common.j` 都不是 1.24 的。** 实测：

| 文件 | `native Blz*` 数 | 真实版本 |
|---|---|---|
| `/tmp/jasslib/common.j`（pjass 用） | **287** | 1.32 Reforged |
| `/tmp/common.j` | 287 | 1.32 |
| `/tmp/jass/common.j` | 395 | 1.33+ |
| `…/ba91b0911c2943c79336cf9391876cb4/work/ref/common.j` | 395 | jassdoc 版（含 Reforged） |

连 GitHub 上能搜到的 `common.j`（WurstScript / PyWC3 / w3x2lni / Drake53 全仓库）
**没有一份是 1.24 的**，清一色 1.31/1.32。

**后果**：拿 1.32 的库去校验 1.24 的图，pjass 会**放行 1.24 根本不存在的 API**
（如 `EVENT_PLAYER_UNIT_DAMAGED`、`BlzGetEventDamageTarget`，均 `@patch 1.31`），
于是打印 **`Parse successful / 0 错误`——而真机加载时编译失败 → 「建立游戏失败 / 闪回」**。

> ⚠️ 注意别把这一条用反了：`GetEventDamage` / `EVENT_UNIT_DAMAGED` / `GetEventTargetUnit`
> 都是 **`@patch 1.00`，1.24 完全可用**（见下表）。**v8 死于 `EVENT_PLAYER_UNIT_DAMAGED`
> 这一个符号**，不是整个「伤害事件家族」都不能用。

**硬规则**：

1. **`pjass 0 错误` 只在「所有用到的 API 都是旧图里出现过的」时才算证据。**
   补丁引入了**基图从未出现过的 native / 事件常量**时，pjass 的绿灯**无效**，
   必须另找真机证据（见下）。
2. **判据优先级**：**本图先例 > 旧图先例 > 官方文档 > pjass**。
   pjass 排最后，因为它的库可能是新版本。
3. **一锤定音的判据：jassdoc 的 `@patch` 版本号**（2026-09-17 实锤，本仓库 `work/api124.py` 已实现）

   [lep/jassdoc](https://github.com/lep/jassdoc) 是社区维护的 WC3 JASS API 数据库，
   每个 native / 常量 / 事件都带 `@patch X.Y` 标注它**从哪个版本开始存在**。
   `https://raw.githubusercontent.com/lep/jassdoc/master/common.j`（另有 `Blizzard.j`）。
   **判据 = `@patch <= 1.24a`**（目标区间 1.24~1.27；jassdoc 在 1.25/1.26/1.27 无任何符号，
   版本从 `1.24a` 直接跳到 `1.29.0`，故该阈值恰好覆盖）。比 pjass 可靠得多，实测对照：

   | 符号 | `@patch` | 1.24 |
   |---|---|---|
   | `EVENT_UNIT_DAMAGED` | 1.00 | ✅ |
   | `GetEventDamage` | 1.00 | ✅ |
   | `GetEventTargetUnit` | 1.00 | ✅ |
   | `TriggerRegisterUnitEvent` | 1.00 | ✅ |
   | `GetEventDamageSource` | 1.17a | ✅ |
   | **`EVENT_PLAYER_UNIT_DAMAGED`** | **1.31.0.11889** | ❌ |
   | `BlzGetEventDamageTarget` | 1.31.0.11889 | ❌ |
   | `BlzSetEventDamage` | 1.29.2.9231 | ❌ |

   `work/api124.py` 用法：
   ```bash
   python3 ~/.openhands/skills/war3-map-cheats/scripts/api124.py 脚本.j [基图.j]
   ```
   它把 jassdoc 的版本表建起来，扫脚本里的标识符，凡 `@patch > 1.24` 的**硬报错**，
   `1.25~1.27` 的给**警示**（不阻断）。已接进构建流程，**不通过不写盘**。
   **v8 就是被这一个符号害死的：`EVENT_PLAYER_UNIT_DAMAGED`（= 1.31 才有）。**
   对照实验：v8 ❌ / v9 ✅（0 个）。

   > 2026-09-17 复现确认：带 1.32 库跑 v8 → `Parse successful: 13845 lines`
   > （= 真实行数，**连行数判据也过**）——假绿灯的完整形态就是这样，别指望行数判据救场。

### 1.24 ~ 1.27 可用符号全貌（2026-09-17 从 jassdoc 实测，改图前必看）

| 结论 | 数据 |
|---|---|
| common.j 声明总数 | 3568 条（native / type / constant / function） |
| **`@patch <= 1.24` 可用** | **1687 条** |
| 不可用（1.29 及以后） | 1881 条 |
| Blizzard.j 可用 / 总数 | 1227 / 1401 |
| **落在 1.25 / 1.26 / 1.27 的符号数** | **0 个** —— jassdoc 版本从 `1.24a` 直接跳到 `1.29.0.8803` |

⇒ **硬底线取 1.24a 是安全的**，且**不需要为 1.25~1.27 放宽任何东西**。

**1.24a 引入了 105 条（common.j）——全是 hashtable 家族**（这是 1.24 分水岭）：

```
type hashtable extends agent
native InitHashtable                       native GetHandleId / StringHash
native Save*  (integer/real/boolean/string + 各种 handle)
native Load* / HaveSaved* / Flush* / RemoveSaved*
constant native GetSpellTargetX / GetSpellTargetY / GetTriggerDestructable
```

* ⇒ **1.24 图上可以用 hashtable，1.23 及更早不行。** 这常是「同一份脚本，1.24 能开、1.20 报错」的真因。
* Blizzard.j 同批加了 98 条 BJ 包装（`Save*BJ` / `GetHandleIdBJ` / `InitHashtableBJ`）。

**1.29.0.8803 才有的 16 条**（1.24~1.27 **全都没有**，用了必挂）：

```
type mousebuttontype
constant native ConvertMouseButtonType / GetBJMaxPlayers / GetBJPlayerNeutralVictim
                GetBJPlayerNeutralExtra / GetBJMaxPlayerSlots
                GetPlayerNeutralPassive / GetPlayerNeutralAggressive
MOUSE_BUTTON_TYPE_{LEFT,MIDDLE,RIGHT}
EVENT_PLAYER_MOUSE_{DOWN,UP,MOVE}
native AutomationTestStart / AutomationTestEnd
```

> ⚠️ **jassdoc 正文里的版本说明只作参考，别当判据**（当判据的是 `@patch` 标注）。
> 例：`common.j` 有一处正文写「needed since 1.24b」，但该声明**只在 1.29 才补标 `@patch`**。
> 拿正文当版本判据会误判。

4. **2026-09-17 曹操Ⅱ v8 实锤**：为了让「中毒跟随引擎实际打到的目标」，
   在补丁里注册了 `EVENT_PLAYER_UNIT_DAMAGED` + `GetEventDamageSource` + `GetEventDamage`。
   pjass（1.32 库）报 0 错误，我据此交付 → **用户回「建图失败回退」**。
   回退到只注册 `EVENT_PLAYER_UNIT_ATTACKED`（**本图自己用过 5 次**）的 v7 立即可用。
   * 旁证：本图的李广之弓 `KFE_Multi_Action` 也**只用** `EVENT_PLAYER_UNIT_ATTACKED`，
     从不用伤害事件。

### 反面教材：**我自己的旧报告已经写过这条结论，我又踩了一遍**

`…/ba91b0911c2943c79336cf9391876cb4/人族无敌2.5X-诊断报告.md` 第 65 行原文：

> 比对用的 `common.j`（jassdoc 版）已含 `Blz*` 系列，即 **Reforged（1.32+）** 的新 API……

**教训**：开工改图前，**先把同题材的旧工作区报告读一遍**（尤其 `*诊断报告*.md` / `AGENTS.md`），
别只读技能库。技能库里的通用条目不包含我上次的具体结论。

### 技能目录自带工具（2026-09-17 补齐，以前只有一个 SKILL.md）

`~/.openhands/skills/war3-map-cheats/scripts/` —— **直接用，别在本机到处找 `common.j`**：

| 文件 | 作用 | 已验证 |
|---|---|---|
| `scripts/probe.py` | **常驻取证脚本**（效率纪律第 2、3 条的工具）。`blk` 一次全量解包 / `j` 看脚本行区间与正则搜 / `w3a`·`w3u`·`w3t` 看对象字段 / `grep` 全成员计数 / `cmp` 逐成员比对 / `list` / `selftest`。**取代 `digN.py` 家族** | selftest + 真图 4 例 |
| `scripts/api124.py` | **1.24 版本门禁**（本技能最重要的判据工具）。`python3 api124.py 脚本.j [基图.j]`，退出码 1 = 有 1.24 不存在的符号 | 真机真值 4/4 |
| `scripts/native_check.py` | **必检项③**（§三.3）：脚本自己声明的 native 是否真实存在。`python3 native_check.py 地图.w3x` | 3 张图判对 |
| `scripts/rt_api124.py` | api124 的回归测试（**改动判据后必跑**）。A 真机真值 / B 类型漏检 / C 假报警 / D 合法性 | 全绿 |
| `scripts/make_samples.py` | 生成 A 组样例（v8 负样例按已记录根因**派生**，不靠考古） | — |
| `scripts/extract_j.py` | 从地图提 `war3map.j`（`--batch` 可批量） | — |
| `scripts/maprepack.py` + `mpqrepack.py` | MPQ 读/写自带依赖（**不要用 mpyq 当兜底，见下**） | — |
| `scripts/ref/{common.j,Blizzard.j}` | jassdoc 副本，**只读 `@patch`，绝不能拿去跑 pjass** | — |

```bash
S=~/.openhands/skills/war3-map-cheats/scripts
python3 $S/probe.py blk 某图.w3x               # ① 开工第一件事：全量解包到 work/blk/
python3 $S/probe.py j 8072 8138                # 看脚本行区间（以后别再开地图）
python3 $S/probe.py w3a A06H                   # 看某技能全字段
python3 $S/probe.py cmp 基图.w3x 成品.w3x       # 逐成员比对
python3 $S/probe.py selftest                   # 改了 probe 就跑这个
python3 $S/api124.py work/blk/war3map.j 基图.j  # 门禁（不通过不写盘）
python3 $S/rt_api124.py                        # 改过判据就重跑这个
python3 $S/native_check.py 成品.w3x            # 必检项③
```

**api124.py 的已知盲区（实测探针得出，必须知情）**：

| 情况 | 处理 |
|---|---|
| **变量/句柄类型名**（`framehandle` / `animtype` / `originframetype` / `commandbuttoneffect`） | ⚠️ 曾是**真 bug**（jassdoc 只给 `type` 声明和 native 参数标 `@patch`）。现已修：类型名一并收录 —— 回归测试 B 组盯着它 |
| 注释里的符号（`// EVENT_PLAYER_UNIT_DAMAGED`） | ✅ 已先剥 `//` 与 `/* */` 再扫，不误报（**假报警会训练人忽略工具，同样是病**） |
| 字符串里出现的符号（`GetPlayerName(p) == "Blz..."`） | ⚠️ 降级为**提示**不阻断，人工确认 |
| jassdoc 未标 `@patch` 的声明 | ⚠️ **保守放行**但列出来，用「本图先例」复核 |
| 脚本自己 `native` 声明的函数 | ❌ **本工具查不出**（它只查标准库符号）→ 必须另跑 `native_check.py` |

> 走不通的死路（别再试）：**想用 jassdoc 生成一份「剔除超版声明」的 1.24 `common.j` 直接喂 pjass**。
> 三条硬障碍：① pjass **不支持块注释** `/* */`（jassdoc 全用它写文档，原样喂报 93959 错，剥掉后 11565 行 0 错）；
> ② 删声明会**打破引用它的保留项**（连锁 889 条，越删越烂）；③ jassdoc 不是可编译库。
> **正解**：判据用 `api124.py` 的「`@patch` + 标识符」路线，**不要**去伪造库。

## 零、脱离平台可开（"无法创建 / 弹回"的完整解法）

> 2026-09-16 在「卢沟桥2026-正式版1.9」（下载自 **80对战平台**）上跑通，用户实测通过。
> 平台图有**两把锁，必须同时解开**。只解一把的症状不同 —— **先按症状分层能省一整轮**。

### 0.1 症状分层（先看这个）

| 现象 | 坏在哪一层 | 去哪查 |
|---|---|---|
| 报「文件损坏 / **File: war3map.j**」 | MPQ 容器层 | §0.2 第一把锁 |
| 「**无法创建、静默弹回**」（一闪而过、无红字） | JASS 脚本层 | §0.3 第二把锁 |

### 0.2 第一把锁：MPQ hash 表双记录 + 自定义密钥

保护者在 `war3map.j` 的 hash 链上挂**两条记录**：

| locale | platform | 指向 | 内容 |
|---|---|---|---|
| 0 | **0xFF00** | block 5 | 完整脚本，明文 |
| 0 | **0x0000** | block 72 | 完整脚本，**自定义密钥加密** |

- **平台**读取参数是 `0xFF00` → 精确命中 → 拿到明文 → 照常能玩。
- **魔兽本体**查 `(0,0)` → 按 StormLib 规则命中**后一条** → 解不开 → 无法创建。
  （StormLib `GetHashEntryLocale`：非 0 查询精确命中即返回；`(0,0)` 查询循环里**后者覆盖前者**。）
- **修法要点**：`mpyq` 与 StormLib **选中的不是同一条**（mpyq 拿到 block 5）。
  所以要把**两条都写成同一份完整脚本**，谁被选中都一致，且平台也照常能玩。

**破自定义密钥（已知明文攻击）**：

- 标准 244 个派生 key 全失败 ⇒ 确认是第三方自定义密钥。
- MPQ 加密按 4 字节字处理，**sector 表首项 = 表长度**，据此可反解出表 key。
- 得表 key 后：**文件 key = 表 key + 1**，第 i 个 sector 再 `+i`。
- **坑**：MPQ 加密只覆盖整 4 字节字，**尾部不足 4 字节的保持原文**；
  忘了这点 zlib 会报 `incorrect data check`。
- 同链的 `(listfile)` 通常也被同样加密，**一起解**（否则读不出文件名清单）。

### 0.3 第二把锁：平台专属 native（JAPI）

**这是最容易漏的一层。** 脚本会**自己声明**一批暴雪没有的 native，由平台在进程内存里注册：

```
EXGetEffectX/Y/Z  读特效坐标         EXSetEffectXY / EXSetEffectZ   改特效位置/高度
EXGetEffectSize / EXSetEffectSize   读/写特效缩放
EXEffectMatRotateX/Y/Z  绕轴旋转     EXEffectMatScale  三轴缩放
EXEffectMatReset        矩阵复位     EXSetEffectSpeed  播放速度
UnitAlive  （第三方 HcUnitAlive 库，常是空壳、零调用）
```

- 魔兽加载地图要**编译** `war3map.j`，碰到**不存在的 native 直接编译失败** → 无法创建、弹回。
- 大多是 **YDWE（Everdream）的 `YDWEJapiEffect` 库**，官方源可查：
  `actboy168/YDWE → Development/Component/ui/japi/jass/japi/YDWEJapiEffect.j`（声明）
  与 `Development/Plugin/Warcraft3/yd_jass_api/Effect.cpp`（实现：取对象后**直接写内存偏移**，
  位置 `+0xC0/C4/C8`、缩放 `+0xE8`、变换矩阵 `+0x108`）。纯 JASS 做不了（暴雪特效创建后不可控）。
- **修法**：把 native **声明 + 调用**一起摘掉，但**摘之前逐条确认调用点是否真的会跑到**。
  本次 14 个 native 只有 2 处调用，且都在无意义路径上
  （一个在**无人调用**的函数 `YDWESetEffectLoc` 里，另一个缩放的特效**下一行就被 `DestroyEffect`**）
  ⇒ 摘掉**玩法零损失**。摘完脚本声明的 native 数应为 **0**。

**native 家族不止 YDWE**（2026-09-16 实测，人族无敌2.5X 共 **36** 个）：

| 前缀 | 数量 | 出处 |
|---|---|---|
| `DzAPI_*` | 26 | **网易官方对战平台**（`Map_SaveServerValue`/`GetMapLevel`/`HasMallItem`/`GetGuildName`/`IsRedVIP`/`GetMatchType`…） |
| `EX*` | 6 | YDWE japi（`EXExecuteScript`/`EXPauseUnit`/`EXGetUnitAbility` 等） |
| `RequestExtra*` | 4 | yiyi / 11 平台数据请求 |

⇒ 见到 `DzAPI_` 前缀就是网易平台图。

#### ★ 更省事的手法：native 声明 → **同名同签名的空实现**

删「声明+调用」适合调用点很少（≤5 处）的情形。**调用点多的时候别这么干**：
把 `native` 声明**整体替换成同名同签名的函数**，按返回类型给安全默认值，
**调用点一行都不用改**（人族无敌 2.5X 有 **91 处**调用，全部原样保留）。

```jass
// 原：native EXGetAbilityState takes ability abil,integer state_type returns real
// 换：function EXGetAbilityState takes ability kfe_abil,integer kfe_state_type returns real
//     return 0.
//     endfunction
```

默认值表：`boolean→false`、`integer→0`、`real→0.`（**必须是 `0.`**，JASS 类型严格）、
`string→""`、`nothing→空函数体`、`ability→null`（`ability` 是**标准库类型**，
见 `common.j:78 type ability extends agent`，`null` 合法）。

**要点**：
1. **参数统一加 `kfe_` 前缀**（见 §三.1）——地图可能有 500+ 个单/双字母全局变量，
   native 的形参名 `u`/`abil`/`value` 极易遮蔽它们。
2. 36 行声明**必须是连续块**才能一次性替换（先断言 `\r\n` 数与声明数相等）。
3. 改完 `native` 声明数必须为 **0**，且 36 个名字各自**有且只有一个函数定义**
   （少了会「未定义」、多了会「重复定义」，两种都编译不过）。

### 0.4 对照图要用对

拿「能单机跑的图」做对照时，必须对照**你要断言的那个变量**：

- ✅ 本次：对照组「爆砍一棵树」**声明的 native 数 = 0**，而平台图 = 14 ⇒ 直接坐实病因。
- ❌ 反例（见 §五）：对照组只是原图/空函数时，它「能进」**证明不了任何事**。

### 0.5 需求是「全解锁 / 破平台验证」时怎么做（2026-09-16 新增）

平台图把「你有没有商城道具 / 会员 / 地图等级」全收进**几个判定函数**里，
认准它们就一步到位。网易平台的典型形态：

```jass
function AU takes player ET,string BU returns boolean   // 有某商城道具吗
    if ( CM ) and ( GetPlayerController(ET) == MAP_CONTROL_USER ) then
        return true
    else
        return DzAPI_Map_HasMallItem(ET, BU) or ( RequestExtraBooleanData(50, ...) )
    endif
endfunction
function CU takes player ET returns integer             // 地图等级
function FU takes player ET returns boolean
```

**改成恒定放行**（`return true` / `return 50` / `return true`）= 破验证 + 全解锁，一次搞定。
`CU` 恒 **50** 可一次打开 5/10/15/20/25/30 六档等级奖励。

#### ⚠️ 千万别去改 `CM`（运行模式开关）

`set CM=( GetObjectName(…) == GetObjectName(…) )` 是**「特权/开发者模式」总开关**。
`CM` 为真会顺带打开：**白送 50 万金币**、人口上限 75、下一波改成 **15 秒**、
`-bo`/`-gx` 调试指令。**超出用户要求** —— 改 `AU/CU/FU` 才精准。

#### ⚠️ 改 `CU` 前必须逐个看调用点，不能无脑调大

`CU` 既被 `>= N` 用，也可能被 `<= N` 用。人族无敌 2.5X 的 4 处调用：
2 处 `>=`、**1 处 `<= 5`**（地图等级 ≤5 送一把武器）、1 处存进 `DZ` 再比 6 个档位。
`CU` 恒 50 会让那处 `<= 5` **永远为假**。⇒ 通用教训：
**同一个判定函数若同时有 `>=` 和 `<=` 两种用法，改返回值前必须枚举全部调用点。**

#### 存档标志 ↔ 效果的对应怎么查（别猜）

平台图把解锁状态存进 hashtable：`call SaveBoolean(YL, NX, 1111638873, true)`。
**查法**：找到「读该标志的那一行」，取它所在 `if` 块里的**第一条中文提示**
（`DisplayTextToPlayer` 的字符串），与效果名对应 —— 这样得到的是**逐块核准**的结果。

⚠️ **不要按字符串邻近猜**。人族无敌那次把 `GXDS`/`SJYD` 猜成「基础建设」，
实际它们是**前置条件标志**，真正的基础建设是 `JCJS`。

**快捷技巧**：标志 ID 就是 4 个 ASCII 字符按 `struct.pack(">I", n)`。
如 `1111638873` → `BBCY`（百步穿杨）、`1465534284` → `WZGL`（王者归来）。
**看 ID 就能猜出作者命名，比读上下文快得多。**

#### 摘掉平台 API 后必须向用户披露的退化点

`SaveServerValue`→存档不落盘、`GetServerValue`→读不到存档、
`EXExecuteScript`→本地化文本为空、`DzAPI_Map_Stat_SetStat`→房间面板不显示、
`EXPauseUnit`→晕眩不再暂停单位。

**还要主动交代「不确定项」**：`EXGetAbilityState` 恒返 0 时，
若脚本拿它当「技能冷却好没有」的闸门（`VT(...) == 0`），触发型技能会更频繁触发。
无游戏环境验证不了 —— 明确告诉用户「实测手感不对告诉我，我改默认值再出一版」。

## 一、交付命名与配色（用户指定，以后默认照做）

```
|cffffcc00<地图名>|cff8000ff·无CD|cff00b0ff·无蓝|cff00ff00·P闪|r
```

- 金色 = 主名，紫色 = 无CD，蓝色 = 无蓝，绿色 = P闪。
- 地图简介统一写「给佳佳的爱 <改完的日期，用户时区 UTC+8>」，例：`给佳佳的爱 2026.09.13`。
- 地图列表里的显示名来自 **MPQ 头 offset 0x08** 的地图名，不是文件名。
- 实测名长：40+ 字符（含颜色代码约 89 字节）可正常显示；字段上限约 500 字节。
- 测试图要**改名区分**（用户一次会下好几张放同一目录）：`n_test*` 系列。

## 二、三件套实现（JASS 补丁）

只对真人玩家生效，不影响电脑 AI：

```jass
// 判据：GetPlayerController(GetOwningPlayer(u)) == MAP_CONTROL_USER
// 无CD + 无限蓝：每 0.5 秒轮询己方英雄
//   call UnitResetCooldown(u)
//   call SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MAX_MANA))
// 施法瞬间再补一次（EVENT_PLAYER_UNIT_SPELL_EFFECT / SPELL_ENDCAST）
// P闪：拦"巡逻"点目标指令（851990 = patrol）
//   IssueImmediateOrder(u,"stop") 后 SetUnitX/SetUnitY 到 GetOrderPointX/Y
```

注册写法（两种都实测可用，首选第一种）：

```jass
// 主：循环 12 个玩家注册 SPELL_EFFECT / SPELL_ENDCAST / ISSUED_POINT_ORDER
// 备：一个 timer(0.5s,true) + TriggerRegisterAnyUnitEventBJ(trigger, EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER)
```

插入位置：`war3map.j` 里 `function main takes nothing returns nothing` 之前插入补丁函数体，
在 `main` 的 `endfunction` 前插一行 `call KFE_Init()`。

## 三、三个必检项（少一个就弹回或名不符实）

### 1. 局部变量命名：一律加前缀，禁止裸 `x` / `y`

混淆过的地图，全局变量是单字母，常见 `timer x`、`timerdialog y`。
补丁里写 `local real x` 会遮蔽它们 → 加载器报 `x shadows global variable` → **创建游戏失败/弹回**。

判定工具（必须 0 错）：

```bash
pjass +shadow wc3_common.j wc3_blizzard.j war3map.j
```

### 2. 加载画面文字：**不要改 w3i 字段，改 wts 里的 TRIGSTR 文本**

写 **w3i 的**加载画面「文字 / 标题 / 副标题」字段会进图崩溃，弹：

```
This application has encountered a critical error: 内存资源不足，无法处理此命令。Object: WEPlayerData
```

`WEPlayerData` = 魔兽解析 w3i 玩家数据的那块。
**证据**：3.0.3 原图这三个字段本来就是空的；能正常玩的守卫剑阁 v2 也是空的。

**✅ 安全替代写法（2026-09-16 实测可用）**：w3i 里这几个字段存的是 **`TRIGSTR_163` / `TRIGSTR_165`**
这样的**字符串编号引用**，真正文本在 `war3map.wts`。**只改 wts 里的文本内容、不动 w3i 的任何字段**
（字段仍指向同一个编号），既改了加载画面又不会碰坏结构：

| w3i 字段 | 引用 | 作用 |
|---|---|---|
| `loadTitle` | `TRIGSTR_163` | 加载画面**大标题** |
| `loadText` | `TRIGSTR_165` | 加载画面**说明文字** |

`wts` 格式（注意 BOM 与 CRLF）：

```
efbbbf STRING <n>\r\n{\r\n<文本>\r\n}\r\n\r\n
```

- **坑**：替换串别写成原始字符串 `r'...\r\n...'` —— 会把**字面的 4 个字符 `\r\n`** 写进文件，
  表现为「wts 里搜不到 `STRING 3\r\n`」。用字节串 `b'STRING %d\r\n{\r\n'`。

### 3. 脚本声明的 native 必须都真实存在（**pjass 查不出这一项**）

见 §0.3。**pjass 会因为脚本自己声明了这些 native 而放行**，
所以 `pjass 通过 ≠ 真实魔兽能加载`。**直接跑自带工具**（2026-09-17 已脚本化）：

```bash
python3 ~/.openhands/skills/war3-map-cheats/scripts/native_check.py 成品.w3x
```

判据：抽出 `^\s*native\s+(\w+)\s+takes` 的名字。

| 结果 | 含义 |
|---|---|
| **声明的 native 数 = 0** | 不是平台图，单机可加载（曹操传 / 人族无敌2.5X 都是 0） |
| 声明了一批标准库没有的 native | **平台图**，脱离平台必然「无法创建」。处置见 §0.3（摘声明 / 同名同签名空实现桩） |

实测对照（2026-09-17）：

| 地图 | 声明 native 数 | 结论 |
|---|---|---|
| 曹操传 v15 原图 | **0** | 单机可加载 |
| 人族无敌2.5X（网易平台图） | **0** | 能加载，平台锁在别处（破验证逻辑） |
| 卢沟桥2026（80平台） | **14**（8 个 `EXGet/EXSet*` = YDWE japi + `UnitAlive` 等） | 平台图，须摘掉 |

识别用的前缀：`DzAPI_Map_*`（网易）、`EXGet*/EXSet*`（YDWE japi）、
`RequestExtra*`（yiyi/11 平台）、`UnitAlive`（第三方空壳库）。

> **读成员别用 mpyq 兜底**：它读不了加密的 `(listfile)`，报
> `NotImplementedError: Encryption is not supported yet.`（或 `None` 属性错）。
> 用本技能自带的 `scripts/maprepack.py`（能解**自定义密钥**加密成员，已实测通过卢沟桥与曹操传）。

## 四、构建与自检流程

**路径 A（无平台锁的普通图）**：用 `mpqwrite.Writer` 打开基图，`mpq_enc.unpack` 取出文件。

**路径 B（带平台锁 / 需要重组容器）**：用一套最小 MPQ 手术式重打包（见 §六"工具链"）。
两条路径共同的步骤：

1. 取出 `war3map.j` / `war3map.w3i` / `war3map.wts`。
2. 改 `war3map.j`：插补丁 + `call KFE_Init()`（**必须插在 `function main` 之前**，JASS 先定义后使用）；
   带平台锁的图先按 §0.3 摘掉平台 native。
3. 改 `war3map.w3i` 的**名字/简介**（只改引用指向、或直接改它引用的 wts 文本）；
   改加载画面走 **wts 文本**（见 §三.2）。
4. 改 MPQ 头 offset 0x08 的显示名（列表里看到的那个）。
5. 写回。
6. **自检要验被改的那一项本身**：
   - 🔴 **先过版本门禁**（1.24~1.27 目标图**必跑**，这是补丁引入新符号时的唯一硬证据）：
     ```bash
     python3 ~/.openhands/skills/war3-map-cheats/scripts/api124.py work/patched_war3map.j 原图脚本.j
     ```
     退出码非 0 ⇒ **不许写盘**。报告里会标出「基图无先例」的符号，优先按「本图先例」替换。
     （`pjass 0 错误` 不能代替这一步 —— 见 §零之前。行数判据也不能代替：v8 假绿灯时行数是对的。）
   - 🔴 **平台图必跑必检项③**：
     ```bash
     python3 ~/.openhands/skills/war3-map-cheats/scripts/native_check.py 成品.w3x
     ```
     声明 native 数 ≠ 0 ⇒ 按 §0.3 摘掉，并披露退化点。
   - pjass `+shadow` 错误数 = 0；
   - 🔴 **绝不为了让校验通过而预处理 war3map.j**（2026-09-17 曹操Ⅱ实锤，比下面两条都重要）。
     本图脚本是**裸 CR 换行**，我用 pjass 校验时报 3 个语法错误；我误判成"pjass 不认 CR"，
     于是在校验脚本里加了 `.replace(b'\r', b'\n')` —— **这一改把唯一能暴露 bug 的特征抹掉了**，
     之后每次"0 错"都是假绿灯。**实测 pjass 本来就支持裸 CR**：原图用**原始字节**喂，
     0 错、解析 13809/13809 行完全正确；坏图用原始字节喂则明确报错。
     ⇒ **喂原始字节**；若要转换，必须断言行数守恒，且**保留原始字节那条判据**。
     ⇒ **把真报警判成误报之前，必须先跑一个已知-good 的基线做对照**（如原图），
       证明工具对基线不产生该报警。没做对照不得判误报。
     ⇒ **修改判据 ≠ 定位原因**；一旦用"改判据"代替"查原因"，后续所有"通过"都不再有信息量。
   - ⚠️ **pjass 解析行数必须等于脚本真实行数**（`j.count(b'\r') + 1`）。
     **只看 "Parse successful" 会被骗**：本图被 `//` 注释吞掉 5870 行后，
     pjass 照样打印 `Parse successful`（实际只解析了 7944 / 13813 行，且解析器**静默收尾**）。
     行数对不上 = 有代码被吞，**此时"通过"毫无意义**。
     （注意：pjass 输出里**三个文件各有一条 Parse successful**，要取**第 3 条**才是本图脚本。）
   - ⚠️ **脚本里 `//` 出现次数 = 0**（本图 CR 换行下 `//` 吞掉后面全部代码 → 建图闪退，详见 §409）。
     构建脚本里加**硬断言**，别靠人记得：
     ```python
     assert b'//' not in PATCH_FUNCS.encode()   # 补丁里禁止出现 //
     assert data.count(b'//') == 0              # 基图 j 里也不许有 //
     ```
     **2026-09-17 二次实锤**：明知有此条仍踩 —— 补丁里写 5 处 `//`（其中 4 处还在第 8094 行后，
     `\n` 一个都没有），第 692 行那处 `//` 后 48196 字节才遇到 `\n`
     ⇒ **吞掉 13247 行**，`endglobals`(697)/`function main`(8332)/`InitBlizzard`(13052) 全被吞 → 闪退。
     **"改成 ASCII 注释无效"**，关键是有没有 `//` 字符。**唯一可靠的是构建时 assert，不是记性。**
   - **脚本声明的 native 全部存在于标准库**（§三.3，pjass 查不出）；
   - 读回来确认名字/简介/加载画面**真的变了**（别只看「文件能打开」）；
   - 逐块抽检 MPQ：坏块 = 0；hash 表未被改动；
   - 下载链接实测 HTTP 200（`curl -o /dev/null -w '%{http_code}'`，GET，HEAD 会 405）。
7. 只 `replace` 现有文件；**往 MPQ 加新文件会失败**（smpq / SFileAddFile 都不行）。

### 改地图名有**三处**，都要改

| # | 位置 | 影响 |
|---|---|---|
| 1 | **MPQ 头 offset 0x08** | 对战平台 / 地图列表里显示的**名字** |
| 2 | `war3map.w3i` 的 name / desc 字段 | 游戏内名字 / 简介（指向 `TRIGSTR_003` / `TRIGSTR_005`） |
| 3 | `war3map.wts` 的 `TRIGSTR_163` / `TRIGSTR_165` | 加载画面**大标题** / **说明文字** |

- **坑（现场踩过）**：MPQ 头 offset 0x08 的名字后面紧跟 `uint32 flags` + `uint8 maxPlayers`，
  再往后是补零填充，**MPQ 从 512 字节处开始、这个总长不能变**。
  名字变长时要把 `flags+maxPlayers` 这 5 字节**原样后移**，
  直接覆盖会**把 maxPlayers 抹成 0**（自检要核这一项）。
- `w3i` 的加载画面**结构字段**别碰，只改它引用的 **wts 文本**（§三.2）。

## 五、神之墓地连错三版的根因（重点，别重犯）

**症状**：补丁版本一进图就弹回创建游戏界面，信息面板全空。

**当时错在哪**：我手上有几张「能进」的对照图（E1/E3/E5），就把它们当作「补丁是安全的」的证据，
推出「是加载画面文字导致弹回」，然后连做三版都只改加载文字 —— 全废。

**真相**：那些「能进」的图**根本没运行补丁代码**（原图原样返回，或只插了一个空函数）。
它们「能进」什么也证明不了。实际是**两个独立病因同时存在**：

| 病因 | 症状 | 修法 |
|---|---|---|
| JASS 局部变量遮蔽地图全局 | 编译器拒绝 → 弹回 | 局部变量全加 `kfe` 前缀 |
| ~~往 w3i 加载画面写文字/标题~~ | 进图崩 WEPlayerData → 弹回 | **别碰 w3i 字段**；要改走 **wts 文本**（§三.2，2026-09-16 修正） |

**通用教训**：**对照图必须真的跑了你要断言的那个变量**。
对照图只是原图/空函数 → 它「能进」不能证明功能代码安全。
（已写进 `systematic-debugging` 技能 Phase 3 第 4 条。）

**取证捷径**：崩溃弹窗里 `Object: XXXXXXXX` 那一行直接点名崩在哪个子系统
（`WEPlayerData` = w3i 玩家数据），别只看「创建游戏失败」这几个字。

### 补充：我自己的诊断失误（2026-09-16）

第一版只解了 MPQ 容器锁就交付，用户回「无法创建，还是弹回」。
**失误点**：我说过「第二把锁可能是 native」，但**搁置了没去处理**就交付，
等于让用户替我做真机验证、白试一版。

**硬规则**：明确识别出「还有一层可能的锁」时，
**要么先解决它，要么在交付时明确标注「这一层没验证、可能需要再试一版」**，
不能默默跳过。

### 补充二：把工具的报警当「误报」——最贵的失误（2026-09-17）

曹操Ⅱ 连崩多版，真因（`//` 注释吞代码，见 §409）**早就在证据里**：
pjass 报 `Parse successful: 7944 lines`，而脚本真实有 **13813 行**。
**我却在笔记里写下「pjass 行数 7944 为误报」，然后继续去找别的原因 —— 白耗好几轮。**

**元教训（比技术细节更重要）**：
> **工具报出的「数字对不上」（行数 / 字节数 / 计数 / 校验和），先当证据，不要先当噪声。**
> 一个我明确看到、却解释不了的数字，比一条我猜出来的假设值钱得多。

配套纪律：
1. **凡是"解析/编译通过"的判据，都要核对产物规模**：行数、字节数、条目数。
   `Parse successful` 只说明「解析到的地方没语法错」，**不说明解析完了**。
2. **权威工具的结论不要用自己写的解析器去推翻**。本次我用自写解析器
   「证明」w3a 有问题、花多轮排查，而 StormLib（暴雪官方参考实现）和 pjass 一照就清楚。
3. **排查顺序：先跑权威工具，再读它们的原始输出（含数字）**，最后才自己写解析器。

## 六、成品位置与工具链

### 成品

- 神之墓地：`/projects/n_testS1_safe.w3x`（主，用户实测通过）、`shenzhimudi303_cheat_v4.w3x`（正式名）。
  对照图 `n_testS2_title.w3x`、`n_testS4_alt.w3x`。说明 `神之墓地三件套-根因说明.md`。
- 守卫剑阁：`/projects/guardsword_zhtx26_cheat_v2.w3x`（用户实测通过）。
- **卢沟桥2026-正式版1.9**（80对战平台图，脱平台）：`luogouqiao2026_v19_unlocked.w3x`
  （用户实测通过；只解锁+改名，**未打三件套**）。
- **人族无敌2.5X**（网易对战平台图，全解锁）：`人族无敌2.5X-全解锁.w3x`
  （8 项天赋全体默认拥有 + 破平台验证 + 改名；native 用「空实现桩」手法）。
  归档：`~/.openhands/archive/rw25x-unlock/`
- 归档：`~/.openhands/archive/2026-09-13-war3改图三件套/`（成品 + 构建脚本 + 说明）。

### 工具链（卢沟桥那次沉淀，可直接复用）

| 文件 | 作用 |
|---|---|
| `work/mpqrepack.py` | 最小 MPQ v1 **手术式重打包**：`read_archive` / `decode_block` / `compress_to_sectors` / `encrypt` / `crypt` / `hash_string`。含 `(attributes)` 重建 |
| `work/extract_fixed.py` | `decrypt_exact`（**4 字节对齐**修正，破自定义密钥用） |
| `work/build.py` | 一键：解锁 +（`KFE_CHEAT=1` 时）三件套 + 改名/简介/加载画面 |
| `work/selfcheck.py <基图> <成品> <期望名> <期望简介>` | 交付前**必跑**，7 项全绿 |

**技能目录自带（跨项目可用，别在各工作区重复找）**：

| 文件 | 作用 |
|---|---|
| `~/.openhands/skills/war3-map-cheats/scripts/api124.py` | **1.24 版本门禁**（§零之前）。补丁引入新符号时**唯一**硬证据 |
| `…/scripts/native_check.py` | **必检项③**：脚本自声明 native 是否真实（平台图判据） |
| `…/scripts/rt_api124.py` | 门禁回归测试，改判据后必跑（A/B/C/D 四组） |
| `…/scripts/make_samples.py` | 生成回归样例（v8 负样例按已记录根因派生） |
| `…/scripts/extract_j.py` | 提 `war3map.j`，`--batch` 批量 |
| `…/scripts/{maprepack,mpqrepack}.py` | MPQ 读/写依赖（能解自定义密钥加密成员） |
| `…/scripts/ref/{common.j,Blizzard.j}` | jassdoc 副本，**只读 `@patch`** |

> 用法示例：
> ```bash
> S=~/.openhands/skills/war3-map-cheats/scripts
> python3 $S/extract_j.py 原图.w3x samples/base.j
> python3 $S/api124.py work/patched_war3map.j samples/base.j
> python3 $S/native_check.py 成品.w3x
> ```

```bash
python3 work/build.py <原图> <输出.w3x>              # 解锁 + 改名/简介/加载画面
KFE_CHEAT=1 python3 work/build.py <原图> <输出.w3x>  # 再打无CD/无限蓝/P闪
python3 work/selfcheck.py <原图> <输出.w3x> '<期望名>' '<期望简介>'
```

### 其它踩过的坑（改图通用）

- **脚本可能混编码**：中文注释部分是 **GBK**，整体 `decode('utf-8')` 会炸。
  打补丁要**字节级**做，别整体转码。
- 构造 MPQ 时 **block table 忘了加密** → 读不出任何块（`crypt` 会统一处理，单写 `struct.pack` 就漏了）。
- 重新排版时 **sector table 偏移要自己算**，别沿用旧 `off`。
- **`mpqrepack.repack()` 假设 MPQ 从文件偏移 0 开始**（2026-09-16 踩了两次）。
  `.w3x` 前面有 **512 字节 `HM3W` 头**，直接把 `.w3x` 喂给 `repack()` 会把新 MPQ 头
  写到 HM3W 区域上，产物损坏（症状：`struct.error: unpack_from requires a buffer of at least N bytes`）。
  **正确姿势**：先 `raw[512:]` 存成 `work/bare.mpq` → 在**裸 MPQ** 上做手术 →
  最后自己拼回改过名的 512 头。`.w3x` 同样不能直接喂 `mpyq`（同理）。
- **pjass 报错时，第一件事是跑原脚本基线**（2026-09-16）。我改坏了 `then`
  （正则含 ` then` 但替换没带上），pjass 报 7 个错。先跑原脚本 →
  `Parse successful: 18060 lines` ⇒ 立刻确认是**我的 bug**，不是原图本来就不合法。
  **这个一次对照实验能定性，别连改三版去试。**
- **mpyq 读不了加密的 `(listfile)`**（报 `Encryption is not supported yet`）——
  它顺便可作「有没有加密成员」的探针。
- 独立交叉验证：`mpyq` 剥掉 512 字节 HM3W 头当**裸 MPQ** 读；`.w3x` 不能直接喂给 mpyq。
- **保护者可能留诱饵**：卢沟桥的明文块是**旧版脚本**（缺 12 个触发器），
  真身在加密块里 —— 交付前和加密块**比一比函数数量**。

### 加「聊天指令」这类功能补丁（2026-09-16 曹操Ⅱ v15 实测）

需求形状：输入 `++` 抬高视距、`--` 缩小视距。翻车点集中在**怎么把新代码塞进容器**。

- **先量一下「脚本块尾到下一块」有多大空隙**。老图（世界编辑器反复保存）通常在数据区留下
  大段空洞（本图脚本块后紧跟 **91KB 空洞**）。有空洞就**原地把脚本块往空洞里长**：
  只改这一块的 `csize/fsize`，**别的块的偏移一个都不动**。
  - 好处：`(listfile)` 是 `FIX_KEY` 加密（密钥 = hash(name) + **块偏移**），
    偏移不动 ⇒ 密钥继续有效，不用解开它、也不用重排容器。
  - 反面教材：`repack` 那种整体重排会把所有偏移挪走 ⇒ FIX_KEY 成员集体失效。
- **原地扩展后必须重写 block table**（`csize` 变了），**hash 表保持原字节**。
- **(attributes) 的 CRC 写回**：`version=100 / flags=1` ⇒ 8 字节头 + 70 个 uint32。
  改过谁就刷谁。**注意**：
  - 老图里 (attributes) 的某些项**本来就是陈旧的**（本图 wts 那项就对不上内容），
    说明魔兽**并不校验它** —— 但既然要动它，就顺手刷成正确值。
  - **重写 (attributes) 后一定要清掉 `FLAG_ENCRYPTED`/`FLAG_FIX_KEY`**（我漏过）：
    `flags` 还写着 0x00010200、实际内容却是明文，读取方按「先解密」走 → 直接读不出来。
    **自检必须把成品当独立文件重新解一遍**，而不是复用构建时的内存对象 —— 这个 bug 就是这么被抓到的。
- **绝对不要写 `//` 注释 —— 机制已实测确证（2026-09-17）**。
  本图脚本是**裸 CR（`\r`）换行**（13808 个 `\r`，仅 10 个 `\n`，且这 10 个 `\n` **全在前 6778 行**）。
  而 JASS 的 `//` 行注释**只以 `\n` 结束**。所以只要在**第 6778 行之后**写一个 `//`，
  它就把**后面到文件末尾的所有代码全部吞成注释** —— 其中包括 `endglobals`、`function main`
  和全部地图初始化 → **建立游戏瞬间闪退，静默无报错**。
  - 实测：我加了 4 行 `//中文注释`（落在第 7943 行）⇒ **5870 行被吞**（含 `main`、`endglobals`）。
  - **改成英文/ASCII 无效**：关键是有没有 `//`，不是编码。中文注释只是我恰好写的中文。
  - 原图与所有「能开」的版本，**`//` 计数恒为 0** —— 这是本图能开的隐含前提。
  - **两行判据（见 §四 自检清单）**：① `j.count(b'//') == 0`；
    ② **pjass 解析行数 == `j.count(b'\r')+1`**（不一致 = 有代码被吞）。
  - 同理：**写补丁前先量一下原脚本的换行符构成**（`\r` / `\n` / `\r\n` 各多少），别假设 `\r\n`。
- **`SetCameraField` 只对调用者自己的客户端生效**，多人局里别的玩家不受影响。
  但想让「只影响发指令的那个人」时，习惯性用 `if GetLocalPlayer() == kfeP then` 包一层更稳。
- **`GetCameraField(CAMERA_FIELD_TARGET_DISTANCE)` 可能返回 0**（地图从没设过该字段时）。
  先判断 `< 1000` 兜底成默认值，不然 `0 + 800` 会把人卡在最小视距。
- **原图 `globals` 段可能一个 `hashtable` 都没有**（本图 369 个全局里 0 个），
  想在补丁里按玩家存状态就得自己加一行 `hashtable udg_XXX=InitHashtable()`；
  或者干脆**不存状态**，改用「读当前相机距离再 ±800」（更短、更少依赖，本图最终采用）。
- **`TriggerRegisterPlayerChatEvent(t, Player(i), "++", false)` 的最后一个参数是
  「exactMatch」**：`false` = 只比较**开头**（聊天串前缀匹配），`true` = 全等。
  想「输入 ++ 就抬高」用 `false`。
- **一个触发器只注册一种字符串**（2026-09-16）。多个字符串挂同一个触发器技术上应该可行，
  但**本图 22 处注册全是「1 触发器 = 1 字符串」**，没有多串先例；而沙箱里**开不了图**，
  验证不了。既然没把握，就**照原图的模式写**（每个指令一个触发器 + `TriggerAddAction`），
  代价只是重复三段同样的 loop。**"能编译"不等于"行为对"，没有先例的写法要降级成有先例的写法。**
- **加「全图视野」不要自己发明**：先 `grep` 原图 —— 本图**自己就有**胜利时开全图的代码
  `CreateFogModifierRectBJ(true, GetEnumPlayer(), FOG_OF_WAR_VISIBLE, bj_mapInitialPlayableArea)`，
  直接复用同一套 native（`CreateFogModifierRect` + `FogModifierStart`）。原图已有 = 已被验证可用。
- **全图视野 / 迷雾涉及游戏同步状态，不要包在 `GetLocalPlayer()` 里**（会不同步 → 掉线）。
  相机视距（`SetCameraField`）才是纯本地客户端效果，两者处理方式不同。
  - 想开全图后还能关回来：把 fogmodifier 存进 hashtable（`SaveFogModifierHandle` /
    `HaveSavedHandle` / `LoadFogModifierHandle` / `RemoveSavedHandle`），
    再发一次同一指令就 `FogModifierStop` 并清掉句柄。
  - **要「主机一条指令，全体生效」**（2026-09-16）：
    * 判定主机：**先查这图哪几个槽位是 `MAP_CONTROL_USER`** —— `grep 'SetPlayerController' war3map.j`。
      本图 main 里把 `Player(0)~Player(5)` 设为 USER、`Player(9)(10)(11)` 设为 COMPUTER，
      所以 **Player(0) 就是主机槽**，用 `GetPlayerId(GetTriggerPlayer()) == 0` 判定即可，够用且最短。
      不要费劲去解析 `war3map.w3i` 的玩家数组 —— **本图 w3i 的玩家字段（next_slot 之后的布局）
      我按标准格式解出来是乱码**，说明该段布局和标准不一致，别在那儿耗时。
    * 遍历 `Player(0..11)` 逐个 `CreateFogModifierRect` + `FogModifierStart`，句柄按**玩家 id**
      存 hashtable（key 用 `kfeI` 而不是主机 id），关闭时同样遍历，并**用 `HaveSavedHandle(udg,0,2)`
      当「当前是否已开」的开关**（因为主机 id 固定是 0，可以拿它当状态位）。
    * 开关都用 `DisplayTextToForce(bj_FORCE_ALL_PLAYERS, ...)`，别用 `DisplayTextToPlayer`。
- **建视野用的矩形别自己 `GetWorldBounds()` 新建**（每次调用返回新 rect，反复开关会泄漏）。
  本图自带 `bj_mapInitialPlayableArea`（由 `InitBlizzard → InitMapRects` 初始化，
  而 `main` 里 `call InitBlizzard()` 在 `call KFE_Zoom_Init()` 之前，时机没问题），直接用它。
  **先 grep 原图有没有现成的 rect/全局变量，有就别造。**
- **F9 任务栏（Quest log）的文本不在 w3i 里**（w3i 只有地图名/作者/简介），而在 `war3map.j` 的
  `CreateQuestBJ(questType, title, desc, icon)` 里，文字多为 `TRIGSTR_xxxx` → 去 `war3map.wts` 查。
  类型常量：`0` = `bj_QUESTTYPE_REQ_DISCOVERED`（显示「必做」）、`2` = `bj_QUESTTYPE_OPT_DISCOVERED`
  （「可选」）、`1`/`3` 是 undiscovered 版。本图 13 条，`CreateQuestItemBJ` = 0（没有子项）。
  导出脚本：`work/quests.py`（`args_of` 要**按引号内的逗号不算分隔符**来切参数，本来图里
  图标路径 `ReplaceableTextures\CommandButtons\X.tga` 不含逗号但描述里可能有）。
- **⚠️ 原图 F9 文本会骗人，必须用脚本交叉验证**（2026-09-16）：本图「英雄出世」任务栏写着
  「满宠..不得购买..必须是红色玩家输入某密码**++**后才能得到」——实际上：
  1. 注册的聊天指令是 **`manchong`**（`TriggerRegisterPlayerChatEvent(gg_trg_manchong, ...)`），
     **根本没有 `++` 这条指令**；`++` 只是编辑器里那个 `TRIGSTR` 文案的过时占位符。
  2. 它注册给 **Player 0~5**（不只是「红色玩家」）。
  3. `Trig_manchong_Actions` 就是无条件 `CreateNUnitsAtLoc(1,'Efur', GetTriggerPlayer(), ...)`
     —— 没有任何金钱/前置条件判断。
  **教训：地图说明文本（F9/wts 简介）属于「玩家被告知的东西」，不是「代码做的事」。
  凡是要据此下结论（尤其是判断指令是否撞车、判断能不能获得某单位），一律回到脚本里核对。**
- **加聊天指令前，把原图注册的字符串完整列出来对照**：
  `grep 'TriggerRegisterPlayerChatEvent' war3map.j`。本图原图只注册了 7 个：
  `caocao.uuu9.com`(仅 Player0) / `-OUT` / `caocao` / `我要升级  ` / `514226QQ` /
  `钱钱拿来  ` / `manchong`。注意后三个带**尾随空格**，是地图编辑器自带的加空格习惯。
- **本图原脚本 0 处 `GetEventPlayerChatString`**：原图全靠 `GetTriggerPlayer()` 做事，
  从不去读聊天内容。所以我加的指令补丁是**全图第一处**读聊天字符串的地方
  （`GetEventPlayerChatString` 本身安全，这样写是为了少建几个触发器/函数）。
- **注册了非拉丁指令后，本图玩家就再也打不出中文了**：该图注册串全是纯 ASCII，
  引擎的 unicode 捕获只有「注册过非拉丁指令」时才启用。我加了 `++` 之后，
  **Player 1~5 打中文会被弹「无法识别指令」并吞掉** —— 但原图本来就注册了中文指令
  `我要升级  `/`钱钱拿来  `，说明这个代价加不加都存在，只是现在无法再靠「没注册非拉丁指令」来规避。
  想规避就把新指令**只注册给 Player(0) 之外的必要范围**，而不是 `Player(0..11)` 全上。
- **注意：本图原脚本 0 处 `GetLocalPlayer`**（`grep -c GetLocalPlayer war3map.j` = 0），
  整张图是全同步写的。给这种图加「相机视距」必然要引入第一处 `GetLocalPlayer`。
  这是 Blizzard 公认的相机本地化写法，但要意识到**这是全图唯一的本地化点**，
  是我自己引入的风险；更保守的替代方案是不用 `GetLocalPlayer`，改成「只给按下 ++/-- 的玩家
  调相机」（原生过滤器通常就这样，更稳但依赖原生行为）。

- **「技能放出来盖住整屏 / 挡住视线」的元凶是 `CinematicFadeBJ`（还有 `DisplayCineFilter`）**（2026-09-16 实测）：
  它整屏盖一张贴图。本图共 15 处，四个神兽技能各一张：
  `Trig_BAI`(白虎 `war3mapImported\11.tga`) / `Trig_QING`(青龙 `22.tga`) /
  `Trig_HONG`(朱雀 `33.tga`) / `Trig_HUANG`(玄武 `44.tga`)，另 11 处是 CameraMasks 黑白闪与结束画面 `1234.tga`。
  **先说清一点：`CreateImage` 数 0 不代表没有盖图** —— 本图 `CreateImage` = 0，盖图全靠 `CinematicFadeBJ`。
  去盖图就一条正则：
  `re.compile(rb'[ \t]*call CinematicFadeBJ\([^\r]*\)\r')` 全替换成
  `call DisplayCineFilter(false)\r`（**不是** `CinematicBlackOutBJ`，那个函数在 Blizzard.j 里根本不存在；
  原生 `DisplayCineFilter(false)` 才是 Blizzard 自己 `CinematicFadeBJ` 内部的收尾手段，只关滤镜不画图）。
  另外 `CinematicModeBJ(true)` 会加黑边+禁操作，本图 46 处；配合上面一起看，
  否则删完盖图还以为「黑边也是盖图」。

- **「魔法护盾挨打掉蓝」不是 bug，是机制**（2026-09-16 实测）：那是魔兽的 **Mana Shield**，
  用蓝顶伤害、每挡一点伤害扣一点蓝。**「无蓝」补丁改的是技能施放魔法消耗 `amcs`（施法时扣一次），
  管不到护盾的持续扣蓝** —— 两者是不同的东西。若要「蓝永远不减」，得另加一个周期补蓝的触发器：
  `TriggerRegisterTimerEvent(0.5, true)` + `GroupEnumUnitsOfPlayer` + `IsUnitType(u, UNIT_TYPE_HERO)` +
  `SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MAX_MANA))`。
  **这个补蓝触发器必须全同步，绝不能包在 `GetLocalPlayer()` 里**（会不同步掉线）。

- **⚠️ 改 JASS 时最容易踩的坑：Python 源码里的字符串字面量，真实 CR 会被规范成 LF**（2026-09-16 实测翻车）：
  本图脚本换行是**裸 CR**（`\r`，13208 个），而我把补丁用三引号放进 build 脚本时写的是**真实换行**，
  Python 解析源码时就把它变成了 LF，结果产物里出现裸 LF，自检 `j.index(b'\rfunction main')` 直接
  `ValueError: subsection not found`。
  **对策**：补丁文本写成**字面量 `\n` 两字符**，再在运行时 `.replace('\n', '\r')` 转 ——
  这就是原作者 build 脚本里 `PATCH2 = '''...'''.replace('\n', '\r')` 那句话的真正原因。
  顺带：**新补丁里不要写 `//` 注释**，原脚本通篇没有注释，万一被当行注释会吞掉代码。

- **「删掉某个英雄技能」要改 `war3map.w3u` 的 `uabi`，而且必须等长替换**（2026-09-16 实测）：
  用户说「司马懿的吸收魔法删掉」，`grep 吸收 war3map.j` = **0**，因为它是**英雄技能**
  （不是施法消耗）—— 在 w3u 里：`Hantuabi` 的值 `Aabs,A05P,AInv`。
  `Aabs` 就是魔兽原生「**吸收魔法**」（Absorb Mana，`atar=vulnerable,enemies,...`），
  全图只出现 1 次，所以定位很干脆：**先在 w3u 里 grep 技能 id，命中就说明是单位数据挂的**。
  **关键坑**：w3u 是二进制对象数据，`uabi` 是长度前缀字符串 ——
  **缩短字符串会让后面所有对象的字段整体错位，整张图的数据就废了**。
  正确做法是**等长替换**：把 `Aabs,`（5 字符）换成 `    ,`（4 空格 + 逗号），
  得到一个空技能位，魔兽会忽略它。改完的 w3u 解压后**长度一个字节都不差**（本图 46751 -> 46751），
  与基图的差异只有 4 个字节（就是那 4 个字符位置）。
  **别**改成 `A05P,AInv`（少 5 字节）—— 那正是会毁数据的做法。
  同理，**别把对象整个删掉**（count 字段、块大小、后续偏移全要跟着动，风险大得多）。

- **改 w3u/w3a 这类对象文件前，先分清「哪几个候选是用户要删的」**（2026-09-16 实测）：
  司马懿身上同时有 `Aabs`（吸收魔法）、`A05P`（基类 `ACmf` 法力护盾）、`AInv`（物品栏）。
  还有 `A05Q`（甄姬的「从敌人身上吸收魔法能量」）也带「吸收」二字，**很容易误删**。
  判定顺序：① 先按**单位**锁定（`Hantuabi` 唯一）→ ② 再看该串里哪个 id 的**基类/描述**对得上
  → ③ 用户说的是「吸收魔法」就删「吸收魔法」，**法力护盾是另一回事，别捎带删掉**。

- **w3a 对象结构的一个可靠经验（用于反查字段归属）**：非标准 w3a 里，
  相邻两个对象常表现为 `<基类4字节><新id4字节>` 紧挨在一起（如 `ACmf`+`A05P`、`ACsm`+`A05Q`），
  后面才是该对象的字段（`anam`/`atp1`/`aub1`）。**注意字段名后面还有 `03 00 00 00`（type=3）
  和 4 字节 level**，所以 `字段名 + 10 字节` 才是字符串起点；直接 `字段名 + 8` 会读出 `\x03` 噪声。
- **加指令前先查撞车**：`grep 'TriggerRegisterPlayerChatEvent'` 把原图已占用的字符串列出来
  （本图有 `-OUT / caocao / manchong / 514226QQ / caocao.uuu9.com / 我要升级 / 钱钱拿来`），
  确认新指令不在其中。顺带注意原图可能带**位置参数**版（`"我要升级  "` 带尾空格）。
- **`pjass` 要配一个反向对照**：拿一个故意调用不存在函数的假脚本跑一遍，
  确认它会报 `Undeclared function` —— 否则「Parse successful」不能证明任何事。
- **`war3map.wts` 的 TRIGSTR 是 CRLF + `STRING n\r\n{\r\n<内容>\r\n}`**，改简介要**原地等长**
  （新值更短时用 `\r` 填充，`\r` 在 wts 值里是填充/换行，不影响显示）。
- **查「某英雄怎么选」要查三处，不要只 grep 脚本**（2026-09-16）：
  英雄名**不在 `war3map.j` 里**。正确顺序：
  1. `war3map.w3u`（单位数据）—— 用 `work/w3obj.py --grep 许褚`。
     **`unam` 是编辑器名、`upro` 是「真名」（玩家看到的名字）**，两者常常不一样：
     本图许褚是 `unam=豪杰 / upro=许褚`。只搜 unam 会找错。
  2. 商店/酒馆的出售名单在**对象的 `useu`**（酒馆卖英雄）或 **`usei`**（商店卖物品）字段，
     值是逗号分隔的对象 id。本图 `nmrc`(剑过不留名) 卖 10 个英雄、`nmrd`(独步空舞) 卖 9 个。
  3. `war3map.j` 里 `CreateUnit(p,'nmrc',...)` 给出酒馆**坐标**；
     `TriggerRegisterTimerExpireEvent(gg_trg_xuanjiq, udg_jsq2)` + `StartTimerBJ(udg_jsq2,false,200.)`
     是**选人倒计时 200 秒**；到点 `Trig_xuanjiq_Actions` 把酒馆 `RemoveUnit` 掉 = 不能再选。
- **`war3map.w3u` 的对象布局不是标准布局**（2026-09-16）：修饰符前的填充字节不规整
  （**偶尔**重复一次对象 id，不是每次都有），严格逐字段解析一定会漂移、报「越界」。
  试了几轮都凑不出「恰好读完整个文件」的布局 —— 别再耗在这上面。
  **改成按字段名直接扫**：`4字节 oid + 字段名 + \x03\x00\x00\x00 + NUL 结尾的字符串`
  （`field` 前面的 oid 可能隔着 4~8 字节的对象头，往前找最近的 4 字节可打印块即可）。
  见 `work/w3obj.py`。字段值是 **UTF-8**。
- **`war3map.w3u` 里字符串的 atype 3 没有长度前缀，是 NUL 结尾**；
  别当成「u32 长度 + 内容」，否则第一个 `ua1g` 就会读出天文数字长度。
- **原图自带的单位既可作为「命名」也可作为「提示」**：本图 `Hmbr` 被同时当成剧情 NPC
  （`gg_unit_Hmbr_0010`，说话）和真英雄（`gg_unit_Hmbr_0437`）；`utub` 里还把「许褚」写成
  「许猪」。**搜的时候几种写法都要试**。


