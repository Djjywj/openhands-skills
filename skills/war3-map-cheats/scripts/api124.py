# -*- coding: utf-8 -*-
"""1.24 版本门禁：禁止补丁引入 1.24 不存在的 API / 类型 / 常量。

★★ 这是本技能最重要的判据工具 —— 因为「pjass 通过」是假绿灯。★★

【为什么要它】
本机所有 common.j 都是 1.31/1.32 版。拿 1.32 库跑 pjass 校验 1.24 的图，
pjass 会**放行 1.24 根本不存在的 API** 并打印 `Parse successful`。实测：

    /tmp/pjass/pjass /tmp/jasslib/common.j /tmp/jasslib/Blizzard.j v8.j
    → Parse successful: 13845 lines（= 真实行数，连行数判据也过）← 假绿灯
    而 v8 真机结果 = 「建图失败回退」

v8 只多用了**一个**符号 `EVENT_PLAYER_UNIT_DAMAGED`（@patch 1.31.0.11889）。

【判据来源】
[lep/jassdoc](https://github.com/lep/jassdoc) 给每个声明标了 `@patch`（从哪版开始存在）。
另有本地副本 `work/ref/{common.j,Blizzard.j}`（只读 @patch，**绝不能拿去跑 pjass**）。

目标区间 **1.24 ~ 1.27**（用户 2026-09-17 明确要求），硬底线取最保守的 **1.24a**。
jassdoc 里落在 1.25/1.26/1.27 的符号数 = **0**（版本从 1.24a 直接跳到 1.29.0），
所以阈值 1.24a 恰好完整覆盖，无需为 1.25+ 放宽。

【判据优先级】本图先例 > 旧图先例 > 官方文档 > pjass。
本工具负责「官方文档」这一层；「本图先例」由 build 脚本里的 grep 断言负责（更硬）。

【已知盲区（实测探针得出结论，务必知情）】
  1. **变量/句柄类型名**：jassdoc 只给 `type` 声明和 native 参数类型标 @patch。
     脚本里写 `local <类型名> v` 时，未标注的参数类型名（如 `originframetype`
     只用作 framehandle 相关 native 的参数）可能落在覆盖之外。
     ⇒ 本工具改为**同时**收录所有出现过 ≥1 次的类型名（保守放行，靠下方第 2 条兜底）。
  2. **未标注的声明**：jassdoc 有少量声明没有 @patch。本工具对「无从判定」的符号
     采取**保守放行**，但会在报告里列出，供人工用「本图先例」复核。
  3. 本工具是**标识符级**判据，不认识语义（如「这个常量只在 1.31 的分支里用」）。

【防假报警（假报警会训练人忽略工具，同样是病）】
  - 先剥 `//` 行注释与 `/* */` 块注释，再扫标识符 → 注释里的符号不算数。
  - 字符串字面量单独处理：只在字符串里出现的符号**不算致命错误**（可能是
    `GetPlayerName(p) == "Blz..."` 这类比较），但会作为 ⚠ 提示列出。

用法：
    python3 api124.py <被检脚本.j> [基图脚本.j]
    退出码 0 = 通过；1 = 有 1.24 不存在的符号
    给了基图脚本时，额外报告「基图没有先例、且 1.24 也无法证明存在」的符号
"""
import os
import re
import sys

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ref')

MIN_OK = (1, 24, 0, 0, 'a')      # 硬底线：1.24a
WARN_MAX = (1, 27, 0, 0, '')     # 警示带上限：1.27

DECL_NATIVE = re.compile(r'\b(\w+)\s+(?:takes|returns)\b')
DECL_CONST = re.compile(r'^\s*constant\s+\w+\s+(\w+)\s*=')
DECL_TYPE = re.compile(r'^type\s+(\w+)\s+extends\b')
DECL_FUNC = re.compile(r'^function\s+(\w+)')


def parse_version(s):
    m = re.match(r'(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?([a-z]*)', s)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0),
            int(m.group(4) or 0), m.group(5) or '')


def vstr(v):
    return '.'.join(str(x) for x in v[:2])


def build_table():
    """从 jassdoc 建「符号 → 引入版本」表。返回 (table, 无标注符号集, 类型名集)。"""
    table, unpatch, types = {}, set(), set()
    for fn in ('common.j', 'Blizzard.j'):
        path = os.path.join(REF, fn)
        if not os.path.exists(path):
            continue
        patch = None
        for ln in open(path, encoding='utf-8', errors='replace'):
            m = re.search(r'@patch\s+([0-9][0-9a-zA-Z.]*)', ln)
            if m:
                patch = parse_version(m.group(1))
                continue
            name = None
            if 'native' in ln:
                m = DECL_NATIVE.search(ln)
                name = m.group(1) if m else None
            elif DECL_CONST.match(ln):
                name = DECL_CONST.match(ln).group(1)
            elif DECL_TYPE.match(ln):
                name = DECL_TYPE.match(ln).group(1)
                if patch is not None:
                    types.add(name)
            elif DECL_FUNC.match(ln):
                name = DECL_FUNC.match(ln).group(1)
            if name:
                if patch is None:
                    unpatch.add(name)
                else:
                    table.setdefault(name, patch)
                patch = None          # 一个 @patch 只作用于紧随其后的那条声明
    return table, unpatch, types


def strip_noise(text):
    """返回 (去注释后的文本, 字符串字面量列表)。"""
    strings = re.findall(r'"((?:[^"\\]|\\.)*)"', text)
    t = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)      # 块注释
    t = re.sub(r'//[^\n]*', ' ', t)                       # 行注释（本图裸 CR 下只到 '\n'）
    t = re.sub(r'"(?:[^"\\]|\\.)*"', '""', t)             # 字符串占位
    return t, strings


def scan(path, base_path=None):
    table, unpatch, types = build_table()
    raw = open(path, encoding='latin1').read()
    code, strings = strip_noise(raw)
    idents = set(re.findall(r'\b[A-Za-z_]\w{2,}\b', code))
    in_str = set()
    for s in strings:
        in_str.update(re.findall(r'\b[A-Za-z_]\w{2,}\b', s))

    illegal, band, noinfo = [], [], []
    for name in idents:
        v = table.get(name)
        if v is None:
            if name in unpatch:
                noinfo.append(name)
            continue
        if v[:5] <= MIN_OK:
            continue
        if v[:5] <= WARN_MAX:
            band.append((name, v))
        else:
            illegal.append((name, v))

    print('   jassdoc 版本表 %d 个符号（目标地图版本 1.24~1.27，硬底线 1.24a）' % len(table))
    base = open(base_path, encoding='latin1').read() if base_path else None

    # 只在字符串里出现的，降级为提示：可能是 GetPlayerName(p)=="X" 这类比较
    only_str = [n for n, _ in illegal if n in in_str and n not in idents - in_str]
    hard = [(n, v) for n, v in illegal if n not in only_str]

    print('   ❌ 1.24 不存在的 API：%d 个' % len(hard))
    for name, v in sorted(hard):
        extra = ''
        if base is not None and name not in base:
            extra = '  ← 基图无先例'
        print('      %-34s @patch %-8s → 1.24 无法加载%s' % (name, vstr(v), extra))
    if only_str:
        print('   ⚠ 只在字符串里出现（不阻断，人工确认）：%s' % ', '.join(sorted(only_str)[:10]))
    if band:
        print('   ⚠ 只在 1.25+ 可用（当前未阻断）：%d 个' % len(band))
        for name, v in sorted(band):
            print('      %-34s @patch %s' % (name, vstr(v)))
    unknown = []
    if base is not None:
        unknown = sorted(n for n in idents
                         if n not in table and n not in unpatch
                         and re.match(r'^[A-Z]', n) and n not in base)
        print('   ⚠ 基图无先例、jassdoc 也查不到的符号：%d 个' % len(unknown))
        for n in unknown[:15]:
            print('      %s' % n)
    if noinfo:
        print('   ⚠ jassdoc 未标 @patch 的符号（保守放行，需本图先例复核）：%d 个 %s'
              % (len(noinfo), sorted(noinfo)[:8]))
    return hard, unknown


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    base = sys.argv[2] if len(sys.argv) > 2 else None
    bad, unk = scan(sys.argv[1], base)
    print()
    if bad:
        print('❌ 不通过：%d 个符号在 1.24 不存在，真机必然建图失败' % len(bad))
        print('   处置：① 换成本图已有的等价玩法（本图先例优先）② 从补丁里摘掉该功能')
        sys.exit(1)
    print('✅ 通过：脚本用到的符号都在 1.24 的版本范围内')
