#!/usr/bin/env python3
"""解除 Agent Canvas 前端的上传体积限制（默认 3MB → 500MB 单文件 / 5TB 合计）。

为什么存在这个脚本
    3MB 限制只在浏览器前端（构建产物里的两个常量），后端与 agent-server 没有任何
    体积上限。前端常量写死在 assets/*.js 里，Docker 镜像又**没有**任何 prestart
    钩子目录，所以升级镜像后补丁会丢，需要重打一次。

安全设计（宁可不动，也不要把界面改坏）
    1. 冒烟测试：先在临时端口起一个静态服务，按文件真实字节数校验它返回的内容。
       本脚本的改写是**等长**的，只有静态服务在启动时缓存 Content-Length（sirv 非
       dev 模式）时才安全。若校验发现服务按真实长度返回（说明新版改为每请求 stat），
       则先停止——因为「等长校验」将失去意义，需人工确认后再用 --force。
    2. 只认原始构建：文件必须同时含两个常量标签与两条提示文案的原样，否则不动文件。
    3. 等长：改写后字节数与原始完全一致，差额补成尾部注释——不改运行时行为，也让
       静态服务缓存里的 Content-Length 仍然正确。
    4. 四道自检：等长、语义常量、node --check 语法、线上字节数 == 磁盘字节数。
    5. 幂等：已打过直接跳过；备份保留，可 --restore 还原。

用法（在容器内执行）
    sudo python3 upload_limit_patch.py            # 打补丁（已打过则只做检查）
    sudo python3 upload_limit_patch.py --check     # 只核对线上文件与磁盘是否一致
    sudo python3 upload_limit_patch.py --restore   # 还原成原始的 3MB 上限
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

FRONTEND_DIR = Path("/opt/agent-canvas/frontend")
ASSETS_DIR = FRONTEND_DIR / "assets"

# 前端构建产物里唯一含该标签的文件；文件名带内容哈希，升级镜像后可能变化。
TARGET_GLOB = "llm-not-configured-banner-*.js"

# 原始（未打补丁）文件的识别标签，三者必须同时存在。
ORIGINAL_TAGS = [
    b"Mr=3*1024*1024,Nr=3*1024*1024;",  # Mr=单文件上限、Nr=合计上限
    b"Files exceeding 3MB are not allowed: ",
    b"exceeding the 3MB limit. Please select fewer or smaller files.",
]

# 等长替换表：(原始 → 新)。每条都必须命中。
REPLACEMENTS = [
    (b"Mr=3*1024*1024,Nr=3*1024*1024;", b"Mr=5e8,Nr=5e12;"),
    (b"Files exceeding 3MB are not allowed: ", b"Files over 500MB are not allowed: "),
    (b"exceeding the 3MB limit. Please select fewer or smaller files.",
     b"over the 5TB limit. Please select fewer or smaller files."),
]

PATCH_MARKER = b"Mr=5e8"
BACKUP_DIR = Path("/home/openhands/.openhands/archive/agent-canvas-upload-limit/frontend-backup")

STATIC_SERVER = Path("/opt/agent-canvas/static-server.mjs")
CONFIG_JSON = Path("/opt/agent-canvas/config.json")
BASE_PATH = "/canvas"


OK, BAD, NOTE = "[ OK ]", "[FAIL]", "[note]"
_failed: list[str] = []


def log(tag: str, msg: str) -> None:
    print(f"{tag} {msg}", flush=True)


def fail(msg: str) -> None:
    _failed.append(msg)
    log(BAD, msg)


def read_config() -> dict:
    if CONFIG_JSON.exists():
        try:
            return json.loads(CONFIG_JSON.read_text())
        except Exception:
            pass
    return {}


def find_target() -> Path | None:
    cands = sorted(ASSETS_DIR.glob(TARGET_GLOB))
    if not cands:
        return None
    for p in cands:
        blob = p.read_bytes()
        if PATCH_MARKER in blob or all(t in blob for t in ORIGINAL_TAGS):
            return p
    return cands[0]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def fetch(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def web_base_candidates() -> list[str]:
    """统一入口通常是 8000；再从容器配置里兜底。"""
    bases = []
    cfg = read_config()
    for key in ("CONFIG_PROXY_PORT", "CONFIG_PORT"):
        if cfg.get(key):
            bases.append(f"http://127.0.0.1:{cfg[key]}")
    bases.append("http://127.0.0.1:8000")
    return list(dict.fromkeys(bases))


def start_temp_server(ready_rel: str) -> tuple[subprocess.Popen, str]:
    """另起一个静态服务（内存缓存为空），用于冒烟测试与线上字节数校验。

    ready_rel：等待可访问的相对路径（用它判断服务已就绪）。
    """
    port = free_port()
    url = f"http://127.0.0.1:{port}/{BASE_PATH.lstrip('/')}/{ready_rel}"
    proc = subprocess.Popen(
        ["node", str(STATIC_SERVER), "--port", str(port), "--host", "127.0.0.1",
         "--dir", str(FRONTEND_DIR), "--base-path", BASE_PATH],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            if fetch(url, timeout=5):
                return proc, f"http://127.0.0.1:{port}"
        except Exception:
            time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("临时静态服务起不来")


def smoke_test() -> bool:
    """实测静态服务对「文件被改大之后」的返回行为，判定等长改写是否必要。

    做法：在静态服务启动**之前**放一个探针文件，等服务起来后把它改大 10 字节，
    再请求一次——
      * 返回仍是旧字节数 ⇒ 服务缓存了启动时的长度，等长改写是唯一安全的改法（True）；
      * 返回新的字节数 ⇒ 服务每次都重新 stat，等长改写不再需要，先停下等人工确认（False）。

    返回 True 表示可以继续打补丁。
    """
    name = f"__upload_limit_probe_{os.urandom(4).hex()}.js"
    probe = FRONTEND_DIR / name
    body = b"/* probe */" + b"a" * 64
    try:
        probe.write_bytes(body)
    except PermissionError:
        log(NOTE, f"无权写入 {FRONTEND_DIR}，跳过冒烟测试（请用 sudo 运行）")
        return False
    try:
        proc, base = start_temp_server(name)
        url = f"{base}/{BASE_PATH.lstrip('/')}/{name}"
        try:
            first = fetch(url)
            probe.write_bytes(body + b"b" * 10)
            second = fetch(url)
        finally:
            proc.terminate()
            proc.wait(timeout=10)
    finally:
        probe.unlink(missing_ok=True)

    if len(second) == len(first) + 10:
        log(BAD, f"静态服务每次请求都重新读取文件长度（改大后立刻返回 {len(second)} 字节）")
        log(NOTE, "该镜像改了服务实现：等长改写不再必要，改了还可能夹带额外限制。")
        log(NOTE, "已停止，不动任何文件。确认新版行为后可加 --force 强制改写。")
        return False
    if len(second) != len(first):
        log(BAD, f"探针返回长度异常：改前 {len(first)}、改后 {len(second)} 字节，无法判断")
        return False
    if len(first) != len(body):
        log(BAD, f"探针首次返回 {len(first)} 字节，与写入的 {len(body)} 字节不符")
        return False
    log(OK, f"冒烟测试：确认服务按启动时缓存的长度返回（文件改成 {len(body) + 10} 字节，"
            f"仍返回 {len(first)} 字节）")
    log(NOTE, "等长改写是当前镜像下唯一安全的改法。")
    return True


def pick_web_base(ready_rel: str) -> str | None:
    for base in web_base_candidates():
        base = base.rstrip("/")
        try:
            if fetch(f"{base}/{BASE_PATH.lstrip('/')}/{ready_rel}", timeout=10):
                return base
        except Exception:
            continue
    return None


def check_served_matches_disk(target: Path, base: str | None = None) -> bool:
    """线上字节数 == 磁盘字节数。sirv 缓存长度时，改大文件会让响应被截断。"""
    rel = target.relative_to(FRONTEND_DIR).as_posix()
    if base is None:
        base = pick_web_base(rel)
        if base is None:
            fail("拿不到前端入口，无法做线上校验")
            return False
    url = f"{base}/{BASE_PATH.lstrip('/')}/{rel}"
    served = fetch(url)
    disk = target.read_bytes()
    same = served == disk
    if same:
        log(OK, f"线上校验：{url} 返回 {len(served)} 字节，与磁盘一致")
        log(OK, f"线上文件 md5 {hashlib.md5(served).hexdigest()}")
    else:
        fail(f"线上校验：磁盘 {len(disk)} 字节，线上 {len(served)} 字节 —— 响应被截断，"
             f"浏览器会加载坏文件。重启容器后重跑本脚本即可。")
    if PATCH_MARKER not in served:
        fail("线上文件里没有新上限常量，仍是旧内容（浏览器缓存或补丁未生效）")
    else:
        log(OK, "线上文件含新上限常量 Mr=5e8")
    return same


def syntax_ok(path: Path) -> bool:
    r = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    if r.returncode == 0:
        log(OK, "node --check 语法检查通过")
        return True
    fail(f"node --check 失败：{r.stderr.strip()[:200]}")
    return False


def logic_ok() -> bool:
    """拿磁盘上真实的 bundle 跑上传校验用例（上限、边界、合计、提示文案）。"""
    script = Path(__file__).resolve().parent / "verify_upload_logic.js"
    if not script.exists():
        log(NOTE, f"找不到 {script.name}，跳过逻辑用例")
        return True
    r = subprocess.run(["node", str(script), "--expect-patched"],
                       capture_output=True, text=True)
    for raw in r.stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("FAIL"):
            fail(line)
        else:
            log(OK if line.startswith(("PASS", "目标文件", "解析出的", "全部通过")) else NOTE, line)
    if r.returncode == 0:
        log(OK, "上传限制逻辑用例全部通过")
        return True
    fail(f"逻辑用例未通过：{(r.stderr.strip() or '见上面的 FAIL 行')[:200]}")
    return False


def rollback(target: Path, original: bytes) -> None:
    """自检未过时把文件写回改动前的字节，避免把界面留在坏状态。"""
    try:
        target.write_bytes(original)
    except OSError as e:
        fail(f"回滚失败：{e} —— 请手动跑 --restore 还原")
        return
    if target.read_bytes() == original:
        log(OK, f"已自动回滚到改动前的内容（{len(original)} 字节），界面仍可用。")
    else:
        fail("回滚后内容与改动前不一致，请手动跑 --restore")


def describe_current_limit(blob: bytes) -> None:
    """告诉用户现在文件里的上限到底是多少，方便判断镜像是否已自带更大限制。"""
    text = blob.decode("utf-8", "ignore")

    pairs = [
        ("单文件上限 Mr", r"Mr=([0-9.eE+*\s]+?)(?:,|;)"),
        ("合计上限 Nr", r"Nr=([0-9.eE+*\s]+?)(?:,|;)"),
    ]
    for label, pat in pairs:
        m = re.search(pat, text)
        if not m:
            log(NOTE, f"{label}：没找到")
            continue
        raw = m.group(1).strip()
        try:
            val = int(eval(raw))  # noqa: S307 - 只解析数字常量，数字白名单已由正则限定
        except Exception:
            log(NOTE, f"{label}：{raw}（无法解析成数字）")
            continue
        human = f"{val / 1024 / 1024:.1f}MB" if val < 1e12 else f"{val / 1e12:.1f}TB"
        log(NOTE, f"{label}：{raw} = {val} 字节（约 {human}）")


def backup(target: Path) -> Path:
    dest = BACKUP_DIR / target.parent.name / target.name
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
        log(OK, f"已备份原始文件到 {dest}")
    else:
        log(NOTE, f"备份已存在：{dest}")
    return dest


def do_patch(target: Path) -> None:
    orig = target.read_bytes()
    new = orig
    for old, rep in REPLACEMENTS:
        if old not in new:
            raise RuntimeError(f"没匹配到预期文案：{old[:60]!r}（镜像可能已更新，请先更新脚本里的标签）")
        new = new.replace(old, rep, 1)

    pad = len(orig) - len(new)
    if pad < 4:
        raise RuntimeError(f"只需补 {pad} 字节，放不下注释，请改短替换文案")
    new += b"/*" + b"x" * (pad - 4) + b"*/"  # 尾部注释补齐，不改运行时行为

    if len(new) != len(orig):
        raise RuntimeError("改写后长度不一致，等长约束被破坏")

    target.write_bytes(new)
    log(OK, f"已写入 {target}（{len(new)} 字节，与原始等长）")


def cmd_check(target: Path) -> int:
    log(NOTE, f"目标文件：{target}")
    check_served_matches_disk(target)
    return 1 if _failed else 0


def cmd_restore(target: Path) -> int:
    dest = BACKUP_DIR / target.parent.name / target.name
    if not dest.exists():
        fail(f"找不到备份 {dest}，无法还原")
        return 1
    shutil.copy2(dest, target)
    log(OK, f"已还原 {target}（{len(dest.read_bytes())} 字节）")
    if PATCH_MARKER in target.read_bytes():
        fail("还原后仍含补丁常量")
        return 1
    log(OK, "已确认回到原始的 3MB 上限")
    log(NOTE, "请在浏览器按 Ctrl+Shift+R 强制刷新。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="解除 Agent Canvas 前端上传上限")
    ap.add_argument("--check", action="store_true", help="只核对线上文件与磁盘是否一致")
    ap.add_argument("--restore", action="store_true", help="还原成原始的 3MB 上限")
    ap.add_argument("--force", action="store_true", help="跳过冒烟测试的安全判定")
    args = ap.parse_args()

    if not STATIC_SERVER.exists():
        fail(f"找不到 {STATIC_SERVER}，无法做安全校验")
        return 1

    target = find_target()
    if target is None:
        fail(f"{ASSETS_DIR} 下找不到 {TARGET_GLOB}，镜像结构可能已变")
        return 1

    if args.restore:
        return cmd_restore(target)

    blob = target.read_bytes()
    if PATCH_MARKER in blob:
        log(OK, "已经打过补丁，跳过改写")
        i = blob.index(PATCH_MARKER)
        log(NOTE, f"当前上限常量：{blob[i:i + 20].decode()}")
        return cmd_check(target)

    if args.check:
        return cmd_check(target)

    missing = [t for t in ORIGINAL_TAGS if t not in blob]
    if missing:
        fail(f"文件不是预期的原始构建，缺标签：{[m[:40] for m in missing]}")
        describe_current_limit(blob)
        fail("为避免改坏界面，本次不动任何文件。")
        return 1
    log(OK, f"文件指纹匹配（原始构建，{len(blob)} 字节）")

    if not args.force and not smoke_test():
        return 0

    # 先备份「改动前的字节」，任何自检不过都按它回滚。
    pre_patch = blob
    backup(target)
    try:
        do_patch(target)
    except RuntimeError as e:
        fail(str(e))
        if target.read_bytes() != pre_patch:
            rollback(target, pre_patch)
        return 1

    log(NOTE, "开始自检")
    new = target.read_bytes()
    if len(new) == len(blob):
        log(OK, f"等长校验通过：{len(new)} 字节")
    else:
        fail(f"等长校验失败：原始 {len(blob)} → 现在 {len(new)} 字节")
    text = new.decode("utf-8", "ignore")
    for kw, want in [("Mr=5e8", True), ("Nr=5e12", True), ("3*1024*1024", False)]:
        got = kw in text
        if got == want:
            log(OK, f"常量检查 {kw!r} 存在={got}")
        else:
            fail(f"常量检查 {kw!r} 存在={got}，期望 {want}")
    syntax_ok(target)
    logic_ok()
    check_served_matches_disk(target)

    if _failed:
        rollback(target, pre_patch)
        print("\n结果：自检未通过，已自动回滚，界面仍是原来的样子。", flush=True)
        print("若要排查，可单独跑 --check；确认新版行为后再加 --force。", flush=True)
        return 1
    print("\n结果：全部通过。请在浏览器按 Ctrl+Shift+R 强制刷新后使用。", flush=True)
    print("提示：升级镜像后补丁会丢，重跑一次本脚本即可。", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已取消。", flush=True)
        sys.exit(130)
    except Exception as e:  # 兜底：任何异常都不留英文堆栈给用户
        print(f"\n[FAIL] 意外错误：{type(e).__name__}: {e}", flush=True)
        print("未完成的改动可能仍留在磁盘上，可跑 --restore 还原。", flush=True)
        sys.exit(1)
