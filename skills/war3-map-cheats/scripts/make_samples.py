# -*- coding: utf-8 -*-
"""生成 api124 回归测试的 A 组样例（可复现，不依赖历史文件）。

背景：v8（真机建图失败的那个版本）**已被回退覆盖，磁盘上已不存在**。
所以负样例按「已记录的真实根因」从 1.24 基图**派生**出来，而不是靠考古。

真实根因（2026-09-17 曹操Ⅱ v15 实测）：
    v8 为让「中毒跟随引擎打到的目标」，注册了
    `EVENT_PLAYER_UNIT_DAMAGED` + `GetEventDamageSource` + `GetEventDamage`。
    其中只有 `EVENT_PLAYER_UNIT_DAMAGED` 是 @patch 1.31，1.24 编译不过
    → pjass 0 错误（假绿灯）→ 真机「建图失败回退」。
    v7 / v9 无此符号 → 可开。

用法：
    python3 make_samples.py [基图.w3x]
    默认基图 ./samples/base.j（不存在时用 caocao2_v15_fixed (3).w3x 提取）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, 'samples')
DEFAULT_MAP = ('/home/openhands/workspace/project/313abb6528b84b1c8c66a6bfae1c8a34/'
               'caocao2_v15_fixed (3).w3x')

# 注入点选在 `function main` 之前，保证是合法的全局位置
ANCHOR = 'function main '


def load_base(map_path=None, sample_path=None):
    if sample_path and os.path.exists(sample_path):
        return open(sample_path, encoding='latin1').read()
    sys.path.insert(0, HERE)
    import extract_j
    os.makedirs(SAMPLES, exist_ok=True)
    dst = os.path.join(SAMPLES, 'base.j')
    extract_j.extract(map_path or DEFAULT_MAP, dst)
    return open(dst, encoding='latin1').read()


def inject_v8(base):
    """植入真实翻车版用到的那个 1.31 事件常量。"""
    inj = ('\nfunction kfeProbeV8 takes nothing returns nothing\n'
           '    local trigger t = CreateTrigger()\n'
           '    call TriggerRegisterPlayerUnitEvent(t, Player(0), '
           'EVENT_PLAYER_UNIT_DAMAGED, null)\n'
           'endfunction\n\n')
    i = base.find(ANCHOR)
    if i < 0:
        i = len(base)
    return base[:i] + inj + base[i:]


def main(map_arg=None):
    os.makedirs(SAMPLES, exist_ok=True)
    base = load_base(map_arg)
    open(os.path.join(SAMPLES, 'base.j'), 'w', encoding='latin1').write(base)
    for tag in ('v7', 'v9'):
        open(os.path.join(SAMPLES, tag + '.j'), 'w', encoding='latin1').write(base)
    open(os.path.join(SAMPLES, 'v8.j'), 'w', encoding='latin1').write(inject_v8(base))
    print('已生成 samples/{base,v7,v8,v9}.j（v8 = 基图 + EVENT_PLAYER_UNIT_DAMAGED）')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
