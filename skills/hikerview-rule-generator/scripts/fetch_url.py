#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同步抓取网页/接口，供 Node 测试桩的 fetch()/request() 调用。

用法:
    python3 fetch_url.py <url> [--method GET|POST] [--headers JSON]
                          [--body STR] [--timeout 20] [--ua UA]

stdout: 响应正文（UTF-8）
stderr: 出错信息，退出码 1
"""
import argparse
import gzip
import io
import json
import sys
import urllib.request
import urllib.parse
import ssl
import zlib

DEFAULT_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
              "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--method", default="GET")
    ap.add_argument("--headers", default="{}")
    ap.add_argument("--body", default=None)
    ap.add_argument("--timeout", type=float, default=20)
    ap.add_argument("--ua", default=None)
    args = ap.parse_args()

    try:
        headers = json.loads(args.headers or "{}")
    except Exception:
        headers = {}
    if not any(k.lower() == "user-agent" for k in headers):
        headers["User-Agent"] = args.ua or DEFAULT_UA

    data = args.body.encode("utf-8") if args.body else None
    # 网址里若有中文等非 ASCII 字符，先按 URL 规则转码，避免请求直接报错
    safe_url = urllib.parse.quote(args.url, safe=":/?#[]@!$&'()*+,;=%~")
    req = urllib.request.Request(safe_url, data=data, headers=headers, method=args.method.upper())

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        resp = urllib.request.urlopen(req, timeout=args.timeout, context=ctx)
        raw = resp.read()
        enc = (resp.headers.get("Content-Encoding") or "").lower()
        if enc == "gzip":
            raw = gzip.decompress(raw)
        elif enc == "deflate":
            raw = zlib.decompress(raw)
        charset = resp.headers.get_content_charset() or "utf-8"
        sys.stdout.buffer.write(raw.decode(charset, "ignore").encode("utf-8"))
    except Exception as e:
        # 用 UTF-8 字节直接输出，防止报错信息里的中文因系统编码再次崩溃
        sys.stderr.buffer.write(("fetch_url error: %s\n" % e).encode("utf-8", "replace"))
        sys.exit(1)


if __name__ == "__main__":
    main()
