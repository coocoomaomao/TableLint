from __future__ import annotations

from pathlib import Path


SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".tex"}


def collect_table_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() in SUPPORTED_SUFFIXES else []

    return sorted(
        path
        for path in target.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )
