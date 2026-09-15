#!/usr/bin/env python3
"""Generate images from a text prompt.

Uses Pollinations.AI, which needs no API key. This is the only image generation
reachable from this environment: the configured DeepSeek endpoint serves chat
models only (its /images/generations returns 404).

Usage:
    python3 gen.py "a watercolor fox reading a book"
    python3 gen.py "logo for a coffee shop" --out logo.png --width 1024 --height 1024
    python3 gen.py "same prompt" --seed 42          # reproducible

No key required. Set POLLINATIONS_TOKEN to raise rate limits; anonymous access
is text-to-image only (image editing returns HTTP 500 without a token).
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://image.pollinations.ai/prompt/{prompt}"
DEFAULT_MODEL = "sana"
MAX_DIM = 2048
MIN_DIM = 64


def build_url(
    prompt: str,
    width: int,
    height: int,
    seed: int | None,
    model: str,
    nologo: bool,
    private: bool,
) -> str:
    params = {
        "width": width,
        "height": height,
        "model": model,
    }
    if seed is not None:
        params["seed"] = seed
    if nologo:
        params["nologo"] = "true"
    if private:
        params["private"] = "true"
    token = os.environ.get("POLLINATIONS_TOKEN")
    if token:
        params["token"] = token
    query = urllib.parse.urlencode(params)
    return ENDPOINT.format(prompt=urllib.parse.quote(prompt, safe="")) + "?" + query


def looks_like_image(data: bytes, content_type: str) -> bool:
    """Pollinations returns an HTML error page with HTTP 200 for bad params."""
    if content_type.startswith("image/"):
        return True
    return data[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1", b"RIFF") or data[:3] == b"\xff\xd8\xff"


MIN_PLAUSIBLE_BYTES = 4096


def generate(url: str, timeout: int = 180) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "imagegen-skill/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        data = resp.read()
    # A real render is always larger than this; a tiny payload is an error page or
    # a silent failure, even when the content type claims an image.
    if not looks_like_image(data, content_type) or len(data) < MIN_PLAUSIBLE_BYTES:
        head = data[:200].decode("utf-8", "replace").replace("\n", " ")
        raise SystemExit(
            f"ERROR: the endpoint did not return a usable image "
            f"({content_type or 'unknown type'}, {len(data)} bytes).\n"
            f"       First bytes: {head}\n"
            "       This usually means a rejected parameter or a rate limit. "
            "Try a simpler prompt, or a smaller size."
        )
    return data


def clamp_dim(value: int) -> int:
    if value < MIN_DIM or value > MAX_DIM:
        raise SystemExit(f"ERROR: --width/--height must be between {MIN_DIM} and {MAX_DIM}.")
    return value


def main() -> int:
    p = argparse.ArgumentParser(description="Generate an image from a text prompt.")
    p.add_argument("prompt", help="what to draw; be specific about subject, style, lighting")
    p.add_argument("--out", "-o", help="output path (default: generated.png, or generated-<seed>.png)")
    p.add_argument("--width", "-W", type=int, default=1024)
    p.add_argument("--height", "-H", type=int, default=1024)
    p.add_argument("--seed", "-s", type=int, help="fix the seed to reproduce the same image")
    p.add_argument("--model", "-m", default=DEFAULT_MODEL,
                   help=f"model name (default: {DEFAULT_MODEL}; anonymous access ignores this and uses {DEFAULT_MODEL})")
    p.add_argument("--no-logo", action="store_true", help="ask for no watermark (needs a token to be honoured)")
    p.add_argument("--private", action="store_true", help="request the image not be shown publicly (needs a token)")
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()

    if not args.prompt.strip():
        raise SystemExit("ERROR: the prompt is empty.")

    width, height = clamp_dim(args.width), clamp_dim(args.height)
    out = Path(args.out) if args.out else Path(
        f"generated-{args.seed}.png" if args.seed is not None else "generated.png"
    )

    url = build_url(args.prompt, width, height, args.seed, args.model, args.no_logo, args.private)
    data = generate(url, args.timeout)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)

    # The service downsizes large requests (1024 usually comes back as 768), so
    # report what was actually written rather than what was asked for.
    actual = ""
    try:
        from PIL import Image

        with Image.open(out) as im:
            actual = f", actually {im.width}x{im.height}"
            if (im.width, im.height) != (width, height):
                actual += " (the service capped the size)"
    except Exception:
        pass

    print(f"wrote {out} ({len(data) / 1024:.0f} KB, requested {width}x{height}{actual})")
    if not os.environ.get("POLLINATIONS_TOKEN"):
        print("note: no POLLINATIONS_TOKEN set - anonymous access is text-to-image only,")
        print("      the model/watermark/private options are not honoured, and limits are lower.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
