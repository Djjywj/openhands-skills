---
name: war3-map-cheats
description: 给魔兽争霸3 地图（.w3x）打「无CD / 无限蓝 / P闪」三件套补丁，以及改地图显示名、简介、加载画面。当用户说"帮我改个无CD 无限蓝 P闪的地图""这张图加作弊/改图""地图创建游戏失败/弹回""信息面板全空""地图名字改色"时使用。含两个必检项（JASS 变量遮蔽、w3i 加载画面文字）和一个已验证的构建自检流程。
---

# war3 改图：无CD / 无限蓝 / P闪 三件套

> 2026-09-13 完成。守卫剑阁-纵横天下 2.6 与神之墓地 3.0.3 贺岁版均已实测可用。
> 神之墓地连错三版，根因见第五节，**开工前先读第五节**。

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

## 三、两个必检项（少一个就弹回）

### 1. 局部变量命名：一律加前缀，禁止裸 `x` / `y`

混淆过的地图，全局变量是单字母，常见 `timer x`、`timerdialog y`。
补丁里写 `local real x` 会遮蔽它们 → 加载器报 `x shadows global variable` → **创建游戏失败/弹回**。

判定工具（必须 0 错）：

```bash
pjass +shadow wc3_common.j wc3_blizzard.j war3map.j
```

### 2. **绝不写 w3i 的加载画面「文字 / 标题 / 副标题」**

写非空的后果：进图崩溃，弹

```
This application has encountered a critical error: 内存资源不足，无法处理此命令。Object: WEPlayerData
```

`WEPlayerData` = 魔兽解析 w3i 玩家数据的那块。

**证据**：3.0.3 原图这三个字段本来就是空的；能正常玩的守卫剑阁 v2 也是空的。
⇒ **改图只改地图名 + 简介，不碰加载画面字符串。** 想在列表里区分就靠地图名。

## 四、构建与自检流程

1. 用 `mpqwrite.Writer` 打开基图，`mpq_enc.unpack` 取出 `war3map.j` / `war3map.w3i`。
2. 改 `war3map.j`（插补丁 + `call KFE_Init()`）、改 `war3map.w3i`（**只改名/简介**）。
3. `set_header_name()` 改 MPQ 头 0x08 的显示名。
4. `w.save(dst, compact=True)`。
5. **自检要验被改的那一项本身**：
   - pjass `+shadow` 错误数 = 0；
   - 读回来确认 w3i 里名字/简介真的变了（别只看「文件能打开」）；
   - 逐块抽检 MPQ：坏块 = 0；
   - 下载链接实测 HTTP 200（`curl -o /dev/null -w '%{http_code}'`，GET，HEAD 会 405）。
6. 只 `replace` 现有文件；**往 MPQ 加新文件会失败**（smpq / SFileAddFile 都不行）。

## 五、神之墓地连错三版的根因（重点，别重犯）

**症状**：补丁版本一进图就弹回创建游戏界面，信息面板全空。

**当时错在哪**：我手上有几张「能进」的对照图（E1/E3/E5），就把它们当作「补丁是安全的」的证据，
推出「是加载画面文字导致弹回」，然后连做三版都只改加载文字 —— 全废。

**真相**：那些「能进」的图**根本没运行补丁代码**（原图原样返回，或只插了一个空函数）。
它们「能进」什么也证明不了。实际是**两个独立病因同时存在**：

| 病因 | 症状 | 修法 |
|---|---|---|
| JASS 局部变量遮蔽地图全局 | 编译器拒绝 → 弹回 | 局部变量全加 `kfe` 前缀 |
| 往 w3i 加载画面写文字/标题 | 进图崩 WEPlayerData → 弹回 | 不碰加载画面字符串 |

**通用教训**：**对照图必须真的跑了你要断言的那个变量**。
对照图只是原图/空函数 → 它「能进」不能证明功能代码安全。
（已写进 `systematic-debugging` 技能 Phase 3 第 4 条。）

**取证捷径**：崩溃弹窗里 `Object: XXXXXXXX` 那一行直接点名崩在哪个子系统
（`WEPlayerData` = w3i 玩家数据），别只看「创建游戏失败」这几个字。

## 六、成品位置

- 神之墓地：`/projects/n_testS1_safe.w3x`（主，用户实测通过）、`shenzhimudi303_cheat_v4.w3x`（正式名）。
  对照图 `n_testS2_title.w3x`、`n_testS4_alt.w3x`。说明 `神之墓地三件套-根因说明.md`。
- 守卫剑阁：`/projects/guardsword_zhtx26_cheat_v2.w3x`（用户实测通过）。
- 归档：`~/.openhands/archive/2026-09-13-war3改图三件套/`（成品 + 构建脚本 + 说明）。
