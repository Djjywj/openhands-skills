# -*- coding: utf-8 -*-
"""从地图提取 war3map.j，用于版本门禁校验与对照实验。

用法：
    python3 extract_j.py <地图.w3x> [输出.j]
    python3 extract_j.py --batch b=/path/a.w3x,v8=/path/b.w3x   # 批量

依赖同目录的 maprepack.py + mpqrepack.py（能解**自定义密钥加密**的成员，
mpyq 做不到 —— 它会报 `Encryption is not supported yet.`）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def extract(map_path, out_path):
    import maprepack as R
    data = R.read_member(R.read_archive(map_path), 'war3map.j')
    open(out_path, 'wb').write(data)
    print('%-14s %7d 字节，%5d 行（回车 %d / 换行 %d）'
          % (os.path.basename(out_path), len(data), data.count(b'\n') + data.count(b'\r'),
             data.count(b'\r'), data.count(b'\n')))
    return data


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--batch':
        os.makedirs('samples', exist_ok=True)
        for item in sys.argv[2].split(','):
            tag, path = item.split('=', 1)
            extract(path.strip(), os.path.join('samples', tag + '.j'))
    elif len(sys.argv) >= 2:
        out = sys.argv[2] if len(sys.argv) > 2 else 'war3map.j'
        extract(sys.argv[1], out)
    else:
        print(__doc__)
        sys.exit(2)
