#!/usr/bin/env python3
"""Verify deliverable files and print a Markdown delivery block.

Optionally bundle files and directories into a single zip archive so the user
has one attachment to download.

Usage:
    python3 delivery_manifest.py <path> [<path> ...] [--archive <archive-path>]
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def collect_files(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """Return (existing_files, missing_paths)."""
    files: list[Path] = []
    missing: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.is_file()))
        elif path.is_file():
            files.append(path)
        else:
            missing.append(path)
    return files, missing


def build_archive(paths: list[Path], archive: Path) -> Path:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            if path.is_dir():
                for file in sorted(path.rglob("*")):
                    if file.is_file():
                        zf.write(file, file.relative_to(path.parent))
            elif path.is_file():
                zf.write(path, path.name)
    return archive


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Files or directories to deliver")
    parser.add_argument("--archive", help="Create a zip archive at this path")
    parser.add_argument("--title", default="Deliverables", help="Heading for the block")
    args = parser.parse_args(argv)

    paths = [Path(p) for p in args.paths]
    files, missing = collect_files(paths)

    print(f"**{args.title}**")
    seen: set[Path] = set()
    for file in files:
        if file in seen:
            continue
        seen.add(file)
        print(f"- `{file.name}` ({human_size(file.stat().st_size)})")
        print(f"  Path: `{file.resolve()}`")

    existing = [p for p in paths if p.exists()]
    if args.archive and existing:
        archive = build_archive(existing, Path(args.archive))
        print(f"- Bundle: `{archive.name}` ({human_size(archive.stat().st_size)})")
        print(f"  Path: `{archive.resolve()}`")

    if missing:
        print()
        print("Missing paths (not created):")
        for path in missing:
            print(f"- `{path}`")

    print()
    print(
        "To download: open the Files tab in Agent Canvas, select the file, "
        "and choose Download."
    )
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
