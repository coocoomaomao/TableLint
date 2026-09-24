from __future__ import annotations

from pathlib import Path

from . import __version__
from .models import Finding, Severity


def summarize(findings: list[Finding]) -> dict[str, int]:
    return {
        "errors": sum(f.severity is Severity.ERROR for f in findings),
        "warnings": sum(f.severity is Severity.WARNING for f in findings),
        "info": sum(f.severity is Severity.INFO for f in findings),
    }


def json_report(
    target: Path,
    findings: list[Finding],
    *,
    file_count: int,
    table_count: int,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "tool": "TableLint",
        "tool_version": __version__,
        "target": str(target),
        "summary": {
            "files": file_count,
            "tables": table_count,
            **summarize(findings),
        },
        "findings": [
            {
                "path": str(finding.path),
                "table": finding.table,
                "row": finding.row,
                "column": finding.column,
                "line": finding.line,
                "severity": finding.severity.value,
                "code": finding.code,
                "message": finding.message,
            }
            for finding in findings
        ],
    }
