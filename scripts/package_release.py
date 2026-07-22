#!/usr/bin/env python3
"""Create a deterministic checksum manifest and a GitHub-ready source ZIP."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST_SHA256.txt"
ARCHIVE = ROOT.parent / f"{ROOT.name}.zip"
EXCLUDED_PARTS = {".git", "tmp", "__pycache__"}


def included_files(include_manifest: bool) -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative == MANIFEST.relative_to(ROOT) and not include_manifest:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest() -> None:
    lines = [
        f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}"
        for path in included_files(include_manifest=False)
    ]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_archive() -> None:
    timestamp = (2026, 7, 21, 0, 0, 0)
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in included_files(include_manifest=True):
            relative = Path(ROOT.name) / path.relative_to(ROOT)
            info = ZipInfo(relative.as_posix(), timestamp)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o755 if os.access(path, os.X_OK) else 0o644) << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    write_manifest()
    write_archive()
    print(MANIFEST)
    print(ARCHIVE)


if __name__ == "__main__":
    main()
