# -*- coding: utf-8 -*-
"""必检项③：脚本自己声明的 native，魔兽标准库里是否真实存在？

【为什么必须单独查】pjass 会因为「脚本自己声明了这些 native」而放行 ——
所以 `pjass 通过 ≠ 真机能加载`。这些是平台专属 API（YDWE / 网易 DzAPI / 11平台），
由平台在**进程内存里**注册；脱离平台后魔兽编译脚本时找不到函数 → 无法创建、弹回。

【判据】
    脚本声明的 native 数 == 0   ⇒ 正规单机图
    脚本声明了一批标准库没有的 native ⇒ 平台图，脱离平台必弹回（除非按 §0.3 处理）

已知平台 API 前缀（看到就基本确定）：
    DzAPI_Map_*     网易官方对战平台
    EX*/EXGet*/EXSet*  YDWE（Everdream）japi
    RequestExtra*     yiyi / 11 平台数据请求
    UnitAlive        HcUnitAlive 第三方库（常为空壳、零调用）

用法：
    python3 native_check.py <地图.w3x>
    退出码 0 = 无平台 native；1 = 有（需要处理）
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DECL = re.compile(r'^\s*native\s+(\w+)\s+takes', re.M)

PLATFORM_HINT = ('DzAPI_', 'EX', 'RequestExtra', 'UnitAlive',
                 'Blz', 'SaveServerValue', 'GetServerValue')


def read_war3map_j(path):
    """用 maprepack 解成员（支持加密成员与自定义密钥，mpyq 做不到这一点）。

    踩过的坑：mpyq 读不了加密的 (listfile)，报
    `NotImplementedError: Encryption is not supported yet.` / 或 None 属性错误 ——
    所以**不要**拿 mpyq 当这里的兜底。本目录已自带 maprepack.py + mpqrepack.py。
    """
    import maprepack as R
    return R.read_member(R.read_archive(path), 'war3map.j')


def main(path):
    j = read_war3map_j(path)
    names = sorted(set(DECL.findall(j.decode('latin1', 'replace'))))
    print('地图：%s' % path)
    print('war3map.j %d 字节，回车符 %d 个，换行符 %d 个'
          % (len(j), j.count(b'\r'), j.count(b'\n')))
    print('脚本自己声明的 native：%d 个' % len(names))
    if not names:
        print('\n✅ 声明的 native 数 = 0 → 不是平台图，单机可加载')
        return 0
    plat = []
    for n in names:
        tag = ''
        if n.startswith('DzAPI_'):
            tag = '网易官方对战平台'
        elif n.startswith(('EXGet', 'EXSet', 'EXPause', 'EXExecute')):
            tag = 'YDWE japi'
        elif n.startswith('RequestExtra'):
            tag = 'yiyi/11平台'
        elif n.startswith(PLATFORM_HINT):
            tag = '平台/非标准'
        print('   %-36s %s' % (n, tag))
        plat.append((n, tag))
    print('\n⚠ 共 %d 个平台专属 native → 脱离平台必然「无法创建」' % len(plat))
    print('   处置（技能手册 §0.3）：把 native「声明 + 调用」一起摘掉，')
    print('   调用点多时改用「同名同签名的空实现」桩（调用点一行都不用改）。')
    print('   两种做法都要在交付时把退化点告知用户。')
    return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
