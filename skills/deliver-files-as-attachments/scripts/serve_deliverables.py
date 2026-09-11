#!/usr/bin/env python3
"""Serve workspace deliverables over a host-mapped port so the user gets a real download link.

Why this exists
---------------
In Agent Canvas the "Files" panel is the documented download path, but it is not always
visible/available to every user. The ``/api/file/download`` and
``/api/conversations/<id>/workspace/<path>`` routes require the session API key (they return
401 without it), and ``/api/v1/app-conversations/<id>/file`` only returns JSON for previews.
Embedding a session key in a link is forbidden.

Agent Canvas maps one or more *container* ports to *host* ports that the user can reach via
``http://localhost:<host_port>`` (the mapping is advertised in the repo context as
``work_hosts``). Serving the deliverable directory on one of those container ports therefore
gives the user a clickable, key-free download URL.

Usage
-----
    python3 serve_deliverables.py --dir /workspace/project --container-port 8011 \
        --host-port 41757 [--files a.zip b.json] [--background]

It prints the landing page URL and one direct URL per file. If ``--background`` is given it
daemonizes the server and writes a PID file. The static server keeps running until the
conversation/sandbox stops, so re-running the command for a new build is usually unnecessary:
just overwrite the files in the served directory.
"""
import argparse
import html
import os
import sys
import threading
import http.server
import socketserver
import urllib.parse


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # silence per-request noise
        pass

    def end_headers(self):
        # Force a real download for the common deliverable extensions.
        if self.path.lower().split("?")[0].endswith((".zip", ".json", ".txt", ".csv", ".md")):
            self.send_header("Content-Disposition", "attachment")
        super().end_headers()


def write_index(directory, files, title):
    rows = []
    for name, desc in files:
        rows.append(
            '<a class="card" href="%s" download><div class="name">%s</div>'
            '<div class="meta">%s</div></a>' % (urllib.parse.quote(name), html.escape(name), html.escape(desc))
        )
    page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><style>
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#0f1115;color:#e8eaed;margin:0;padding:32px;max-width:720px}
h1{font-size:20px}p{color:#9aa0a6;font-size:14px}
a.card{display:block;background:#1c2028;border:1px solid #2a2f3a;border-radius:12px;padding:16px 18px;margin:12px 0;text-decoration:none;color:#e8eaed}
a.card:hover{border-color:#22d59c}.name{font-size:16px;font-weight:600}.meta{color:#9aa0a6;font-size:13px;margin-top:4px}
</style></head><body><h1>%s</h1><p>点击文件即可下载。</p>%s</body></html>""" % (
        html.escape(title), html.escape(title), "".join(rows)
    )
    with open(os.path.join(directory, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/workspace/project", help="directory to serve")
    ap.add_argument("--container-port", type=int, default=8011)
    ap.add_argument("--host-port", type=int, default=None, help="host port mapped to container port")
    ap.add_argument("--files", nargs="*", default=[], help="file names to link on the landing page")
    ap.add_argument("--title", default="文件下载")
    ap.add_argument("--background", action="store_true")
    args = ap.parse_args()

    directory = os.path.abspath(args.dir)
    if args.files:
        write_index(directory, [(f, "") for f in args.files], args.title)

    os.chdir(directory)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("0.0.0.0", args.container_port), QuietHandler)

    base = "http://localhost:%d" % (args.host_port or args.container_port)
    print("Serving %s on container port %d" % (directory, args.container_port))
    print("Landing page: %s/" % base)
    for f in args.files:
        print("Direct link: %s/%s" % (base, urllib.parse.quote(f)))

    if args.background:
        pid = os.fork()
        if pid:
            print("Background PID:", pid)
            return
        os.setsid()
        httpd.serve_forever()
    else:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
