# -*- coding: utf-8 -*-
"""常驻取证脚本 —— 替代 dig1..dig28 / show1..show9 那种「一个事实一个脚本」的写法。

背景（2026-09-17 实测）：改图那次对话写了 62 个一次性 .py（其中 dig 家族 28 个），
每个 = create + run = 2 次 LLM 往返 ≈ 28 分钟。同一形状命令最高重复 27 次。

用法（在**工作区根目录**跑，默认在 ./work/blk/ 找已解出的成员）：
    python3 probe.py blk                       # 一次性全量解包 ./*.w3x → work/blk/
    python3 probe.py blk 某图.w3x 输出目录      # 指定图与输出目录
    python3 probe.py j 8072 8138               # 打印 war3map.j 第 8072~8138 行
    python3 probe.py j --grep 'KFE_\\w+'        # 正则搜脚本，带行号
    python3 probe.py w3a A06H                  # 打印某技能的 w3a 全字段
    python3 probe.py w3u Hmbr                  # 打印某单位的 w3u 全字段
    python3 probe.py w3t I01H                  # 打印某物品的 w3t 全字段
    python3 probe.py grep KFE_Multi            # 全成员关键字计数
    python3 probe.py cmp 基图.w3x 成品.w3x      # 逐成员比对（证明「没动的真的没动」）
    python3 probe.py list                      # 列出 work/blk/ 里已解出的成员
"""
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BLK = 'work/blk'
DEFAULT_MEMBERS = ['war3map.j', 'war3map.w3i', 'war3map.wts', 'war3map.w3u',
                   'war3map.w3a', 'war3map.w3t', 'war3map.w3h', 'war3map.w3q',
                   'war3map.w3d', 'war3map.w3b', 'war3map.w3c', 'war3map.wtg',
                   'war3map.wct', 'war3map.wpm', 'war3map.shd', 'war3map.doo',
                   'war3mapUnits.doo', 'war3map.mmp', '(listfile)']


# ---------------------------------------------------------------- 解包

def cmd_blk(args):
    import maprepack as R
    src = args[0] if args else None
    if not src:
        cands = [f for f in os.listdir('.') if f.lower().endswith('.w3x')]
        if len(cands) != 1:
            sys.exit('根目录有 %d 个 .w3x，请显式指定：probe.py blk 某图.w3x' % len(cands))
        src = cands[0]
    out = args[1] if len(args) > 1 else BLK
    os.makedirs(out, exist_ok=True)
    arch = R.read_archive(src)
    ok = bad = 0
    for n in DEFAULT_MEMBERS:
        try:
            data = R.read_member(arch, n)
            open(os.path.join(out, n), 'wb').write(data)
            print('  ✅ %-22s %8d 字节' % (n, len(data)))
            ok += 1
        except Exception as e:
            print('  ⚠  %-22s 读不出（%s）' % (n, type(e).__name__))
            bad += 1
    if bad:
        print('\n注：`(listfile)` 读不出是**正常现象** —— 它常被作者的密钥加密，'
              '不是脚本坏了。\n    成员清单请从**同类基图**已解出的 (listfile) 取，'
              '或用 scripts/extract_fixed.py 解自定义密钥。')
    print('\n%s → %s/：成功 %d，读不出 %d' % (src, out, ok, bad))
    print('之后所有取证都读 %s/，**不要再 open 地图**。' % out)


def load(name):
    p = os.path.join(BLK, name)
    if not os.path.exists(p):
        sys.exit('缺 %s —— 先跑：python3 probe.py blk' % p)
    return open(p, 'rb').read()


def jav():
    return load('war3map.j').decode('latin1')


def lines(d):
    return d.replace('\r\n', '\n').replace('\r', '\n').split('\n')


# ---------------------------------------------------------------- 脚本

def cmd_j(args):
    j = jav()
    if args and args[0] == '--grep':
        pat = re.compile(args[1])
        for i, ln in enumerate(lines(j), 1):
            if pat.search(ln):
                print('%6d | %s' % (i, ln.strip()[:200]))
        return
    a = int(args[0]) if args else 1
    b = int(args[1]) if len(args) > 1 else a
    L = lines(j)
    print('war3map.j 共 %d 行，// 出现 %d 次（本图 CR 换行下必须为 0）'
          % (len(L), j.count('//')))
    for i in range(a - 1, min(b, len(L))):
        print('%6d | %s' % (i + 1, L[i][:220]))


# ---------------------------------------------------------------- 对象表

def parse_obj(d, optional_ints=True):
    """w3a/w3u/w3t 共用格式，严格照抄 HiveWE 的 load_modification_table。"""
    def u32(p):
        return struct.unpack_from('<I', d, p)[0]
    p, version, tables = 0, u32(0), []
    p = 4
    for _ in range(2):
        cnt = u32(p); p += 4
        objs = []
        for _ in range(cnt):
            oid, mid = d[p:p + 4], d[p + 4:p + 8]; p += 8
            if version >= 3:
                p += 8
            nmod = u32(p); p += 4
            fields = []
            for _ in range(nmod):
                fid = d[p:p + 4]; typ = u32(p + 4); p += 8
                lv = dp = None
                if optional_ints:
                    lv, dp = u32(p), u32(p + 4); p += 8
                if typ == 0:
                    val = struct.unpack_from('<i', d, p)[0]; p += 4
                elif typ in (1, 2):
                    val = struct.unpack_from('<f', d, p)[0]; p += 4
                elif typ == 3:
                    e = d.find(b'\x00', p)
                    val = d[p:e]; p = e + 1
                else:
                    raise ValueError('type=%d 非法 @%d' % (typ, p))
                p += 4                       # end_token
                fields.append((fid.decode('latin1'), typ, lv, val))
            objs.append((oid.decode('latin1'), mid.decode('latin1'), fields))
        tables.append(objs)
    return version, tables, p


def show_obj(args, member, optional_ints):
    if not args:
        sys.exit('用法：probe.py %s <对象id>' % member.split('.')[-1])
    want = args[0]
    d = load(member)
    version, tables, end = parse_obj(d, optional_ints)
    print('%s  version=%d  表1=%d 对象  表2=%d 对象  解析到 %d/%d 字节 %s\n'
          % (member, version, len(tables[0]), len(tables[1]), end, len(d),
             '✅' if end == len(d) else '❌ 差 %d' % (len(d) - end)))
    hit = 0
    for ti, t in enumerate(tables):
        for oid, mid, fields in t:
            if want not in (oid, mid, oid + '|' + mid):
                continue
            hit += 1
            print('表%d  oid=%s  mid=%s  字段 %d 个' % (ti, oid, repr(mid), len(fields)))
            for fid, typ, lv, val in fields:
                v = val.decode('utf-8', 'replace') if isinstance(val, bytes) else val
                print('    %-6s type=%d lv=%-4s %r' % (fid, typ, lv, v))
            print()
    if not hit:
        print('未找到 %r。可用 grep 子命令先确认 id 存在。' % want)


def cmd_w3a(args):
    show_obj(args, 'war3map.w3a', True)


def cmd_w3u(args):
    show_obj(args, 'war3map.w3u', False)


def cmd_w3t(args):
    show_obj(args, 'war3map.w3t', False)


# ---------------------------------------------------------------- 其它

def cmd_grep(args):
    if not args:
        sys.exit('用法：probe.py grep <关键字>（中文会同时按 UTF-8 与 GBK 各试一次）')
    pats = {args[0].encode('utf-8')}
    try:
        pats.add(args[0].encode('gbk'))
    except UnicodeEncodeError:
        pass
    for n in sorted(os.listdir(BLK)):
        d = open(os.path.join(BLK, n), 'rb').read()
        c = sum(d.count(p) for p in pats)
        if c:
            print('  %-22s %6d 次' % (n, c))


def cmd_cmp(args):
    import maprepack as R
    if len(args) < 2:
        sys.exit('用法：probe.py cmp <基图.w3x> <成品.w3x>')
    a, b = R.read_archive(args[0]), R.read_archive(args[1])
    names = [n for n in DEFAULT_MEMBERS if n != '(listfile)']
    same = diff = fail = 0
    print('%-24s %s' % ('成员', '结论'))
    for n in names:
        try:
            x, y = R.read_member(a, n), R.read_member(b, n)
        except Exception:
            fail += 1
            print('  %-22s 读取失败' % n)
            continue
        if x == y:
            same += 1
        else:
            diff += 1
            print('  %-22s ★ 不同（%d → %d 字节）' % (n, len(x), len(y)))
    print('\n改动 = %d，未变 = %d，读取失败 = %d' % (diff, same, fail))


def cmd_list(args):
    if not os.path.isdir(BLK):
        sys.exit('还没有 %s/ —— 先跑：python3 probe.py blk' % BLK)
    for n in sorted(os.listdir(BLK)):
        print('  %-24s %9d' % (n, os.path.getsize(os.path.join(BLK, n))))


def cmd_selftest(args):
    """合成一份最小 w3u/w3a 复刻真实字节布局，验证解析器与对象查找。

    覆盖三个会静默出错的地方：① version>=3 多出的 8 字节 ② 常规对象 mid=NUL
    ③ 字符串字段的 NUL 结尾与 end_token。不碰任何地图文件。
    """
    def u32(x):
        return struct.pack('<I', x)

    def obj(oid, mid, fields):
        b = oid + mid + u32(len(fields))
        for fid, typ, val in fields:
            b += fid + u32(typ)
            if typ == 3:
                b += val + b'\x00'
            else:
                b += struct.pack('<f' if typ in (1, 2) else '<i', val)
            b += b'\x00\x00\x00\x00'
        return b

    for ver, optional_ints in ((2, False), (2, True), (3, False), (3, True)):
        pad = b'\x00' * 8 if ver >= 3 else b''

        def obj(oid, mid, fields):
            # 对象 = oid(4) + mid(4) [+ v3: 8 字节] + nmod(4) + 字段们
            b = oid + mid + pad + u32(len(fields))
            for fid, typ, val in fields:
                b += fid + u32(typ)
                if optional_ints:          # w3a 有 level_variation + data_pointer
                    b += u32(0) + u32(0)
                b += val + b'\x00' if typ == 3 else struct.pack(
                    '<f' if typ in (1, 2) else '<i', val)
                b += b'\x00\x00\x00\x00'   # end_token —— 漏掉它就会整表错位
            return b

        # 表1 = 常规对象（mid 为 4 个 NUL），表2 = 自定义对象（mid = 作者新 id，oid = 基类）
        d = u32(ver) + u32(1) + obj(b'Rooo', b'\x00\x00\x00\x00',
                                    [(b'unam', 3, b'x'), (b'uhpm', 0, 100)]) \
            + u32(1) + obj(b'Efur', b'CSTM', [(b'uabi', 3, b'AInv,Aspo')])
        version, tables, end = parse_obj(d, optional_ints)
        assert end == len(d), 'v%d/%s 解析未铺满：%d vs %d' % (ver, optional_ints, end, len(d))
        got = {o[0]: o for t in tables for o in t}
        assert set(got) == {'Rooo', 'Efur'}, got.keys()
        f = {x[0]: x[3] for x in got['Rooo'][2]}
        f = {k: (v.decode() if isinstance(v, bytes) else v) for k, v in f.items()}
        assert f == {'unam': 'x', 'uhpm': 100}, f
        assert got['Rooo'][1] == '\x00\x00\x00\x00' and got['Efur'][1] == 'CSTM'
        assert got['Efur'][0] == 'Efur'   # 自定义对象：oid=基类单位, mid=作者新 id
        assert len(tables[0]) == 1 and len(tables[1]) == 1, [len(x) for x in tables]
    print('✅ probe.selftest 通过（v2/v3 × optional_ints 四种组合）')


CMDS = {'blk': cmd_blk, 'j': cmd_j, 'w3a': cmd_w3a, 'w3u': cmd_w3u, 'w3t': cmd_w3t,
        'grep': cmd_grep, 'cmp': cmd_cmp, 'list': cmd_list, 'selftest': cmd_selftest}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(0 if len(sys.argv) < 2 else 1)
    CMDS[sys.argv[1]](sys.argv[2:])
