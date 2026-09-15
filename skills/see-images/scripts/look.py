#!/usr/bin/env python3
"""Read an image by delegating to a vision-capable model (DeepSeek ``deepseek-flash``).

This agent cannot see image pixels directly. This script sends an image to the
DeepSeek OpenAI-compatible vision endpoint and prints the model's textual answer,
so image content can be inspected from any conversation.

Usage:
    python3 look.py IMAGE [PROMPT] [--detail low|high|original|auto]
    python3 look.py --latest [PROMPT] [--save out.png]
    python3 look.py --url https://example.com/a.png [PROMPT]
    python3 look.py IMG1 IMG2 [PROMPT]          # multiple images, one request

API key resolution order (never printed, never written to disk):
    1. $DEEPSEEK_API_KEY
    2. decrypt the ``api_key`` field of a stored profile under ~/.openhands/profiles/
       using $OH_SECRET_KEY (Fernet key = b64(sha256(OH_SECRET_KEY)))

Images are normalised automatically: unsupported formats (BMP/TIFF) are re-encoded
to JPEG, and oversized images (>32 MiB or any side >8192 px) are downscaled.
"""

from __future__ import annotations

import argparse
import base64
import glob
import io
import json
import os
import re
import sys

BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"

ALLOWED_FORMATS = {"PNG": "image/png", "JPEG": "image/jpeg", "GIF": "image/gif", "WEBP": "image/webp"}
MAX_BYTES = 32 * 1024 * 1024
MAX_SIDE = 8192
PROFILES_DIR = os.path.expanduser("~/.openhands/profiles")
CONVERSATIONS_ROOT = os.environ.get(
    "OH_CONVERSATIONS_PATH", os.path.expanduser("~/.openhands/agent-canvas/conversations")
)


def load_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    secret = os.environ.get("OH_SECRET_KEY")
    if not secret:
        sys.exit("No DEEPSEEK_API_KEY set and no OH_SECRET_KEY to decrypt a stored profile.")
    # Importing the SDK prints a startup banner to stderr; silence it so callers
    # (and the vision transcript they parse) stay clean. Set before the import.
    os.environ["OPENHANDS_SUPPRESS_BANNER"] = "1"
    from openhands.sdk.utils.cipher import Cipher

    cipher = Cipher(secret)
    for path in sorted(glob.glob(os.path.join(PROFILES_DIR, "*.json"))):
        try:
            data = json.load(open(path))
        except Exception:
            continue
        token = data.get("api_key")
        if isinstance(token, str) and token.startswith("gAAAAA"):
            plain = cipher.decrypt(token)
            if plain:
                return plain.get_secret_value()
    sys.exit("Could not decrypt any stored profile API key.")


def encode_for_api(raw: bytes) -> tuple[bytes, str, str | None]:
    """Return (bytes, mime, note). Re-encodes/downscales only when limits require it."""
    from PIL import Image

    im = Image.open(io.BytesIO(raw))
    fmt = (im.format or "").upper()
    note = None
    if fmt in ALLOWED_FORMATS and max(im.size) <= MAX_SIDE and len(raw) <= MAX_BYTES:
        return raw, ALLOWED_FORMATS[fmt], note

    reasons = []
    if fmt not in ALLOWED_FORMATS:
        reasons.append(f"unsupported format {fmt or '?'}")
    if max(im.size) > MAX_SIDE:
        reasons.append(f"side {max(im.size)}px > {MAX_SIDE}px")
    if len(raw) > MAX_BYTES:
        reasons.append(f"{len(raw) / 1048576:.1f}MiB > 32MiB")

    rgb = im.convert("RGB")
    for scale in (1.0, 0.75, 0.5, 0.35, 0.25, 0.15, 0.1):
        w, h = max(1, int(rgb.width * scale)), max(1, int(rgb.height * scale))
        if max(w, h) > MAX_SIDE:
            r = MAX_SIDE / max(w, h)
            w, h = max(1, int(w * r)), max(1, int(h * r))
        buf = io.BytesIO()
        rgb.resize((w, h), Image.LANCZOS).save(buf, "JPEG", quality=88)
        data = buf.getvalue()
        if len(data) <= MAX_BYTES:
            note = f"re-encoded to JPEG {w}x{h} ({'; '.join(reasons)})"
            return data, "image/jpeg", note
    sys.exit("Could not shrink image under the 32 MiB limit.")


def image_from_conversation() -> tuple[bytes, str]:
    """Newest image in *this* conversation's event log."""
    events = os.path.join(current_conversation_dir(), "events")
    best: tuple[int, str] | None = None
    for path in glob.glob(os.path.join(events, "*.json")):
        try:
            index = int(os.path.basename(path).split("-")[1])
            event = json.load(open(path))
        except Exception:
            continue
        for content in (event.get("llm_message") or {}).get("content") or []:
            if isinstance(content, dict) and content.get("type") == "image":
                for url in content.get("image_urls") or []:
                    if best is None or index > best[0]:
                        best = (index, url)
    if best is None:
        sys.exit(f"No image found in this conversation's events ({events}).")
    data_url = best[1]
    match = re.match(r"^data:([^;,]+);base64,(.*)$", data_url, re.S)
    if match:
        return base64.b64decode(match.group(2)), match.group(1)
    return _fetch(data_url), "image/png"


def current_conversation_dir() -> str:
    """Resolve the conversation owning the current workspace."""
    base = os.path.basename(os.getcwd())
    if re.fullmatch(r"[0-9a-f]{32}", base):
        candidate = os.path.join(CONVERSATIONS_ROOT, base)
        if os.path.isdir(os.path.join(candidate, "events")):
            return candidate
    # Fall back to the most recently modified conversation that has events.
    convs = [
        os.path.join(CONVERSATIONS_ROOT, name)
        for name in os.listdir(CONVERSATIONS_ROOT)
        if os.path.isdir(os.path.join(CONVERSATIONS_ROOT, name, "events"))
    ] if os.path.isdir(CONVERSATIONS_ROOT) else []
    if convs:
        return max(convs, key=os.path.getmtime)
    sys.exit(f"No conversation with events found under {CONVERSATIONS_ROOT}.")


def _fetch(url: str) -> bytes:
    import httpx

    response = httpx.get(url, timeout=60, follow_redirects=True)
    response.raise_for_status()
    return response.content


def build_content(question: str, parts: list[tuple[bytes, str]], detail: str) -> list[dict]:
    content: list[dict] = [{"type": "text", "text": question}]
    for raw, mime in parts:
        b64 = base64.b64encode(raw).decode()
        content.append(
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": detail}}
        )
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description="Read an image via a vision LLM.")
    parser.add_argument(
        "items",
        nargs="*",
        help="image path(s) followed by an optional question (the non-path trailing arg)",
    )
    parser.add_argument("--latest", action="store_true", help="use newest image from this conversation")
    parser.add_argument("--url", action="append", default=[], help="remote image URL (repeatable)")
    parser.add_argument("--prompt", default=None, help="question about the image(s)")
    parser.add_argument("--detail", default="high", choices=["low", "high", "original", "auto"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--save", help="write the extracted/latest image here")
    args = parser.parse_args()

    # Trailing non-path argument is the prompt; anything that names a real file is an image.
    paths: list[str] = []
    inline_prompt: str | None = None
    for item in args.items:
        if os.path.isfile(item):
            paths.append(item)
        elif inline_prompt is None:
            inline_prompt = item
        else:
            inline_prompt = f"{inline_prompt} {item}"

    parts: list[tuple[bytes, str]] = []
    for url in args.url:
        parts.append((_fetch(url), "image/png"))
    if args.latest:
        raw, _ = image_from_conversation()
        if args.save:
            open(args.save, "wb").write(raw)
        parts.append(encode_for_api(raw)[:2])
    for path in paths:
        parts.append(encode_for_api(open(path, "rb").read())[:2])
    if not parts:
        sys.exit("Provide image path(s), --latest, or --url. If a path was given, it is not a file.")

    question = args.prompt or inline_prompt or "详细、客观地描述这张图片，并逐字转录其中所有可见文字。"

    from openai import OpenAI

    client = OpenAI(api_key=load_api_key(), base_url=BASE_URL)
    response = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": build_content(question, parts, args.detail)}],
    )
    print(response.choices[0].message.content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
