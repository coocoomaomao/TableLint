from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Finding:
    path: Path
    severity: Severity
    code: str
    message: str
    table: str | None = None
    row: int | None = None
    column: int | None = None
    line: int | None = None


@dataclass
class TableData:
    path: Path
    name: str
    headers: list[Any]
    rows: list[list[Any]]
    source_kind: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReadResult:
    tables: list[TableData] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
