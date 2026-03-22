from __future__ import annotations

import atexit
import os
import sys
from typing import TextIO

from manana.hook import get_finder
from manana.lazy import LoadMetadata

_REGISTERED: bool = False


def _safe_ms(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    return f"{seconds * 1000:.3f}"


def _format_trigger_path(path: str) -> str:
    cwd = os.getcwd()
    try:
        relative = os.path.relpath(path, cwd)
    except ValueError:
        return path

    if relative == ".":
        return relative
    if relative.startswith(".."):
        return path
    return relative


def _build_lines(records: dict[str, LoadMetadata]) -> list[str]:
    lines: list[str] = []

    for name in sorted(records):
        metadata = records[name]
        if metadata.loaded:
            if metadata.trigger_file is not None and metadata.trigger_line is not None:
                trigger_path = _format_trigger_path(metadata.trigger_file)
                trigger = f"trigger={trigger_path}:{metadata.trigger_line}"
            else:
                trigger = ""
            lines.append(f"loaded  {name} in {_safe_ms(metadata.load_time)}ms ({trigger})")
        else:
            lines.append(f"ignored {name}")
    return lines


def report(stream: TextIO | None = None) -> None:
    target = stream if stream is not None else sys.stdout

    finder = get_finder()
    if finder is None:
        target.write("[manana] finder not active\n")
        return

    records = finder.records
    if not records:
        target.write("[manana] no ignored imports\n")
        return

    loaded = sum(1 for metadata in records.values() if metadata.loaded)
    deferred = len(records) - loaded

    target.write(f"[manana] total={len(records)} loaded={loaded} ignored={deferred}\n")
    target.write("\n".join(_build_lines(records)))
    target.write("\n")


def register_atexit_reporter(stream: TextIO | None = None) -> None:
    global _REGISTERED
    if _REGISTERED:
        return

    atexit.register(report, stream)
    _REGISTERED = True
