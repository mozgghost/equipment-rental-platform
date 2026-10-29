#!/usr/bin/env python3
"""Create a deterministic, secret-aware source ZIP for the project."""
from __future__ import annotations

import hashlib
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / f"{ROOT.name}.zip"
FIXED_TIMESTAMP = (2026, 10, 26, 0, 0, 0)
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "dist", ".pytest_cache", "__pycache__",
    ".ruff_cache", ".mypy_cache", ".vite", "htmlcov", "coverage", "playwright-report",
    "test-results",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pem", ".key", ".sqlite3", ".log"}
EXCLUDED_NAMES = {".env", ".coverage", "package-lock.json.tmp"}


def include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    name = path.name
    if name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    # Allow only the safe example config; never include local or production env files.
    if name.startswith(".env") and name != ".env.example":
        return False
    if path.is_symlink() or not path.is_file():
        return False
    return True


def main() -> None:
    files = sorted(p for p in ROOT.rglob("*") if include(p))
    if not files:
        raise SystemExit("No project files found; refusing to create an empty archive.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{ROOT.name}/{relative}", date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.flag_bits |= 0x800  # UTF-8 names
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    with zipfile.ZipFile(OUTPUT, "r") as archive:
        bad_member = archive.testzip()
        names = archive.namelist()
        if bad_member:
            raise SystemExit(f"ZIP CRC validation failed for {bad_member}")
        required = {f"{ROOT.name}/README.md", f"{ROOT.name}/.env.example", f"{ROOT.name}/backend/config/settings.py"}
        missing = required.difference(names)
        if missing:
            raise SystemExit(f"Archive is missing required files: {sorted(missing)}")
        forbidden = [n for n in names if "/.env" in n and not n.endswith("/.env.example")]
        forbidden += [n for n in names if any(part in EXCLUDED_DIRS for part in Path(n).parts)]
        if forbidden:
            raise SystemExit(f"Forbidden files found in archive: {forbidden[:10]}")

    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"Archive: {OUTPUT}")
    print(f"Files: {len(files)}")
    print(f"Size: {OUTPUT.stat().st_size} bytes")
    print(f"SHA-256: {digest}")
    print("ZIP CRC, required-file and secret/cache exclusion checks: PASS")


if __name__ == "__main__":
    main()
