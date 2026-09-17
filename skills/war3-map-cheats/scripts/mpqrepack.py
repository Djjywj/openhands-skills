"""Minimal MPQ (v1) surgical repacker for Warcraft III maps.

Rebuilds an archive by copying every existing block byte-for-byte, replacing
the payload of one or more files, then re-laying-out the block table and
re-encrypting it. The hash table is copied verbatim (it carries name hashes,
not offsets), so unknown/protected file names are preserved.
"""
import hashlib
import struct
import zlib

# (attributes) integrity table: version+flags then three parallel arrays,
# indexed by block-table position, each present only if its flag bit is set.
ATTR_NAME = '(attributes)'
ATTR_CRC = 0x1
ATTR_FILETIME = 0x2
ATTR_MD5 = 0x4

# --- MPQ crypto (mirrors mpyq._decrypt; the transform is an involution) ---
def _build_crypt_table():
    seed = 0x00100001
    table = [0] * 0x500
    for idx in range(0x100):
        for i in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            a = (seed & 0xFFFF) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            b = seed & 0xFFFF
            table[idx + i * 0x100] = a | b
    return table

CRYPT_TABLE = _build_crypt_table()

def decrypt(data, key):
    """MPQ 表/扇区解密。

    ⚠️ 只处理完整的 4 字节字，尾部不足 4 字节原样保留，**输出长度必须与输入
    严格相同**。先前用 struct.unpack('<I', data[i:i+4].ljust(4)) 会让尾部
    补成一个整字，导致输出比输入长 —— 加密写盘时扇区偏移表与实际数据错位，
    StormLib / 游戏直接读不出该成员（错误码 1004），建图闪退。
    """
    out = bytearray(data)
    seed1 = key & 0xFFFFFFFF
    seed2 = 0xEEEEEEEE
    for i in range(0, len(data) & ~3, 4):
        seed2 = (seed2 + CRYPT_TABLE[0x400 + (seed1 & 0xFF)]) & 0xFFFFFFFF
        value = struct.unpack_from('<I', data, i)[0]
        value = (value ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed1 = (((~seed1) << 0x15) + 0x11111111) | (seed1 >> 0x0B)
        seed1 &= 0xFFFFFFFF
        seed2 = (value + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
        struct.pack_into('<I', out, i, value)
    return bytes(out)


def encrypt(data, key):
    """decrypt 的逆。同样只处理完整 4 字节字，输出长度与输入严格相同。"""
    out = bytearray(data)
    seed1 = key & 0xFFFFFFFF
    seed2 = 0xEEEEEEEE
    for i in range(0, len(data) & ~3, 4):
        plain = struct.unpack_from('<I', data, i)[0]
        seed2 = (seed2 + CRYPT_TABLE[0x400 + (seed1 & 0xFF)]) & 0xFFFFFFFF
        cipher = (plain ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed1 = (((~seed1) << 0x15) + 0x11111111) | (seed1 >> 0x0B)
        seed1 &= 0xFFFFFFFF
        seed2 = (plain + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
        struct.pack_into('<I', out, i, cipher)
    return bytes(out)


# kept for readability at call sites
crypt = decrypt

def hash_string(name, hash_type):
    """hash_type: 0=table offset, 1=name A, 2=name B, 3=file key."""
    seed1, seed2 = 0x7FED7FED, 0xEEEEEEEE
    for ch in name.upper().encode('ascii'):
        seed1 = (CRYPT_TABLE[(hash_type << 8) + ch] ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed2 = (ch + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1

HASH_TABLE_KEY = hash_string('(hash table)', 3)
BLOCK_TABLE_KEY = hash_string('(block table)', 3)

FLAG_EXISTS = 0x80000000
FLAG_SINGLE_UNIT = 0x01000000
FLAG_ENCRYPTED = 0x00010000
FLAG_FIX_KEY = 0x00020000
FLAG_COMPRESS = 0x00000200


def read_archive(path):
    raw = open(path, 'rb').read()
    mpq_at = raw.find(b'MPQ\x1a')
    prefix = raw[:mpq_at]
    hdr = dict(zip(
        ('magic', 'header_size', 'archive_size', 'format_version', 'sector_size_shift',
         'hash_table_offset', 'block_table_offset', 'hash_table_entries', 'block_table_entries'),
        struct.unpack_from('<4sIIHHIIII', raw, mpq_at)))
    base = mpq_at
    ht_raw = raw[base + hdr['hash_table_offset']:
                 base + hdr['hash_table_offset'] + hdr['hash_table_entries'] * 16]
    bt_raw = raw[base + hdr['block_table_offset']:
                 base + hdr['block_table_offset'] + hdr['block_table_entries'] * 16]
    hash_table = crypt(ht_raw, HASH_TABLE_KEY)
    block_table = crypt(bt_raw, BLOCK_TABLE_KEY)
    blocks = []
    for i in range(hdr['block_table_entries']):
        off, csize, fsize, flags = struct.unpack_from('<IIII', block_table, i * 16)
        blocks.append({'off': off, 'csize': csize, 'fsize': fsize, 'flags': flags})
    return {'prefix': prefix, 'hdr': hdr, 'hash_raw': ht_raw, 'blocks': blocks, 'raw': raw, 'base': base}


def find_block_for(arch, name):
    ht = crypt(arch['hash_raw'], HASH_TABLE_KEY)
    idx = hash_string(name, 0) & (arch['hdr']['hash_table_entries'] - 1)
    for probe in range(arch['hdr']['hash_table_entries']):
        i = (idx + probe) & (arch['hdr']['hash_table_entries'] - 1)
        h_a, h_b, h_locale, h_plat, h_block = struct.unpack_from('<IIHHI', ht, i * 16)
        if h_block == 0xFFFFFFFF:
            return None
        if h_a == hash_string(name, 1) and h_b == hash_string(name, 2):
            return h_block
    return None


def read_block_data(arch, b):
    return arch['raw'][arch['base'] + b['off']: arch['base'] + b['off'] + b['csize']]


def compress_to_sectors(data, sector_size):
    """Build MPQ sector format: offset table + per-sector zlib payloads."""
    sectors = [data[i:i + sector_size] for i in range(0, len(data), sector_size)] or [b'']
    compressed = []
    for s in sectors:
        c = b'\x02' + zlib.compress(s)
        compressed.append(c if len(c) < len(s) else b'\x00' + s)
    n = len(compressed)
    table_size = (n + 1) * 4
    offsets = []
    pos = table_size
    for c in compressed:
        offsets.append(pos)
        pos += len(c)
    offset_table = b''.join(struct.pack('<I', o) for o in offsets)
    offset_table += struct.pack('<I', pos)
    return offset_table + b''.join(compressed)


def _probe_decrypt(raw, block, key, sector_size):
    """严格试解：只有 sector 偏移表完全合法才认为 key 正确。"""
    fsize = block['fsize']
    if fsize == 0:
        return b''
    nsec = (fsize + sector_size - 1) // sector_size
    if (nsec + 1) * 4 > len(raw):
        return None
    offs = list(struct.unpack_from('<%dI' % (nsec + 1),
                                   decrypt(raw[:(nsec + 1) * 4], (key - 1) & 0xFFFFFFFF), 0))
    if offs[0] != (nsec + 1) * 4 or not offs[0] < offs[-1] <= block['csize']:
        return None
    if any(offs[i] > offs[i + 1] for i in range(nsec)):
        return None
    try:
        out = b''
        for i in range(nsec):
            ch = decrypt(raw[offs[i]:offs[i + 1]], (key + i) & 0xFFFFFFFF)
            out += zlib.decompress(ch[1:]) if ch[:1] == b'\x02' else ch[1:]
    except Exception:
        return None
    return out


def find_bound_key(arch, name, sector_size, max_delta=256):
    """反推某成员在原图里真正使用的加密 key —— 游戏就是用这个 key 读它的。

    ⚠️ 不能假设 key == hash(文件名)！本图 (attributes) 实际用的是 hash+1，
    照 hash 写回会让游戏解出垃圾 → 建图闪退。这里直接从原图探测真实值。
    """
    bi = find_block_for(arch, name)
    if bi is None:
        return None
    b = arch['blocks'][bi]
    if not (b['flags'] & FLAG_ENCRYPTED):
        return None
    raw = read_block_data(arch, b)
    base = hash_string(name.split('\\')[-1], 3)
    if b['flags'] & FLAG_FIX_KEY:
        for k in (((base + b['off']) ^ b['fsize']) & 0xFFFFFFFF, (base + b['off']) & 0xFFFFFFFF):
            if _probe_decrypt(raw, b, k, sector_size) is not None:
                return k
    for d in range(max_delta + 1):
        for k in ((base + d) & 0xFFFFFFFF, (base - d) & 0xFFFFFFFF):
            if _probe_decrypt(raw, b, k, sector_size) is not None:
                return k
    return None


def file_key(name, block, key=None):
    """MPQ 成员密钥。

    key 显式给定时优先用它（由 find_bound_key 从原图反推，游戏就是用这个）；
    否则退回通用公式：hash(文件名)，带 FIX_KEY 再叠加自身偏移。
    """
    if key is not None:
        return key & 0xFFFFFFFF
    k = hash_string(name.split('\\')[-1], 3)
    if block['flags'] & FLAG_FIX_KEY:
        k = (k + block['off']) & 0xFFFFFFFF
    return k


def compress_to_sectors_encrypted(data, sector_size, key):
    """同 compress_to_sectors，但按 MPQ 规则加密：
    sector offset table 用 (key-1)，第 i 个扇区数据用 (key+i)。"""
    sectors = [data[i:i + sector_size] for i in range(0, len(data), sector_size)] or [b'']
    compressed = []
    for s in sectors:
        c = b'\x02' + zlib.compress(s)
        compressed.append(c if len(c) < len(s) else b'\x00' + s)
    pos = (len(compressed) + 1) * 4
    offsets = []
    for c in compressed:
        offsets.append(pos)
        pos += len(c)
    table = b''.join(struct.pack('<I', o) for o in offsets) + struct.pack('<I', pos)
    table = encrypt(table, (key - 1) & 0xFFFFFFFF)
    body = b''.join(encrypt(c, (key + i) & 0xFFFFFFFF) for i, c in enumerate(compressed))
    return table + body


def sectors_for(name, block, data, sector_size, key=None):
    """按块原有标志决定是否加密，并在返回前做强制自检。

    ⚠️ 加密标志绝不能丢：本图 war3map.j / w3a / wts / (attributes) 都是
    「压缩 + 文件名派生密钥加密」，标志被清掉后游戏仍按密文解释，建图直接闪退。
    ⚠️ key 必须与游戏读它时用的一致；本图 (attributes) 的 key 是 hash+1 而非 hash，
    所以调用方应先 find_bound_key 反推，再传进来。
    """
    if block['flags'] & FLAG_ENCRYPTED:
        stored = compress_to_sectors_encrypted(data, sector_size,
                                               file_key(name, block, key))
    else:
        stored = compress_to_sectors(data, sector_size)
    verify_sectors(name, block, stored, data, sector_size, key)
    return stored


def verify_sectors(name, block, stored, data, sector_size, key=None):
    """自检：写盘用的存储字节，必须能被「游戏用的 key」原样解回 data。

    这一步专治「扇区偏移表声明的末尾 != csize」这类错位 ——
    它会让 StormLib / 游戏读不出成员（错误码 1004），表现为建图闪退，
    而我自己的解析器因为不校验偏移表边界，会一路「自证成功」看不出来。
    """
    nsec = len([data[i:i + sector_size] for i in range(0, len(data), sector_size)]) or 1
    if block['flags'] & FLAG_ENCRYPTED:
        k = file_key(name, block, key)
        head = decrypt(stored[:(nsec + 1) * 4], (k - 1) & 0xFFFFFFFF)
        offs = list(struct.unpack_from('<%dI' % (nsec + 1), head, 0))
        assert offs[0] == (nsec + 1) * 4, \
            '%s 扇区表起点错：%d != %d' % (name, offs[0], (nsec + 1) * 4)
        assert offs[-1] == len(stored), \
            '%s 扇区表末尾 %d != csize %d（表与实际数据错位，游戏会读不出）' \
            % (name, offs[-1], len(stored))
        out = b''
        for i in range(nsec):
            ch = decrypt(stored[offs[i]:offs[i + 1]], (k + i) & 0xFFFFFFFF)
            out += zlib.decompress(ch[1:]) if ch[:1] == b'\x02' else ch[1:]
    else:
        offs = list(struct.unpack_from('<%dI' % (nsec + 1), stored, 0))
        assert offs[-1] == len(stored), \
            '%s 扇区表末尾 %d != csize %d' % (name, offs[-1], len(stored))
        out = b''
        for i in range(nsec):
            ch = stored[offs[i]:offs[i + 1]]
            out += zlib.decompress(ch[1:]) if ch[:1] == b'\x02' else ch[1:]
    assert out == data, '%s 往返不一致（写出的字节解不回原文）' % name
    return True


def decode_block(raw, block, sector_size):
    """Decompress one block's stored bytes back to its logical content.

    Non-SINGLE_UNIT files always carry a sector offset table, even when they
    hold a single sector (e.g. the 848-byte (attributes) file), so the table is
    read unconditionally.
    """
    if block['fsize'] == 0:
        return b''
    nsec = block['fsize'] // sector_size + 1
    table = list(struct.unpack_from('<%dI' % (nsec + 1), raw, 0))
    out = b''
    for i in range(nsec):
        chunk = raw[table[i]:table[i + 1]]
        if chunk and chunk[0] == 0x02:
            out += zlib.decompress(chunk[1:])
        elif chunk and chunk[0] == 0x00:
            out += chunk[1:]
        else:
            out += chunk
    return out


def _split_attributes(attrs, count):
    """Split (attributes) into (version, flags, crc[], filetime[], md5[])."""
    version, flags = struct.unpack_from('<II', attrs, 0)
    off = 8
    crc = filetime = md5 = None
    if flags & ATTR_CRC:
        crc = list(struct.unpack_from('<%dI' % count, attrs, off))
        off += 4 * count
    if flags & ATTR_FILETIME:
        filetime = [attrs[off + i * 8: off + (i + 1) * 8] for i in range(count)]
        off += 8 * count
    if flags & ATTR_MD5:
        md5 = [attrs[off + i * 16: off + (i + 1) * 16] for i in range(count)]
        off += 16 * count
    return version, flags, crc, filetime, md5


def rebuild_attributes(arch, block_data, sector_size, block_count=None):
    """Recompute (attributes) for the given per-block logical payloads.

    WC3 verifies this table when loading a map: a stale record makes it report
    the changed file (e.g. war3map.j) as corrupt. Records for blocks we are not
    given are left exactly as they were. The self record for (attributes) itself
    is zeroed, matching the convention in files written by the World Editor.

    `block_count` may exceed the old count when members are being added; the
    three parallel arrays are then zero-extended so the table still indexes by
    block-table position.
    """
    bidx = find_block_for(arch, ATTR_NAME)
    if bidx is None:
        return None
    original = decode_block(read_block_data(arch, arch['blocks'][bidx]),
                            arch['blocks'][bidx], sector_size)
    old = len(arch['blocks'])
    count = block_count or old
    version, flags, crc, filetime, md5 = _split_attributes(original, old)
    if count > old:
        pad_i = [0] * (count - old)
        pad_t = [b'\0' * 8] * (count - old)
        pad_m = [b'\0' * 16] * (count - old)
        if crc is not None:
            crc += pad_i
        if filetime is not None:
            filetime += pad_t
        if md5 is not None:
            md5 += pad_m
    for i, payload in block_data.items():
        if crc is not None:
            crc[i] = zlib.crc32(payload) & 0xFFFFFFFF
        if md5 is not None:
            md5[i] = hashlib.md5(payload).digest()
    if crc is not None:
        crc[bidx] = 0

    out = bytearray(struct.pack('<II', version, flags))
    if crc is not None:
        out += struct.pack('<%dI' % count, *crc)
    if filetime is not None:
        out += b''.join(filetime)
    if md5 is not None:
        out += b''.join(md5)
    return bytes(out)


def _add_hash_entry(hash_raw, name, block_index):
    """Place a name's two hashes in a free slot, keeping probe order valid.

    Takes and returns the *encrypted* table, so callers can chain additions.
    """
    ht = bytearray(decrypt(hash_raw, HASH_TABLE_KEY))
    n = len(ht) // 16
    idx = hash_string(name, 0) & (n - 1)
    for probe in range(n):
        i = (idx + probe) & (n - 1)
        h_a, h_b, loc, plat, blk = struct.unpack_from('<IIHHI', ht, i * 16)
        if blk == 0xFFFFFFFF:
            struct.pack_into('<IIHHI', ht, i * 16,
                             hash_string(name, 1), hash_string(name, 2),
                             0, 0, block_index)
            return encrypt(bytes(ht), HASH_TABLE_KEY)
        if h_a == hash_string(name, 1) and h_b == hash_string(name, 2):
            raise RuntimeError('hash entry already exists for %r' % name)
    raise RuntimeError('hash table full, cannot add %r' % name)


def repack(arch, replacements, out_path, additions=None):
    """replacements: {name: new_content_bytes}; additions: {name: content} new members.

    Adding a member grows the block table (and, with it, the (attributes)
    arrays), so the result is no longer a pure in-place shuffle. Existing
    entries keep their order, which is what (attributes) indexes by.
    """
    blocks = [dict(b) for b in arch['blocks']]
    sector_size = 512 << arch['hdr']['sector_size_shift']
    hash_raw = arch['hash_raw']
    added = {}

    for name, content in (additions or {}).items():
        if find_block_for(arch, name) is not None:
            raise RuntimeError('%r already exists' % name)
        idx = len(blocks)
        blocks.append({'off': 0, 'csize': 0, 'fsize': len(content),
                       'flags': FLAG_EXISTS | FLAG_COMPRESS, '_data': None,
                       '_content': content})
        hash_raw = _add_hash_entry(hash_raw, name, idx)
        added[idx] = content

    changed = {}
    for name, content in replacements.items():
        bidx = find_block_for(arch, name)
        if bidx is None:
            raise RuntimeError('block not found for %r' % name)
        b = blocks[bidx]
        if b['flags'] & FLAG_SINGLE_UNIT:
            raise RuntimeError('cannot write SINGLE_UNIT file %r' % name)
        b['_data'] = sectors_for(name, b, content, sector_size)
        b['csize'] = len(b['_data'])
        b['fsize'] = len(content)
        b['_name'] = name
        changed[bidx] = content

    for idx, content in added.items():
        b = blocks[idx]
        b['_data'] = compress_to_sectors(content, sector_size)
        b['csize'] = len(b['_data'])
        b['fsize'] = len(content)
        changed[idx] = content

    # WC3 checks (attributes) on load; refresh the records for the files we
    # touched so it does not reject the map as corrupt.
    attr_bidx = find_block_for(arch, ATTR_NAME)
    if attr_bidx is not None and attr_bidx not in changed:
        new_attrs = rebuild_attributes(arch, changed, sector_size,
                                       block_count=len(blocks))
        b = blocks[attr_bidx]
        b['_data'] = compress_to_sectors(new_attrs, sector_size)
        b['csize'] = len(b['_data'])
        b['fsize'] = len(new_attrs)

    # lay out all existing blocks sequentially after the 32-byte header
    cursor = 32
    ALIGN = 512
    for b in blocks:
        if not (b['flags'] & FLAG_EXISTS):
            continue
        if '_data' not in b:
            b['_data'] = read_block_data(arch, b)
        cursor = (cursor + ALIGN - 1) // ALIGN * ALIGN
        b['off'] = cursor
        cursor += b['csize'] if b['csize'] else len(b['_data'])

    hash_at = (cursor + ALIGN - 1) // ALIGN * ALIGN
    block_at = hash_at + arch['hdr']['hash_table_entries'] * 16
    archive_size = block_at + len(blocks) * 16

    out = bytearray()
    out += arch['prefix']
    hdr = dict(arch['hdr'])
    hdr['archive_size'] = archive_size
    hdr['hash_table_offset'] = hash_at
    hdr['block_table_offset'] = block_at
    hdr['block_table_entries'] = len(blocks)
    out += struct.pack('<4sIIHHIIII', hdr['magic'], hdr['header_size'], hdr['archive_size'],
                       hdr['format_version'], hdr['sector_size_shift'], hdr['hash_table_offset'],
                       hdr['block_table_offset'], hdr['hash_table_entries'], hdr['block_table_entries'])
    for b in blocks:
        if not (b['flags'] & FLAG_EXISTS):
            continue
        pad = b['off'] - len(out)
        if pad > 0:
            out += b'\0' * pad
        out += b['_data']

    if len(out) < hash_at:
        out += b'\0' * (hash_at - len(out))
    out += hash_raw

    bt = bytearray()
    for b in blocks:
        bt += struct.pack('<IIII', b['off'], b['csize'], b['fsize'], b['flags'])
    out += encrypt(bytes(bt), BLOCK_TABLE_KEY)

    open(out_path, 'wb').write(bytes(out))
    return len(out)
