# -*- coding: utf-8 -*-
"""改写地图内部成员（MPQ）的公共工具。

本图绝大多数成员都是「压缩 + 文件名派生密钥加密」，且部分块带 FIX_KEY
（解密密钥含自身偏移，重排后会解不开）—— 所以不能简单整盘重写。

对外只有两个函数：
    read_member(arch, name)                 解出成员明文
    rewrite(arch, {name: bytes}, dst)       按原标志/原密钥写回，并同步
                                            (attributes) 里对应的 CRC32

(attributes) 的格式：偏移 8 起，每个块一个 uint32 CRC32，按块序号排列。
改了哪个成员就必须刷新它的 CRC，否则游戏判定地图损坏。
"""
import os
import struct
import zlib

import mpqrepack as M

read_archive = M.read_archive
find_block_for = M.find_block_for
hash_string = M.hash_string


def read_member(arch, name):
    ss = 512 << arch['hdr']['sector_size_shift']
    bi = M.find_block_for(arch, name)
    b = arch['blocks'][bi]
    raw = M.read_block_data(arch, b)
    if not (b['flags'] & M.FLAG_ENCRYPTED):
        return M.decode_block(raw, b, ss)[:b['fsize']]
    base = M.hash_string(os.path.basename(name), 3)
    if b['flags'] & M.FLAG_FIX_KEY:
        base = (base + b['off']) & 0xFFFFFFFF
    nsec = b['fsize'] // ss + 1
    for k in (base, (base + 1) & 0xFFFFFFFF, (base - 1) & 0xFFFFFFFF):
        try:
            offs = list(struct.unpack_from(
                '<%dI' % (nsec + 1), M.decrypt(raw[:(nsec + 1) * 4], (k - 1) & 0xFFFFFFFF), 0))
            if offs[0] != (nsec + 1) * 4 or not offs[0] < offs[-1] <= b['csize']:
                continue
            out = b''
            for i in range(nsec):
                ch = M.decrypt(raw[offs[i]:offs[i + 1]], (k + i) & 0xFFFFFFFF)
                out += zlib.decompress(ch[1:]) if ch[:1] == b'\x02' else ch[1:]
            if len(out) >= b['fsize']:
                return out[:b['fsize']]
        except Exception:
            continue
    raise RuntimeError('%r 解密失败' % name)


def rewrite(path, changes, dst, verbose=True):
    """changes: {成员名: 新明文字节}；自动刷新 (attributes) 的 CRC 并整盘重排。"""
    arch = M.read_archive(path)
    ss = 512 << arch['hdr']['sector_size_shift']
    raw = bytearray(arch['raw'])
    blocks = [dict(b) for b in arch['blocks']]

    idx = {nm: M.find_block_for(arch, nm) for nm in changes}
    if verbose:
        print('=== 改写成员 ===')
        for nm, i in idx.items():
            b = arch['blocks'][i]
            print('  %-16s 块%-4d 旧 fsize=%-8d 新 fsize=%-8d %s'
                  % (nm, i, b['fsize'], len(changes[nm]),
                     '✅ 加密' if b['flags'] & M.FLAG_ENCRYPTED else '⚠ 明文'))

    attr_i = M.find_block_for(arch, '(attributes)')
    attr = bytearray(read_member(arch, '(attributes)'))
    for nm, new in changes.items():
        i = idx[nm]
        old = struct.unpack_from('<I', attr, 8 + 4 * i)[0]
        new_crc = zlib.crc32(new) & 0xFFFFFFFF
        struct.pack_into('<I', attr, 8 + 4 * i, new_crc)
        if verbose:
            print('  (attributes) 块%-4d CRC %08x → %08x' % (i, old, new_crc))
    attr = bytes(attr)

    KEYS = {nm: M.find_bound_key(arch, nm, ss) for nm in list(changes) + ['(attributes)']}
    if verbose:
        for nm, k in KEYS.items():
            h = M.hash_string(nm, 3)
            print('  密钥 %-16s 绑定=%-11d hash=%-11d %s'
                  % (nm, k, h, '✅' if k == h else '⚠ 差 %d' % (k - h)))

    content = {i: bytes(arch['raw'][arch['base'] + b['off']: arch['base'] + b['off'] + b['csize']])
               for i, b in enumerate(blocks)}
    for nm, new in changes.items():
        content[idx[nm]] = M.sectors_for(nm, blocks[idx[nm]], new, ss, KEYS[nm])
    content[attr_i] = M.sectors_for('(attributes)', blocks[attr_i], attr, ss, KEYS['(attributes)'])

    PIN = {i: b['off'] for i, b in enumerate(blocks) if b['flags'] & M.FLAG_FIX_KEY}
    for i in sorted(PIN):
        if verbose:
            print('  ⚠ 块 %d 带 FIX_KEY → 钉在原位 off=%d' % (i, PIN[i]))

    region_lo, region_hi = 32, arch['hdr']['hash_table_offset']
    cursor, new_off = region_lo, {}
    pinned = sorted((off, off + blocks[i]['csize']) for i, off in PIN.items())
    for i in range(len(blocks)):
        if i in PIN:
            new_off[i] = PIN[i]
            continue
        c = len(content[i])
        if cursor % 512:
            cursor += 512 - cursor % 512
        for lo, hi in pinned:
            if cursor < hi and cursor + c > lo:
                cursor = (hi + 511) // 512 * 512
        if cursor + c > region_hi:
            raise RuntimeError('放不下：块 %d 需 %d 字节，游标 %d > %d' % (i, c, cursor, region_hi))
        new_off[i] = cursor
        cursor += c

    buf = bytearray(region_hi - region_lo)
    for i in range(len(blocks)):
        o = new_off[i] - region_lo
        buf[o:o + len(content[i])] = content[i]
    raw[arch['base'] + region_lo: arch['base'] + region_hi] = buf

    for i, b in enumerate(blocks):
        b['off'] = new_off[i]
        b['csize'] = len(content[i])
    for nm, new in changes.items():
        blocks[idx[nm]]['fsize'] = len(new)
    blocks[attr_i]['fsize'] = len(attr)

    spans = sorted((b['off'], b['off'] + b['csize']) for b in blocks)
    for a, z in zip(spans, spans[1:]):
        assert a[1] <= z[0], '重排后重叠 %s vs %s' % (a, z)
    assert all(b['off'] + b['csize'] <= region_hi for b in blocks), '块越出数据区'

    bt = b''.join(struct.pack('<IIII', x['off'], x['csize'], x['fsize'], x['flags']) for x in blocks)
    raw[arch['base'] + arch['hdr']['block_table_offset']:
        arch['base'] + arch['hdr']['block_table_offset'] + len(bt)] = M.encrypt(bt, M.BLOCK_TABLE_KEY)
    assert len(raw) == len(arch['raw']), '文件长度必须不变'
    open(dst, 'wb').write(bytes(raw))
    if verbose:
        print('  重排 %d 块，用到 %d，余 %d 字节，无重叠 ✓' % (len(blocks), cursor, region_hi - cursor))
        print('  ✅ 已写出 %s（%d 字节）' % (dst, len(raw)))
    return arch
