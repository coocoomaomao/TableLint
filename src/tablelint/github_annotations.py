from __future__ import annotations

from .models import Finding, Severity


_LEVEL = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFO: "notice",
}


def _escape_message(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def _escape_property(value: str) -> str:
    return (
        _escape_message(value)
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def format_annotation(finding: Finding) -> str:
    level = _LEVEL[finding.severity]
    properties = [
        f"file={_escape_property(str(finding.path))}",
        f"title={_escape_property(finding.code)}",
    ]
    if finding.line is not None:
        properties.append(f"line={finding.line}")

    location = []
    if finding.table:
        location.append(f"table={finding.table}")
    if finding.row is not None:
        location.append(f"row={finding.row}")
    if finding.column is not None:
        location.append(f"column={finding.column}")

    message = finding.message
    if location:
        message = f"[{', '.join(location)}] {message}"

    return (
        f"::{level} "
        + ",".join(properties)
        + "::"
        + _escape_message(message)
    )


def emit_annotations(findings: list[Finding]) -> None:
    for finding in findings:
        print(format_annotation(finding))
