# -*- coding: utf-8 -*-
"""api124.py 的回归测试（改动判据后必跑）。

四类用例，全部自包含（不依赖某个工作区路径）：
  A. 真机真值对照 base/v7/v8/v9 —— 样例在 samples/，缺失时用 --maps 从地图现提
  B. 类型名漏检（本工具修过的真实 bug）
  C. 假报警（注释里的符号不该报；假报警会训练人忽略工具，同样是病）
  D. 合法性不误伤（1.24a 才有的 hashtable 全家桶必须放行）

真值来源（2026-09-17 曹操Ⅱ v15 真机实测）：
    base 原图 / v7 / v9 = 能开；v8（注册了 EVENT_PLAYER_UNIT_DAMAGED）= 建图失败。

用法：
    python3 rt_api124.py
    python3 rt_api124.py --maps base=图A.w3x,v8=图B.w3x   # 从地图现提样例
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(HERE, 'api124.py')
SAMPLES = os.path.join(HERE, 'samples')
fails = []


def run_api(src_text):
    open('/tmp/_rt.j', 'w').write(src_text)
    return subprocess.run([sys.executable, API, '/tmp/_rt.j'],
                          capture_output=True, text=True, timeout=600).returncode


def ensure_samples(maps_arg):
    """A 组需要 base/v7/v8/v9；缺失时从 --maps 提取。"""
    need = ('base', 'v7', 'v8', 'v9')
    have = {t: os.path.join(SAMPLES, t + '.j') for t in need
            if os.path.exists(os.path.join(SAMPLES, t + '.j'))}
    if maps_arg:
        os.makedirs(SAMPLES, exist_ok=True)
        sys.path.insert(0, HERE)
        import extract_j
        for item in maps_arg.split(','):
            tag, path = item.split('=', 1)
            extract_j.extract(path.strip(), os.path.join(SAMPLES, tag + '.j'))
            have[tag] = os.path.join(SAMPLES, tag + '.j')
    return have


def case_a(have):
    truth = {'base': 0, 'v7': 0, 'v8': 1, 'v9': 0}
    print('--- A. 真机真值对照 ---')
    if len(have) < 4:
        print('   ⏭ 样例不足（缺 %s），跳过。用 --maps base=..,v7=..,v8=..,v9=.. 提供'
              % ','.join(t for t in truth if t not in have))
        return
    for tag, want in truth.items():
        r = subprocess.run([sys.executable, API, have[tag]],
                           capture_output=True, text=True, timeout=600)
        ok = r.returncode == want
        print('   %-5s exit=%d 期望=%d %s' % (tag, r.returncode, want, '✅' if ok else '❌'))
        if not ok:
            fails.append('A/' + tag)


def case_b():
    print('--- B. 1.30+ 类型名（曾漏检）---')
    body = 'function F takes nothing returns nothing\n    local %s kfeV = null\nendfunction\n'
    for ty in ('framehandle', 'animtype', 'originframetype', 'commandbuttoneffect'):
        rc = run_api(body % ty)
        ok = rc == 1
        print('   %-20s exit=%d %s' % (ty, rc, '✅ 抓到' if ok else '❌ 漏检'))
        if not ok:
            fails.append('B/' + ty)


def case_c():
    print('--- C. 注释里的符号（不该报）---')
    for label, src in (
        ('行注释', 'function F takes nothing returns nothing\n'
                   '    // EVENT_PLAYER_UNIT_DAMAGED\n    set i = 0\nendfunction\n'),
        ('块注释', 'function F takes nothing returns nothing\n'
                   '    /* BlzGetUnitArmor framehandle */\n    set i = 0\nendfunction\n'),
    ):
        rc = run_api(src)
        ok = rc == 0
        print('   %-8s exit=%d %s' % (label, rc, '✅ 未误报' if ok else '❌ 误报'))
        if not ok:
            fails.append('C/' + label)


def case_d():
    print('--- D. 1.24a 合法 API（不该报）---')
    body = ('function F takes nothing returns nothing\n'
            '    local hashtable kfeH = InitHashtable()\n'
            '    local integer kfeI = GetHandleId(kfeH)\n'
            '    call SaveInteger(kfeH, 0, 1, 2)\n'
            '    if HaveSavedInteger(kfeH, 0, 1) then\n'
            '        set kfeI = LoadInteger(kfeH, 0, 1)\n'
            '    endif\n'
            'endfunction\n')
    rc = run_api(body)
    ok = rc == 0
    print('   hashtable 全家桶 exit=%d %s' % (rc, '✅ 放行' if ok else '❌ 误伤'))
    if not ok:
        fails.append('D/hashtable')


if __name__ == '__main__':
    maps = sys.argv[sys.argv.index('--maps') + 1] if '--maps' in sys.argv else None
    print('=' * 66)
    print('api124.py 回归测试')
    print('=' * 66)
    case_a(ensure_samples(maps))
    case_b()
    case_c()
    case_d()
    print()
    if fails:
        print('❌ 失败 %d 项：%s' % (len(fails), fails))
        sys.exit(1)
    print('✅ 全部通过')
