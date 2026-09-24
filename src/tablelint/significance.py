from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any

from .models import Finding, Severity, TableData


_P_HEADER_RE = re.compile(r"^p(?:\s*[-_]?\s*(?:value|val))?$", re.IGNORECASE)
_STAR_HEADER_RE = re.compile(
    r"^(?:stars?|sig(?:nificance)?|significance\s+stars?)$",
    re.IGNORECASE,
)
_EXACT_P_RE = re.compile(
    r"^\s*(?:p\s*)?=?\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$",
    re.IGNORECASE,
)
_MISSING_MARKERS = {"na", "n/a", "nan", "null", "none", "-", "—", "–"}
_ZERO_STAR_MARKERS = {"", "ns", "n.s.", "n.s", "not significant", "non-significant"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalized(value: Any) -> str:
    return " ".join(_text(value).casefold().split())


def parse_star_thresholds(raw: str) -> tuple[Decimal, ...]:
    """Parse comma-separated *, **, *** p-value thresholds.

    Thresholds must be strictly descending, e.g. 0.05,0.01,0.001.
    A star level means p is strictly less than its configured threshold.
    """
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise ValueError("provide at least one threshold")
    if len(parts) > 5:
        raise ValueError("at most five significance-star thresholds are supported")

    values: list[Decimal] = []
    for part in parts:
        try:
            value = Decimal(part)
        except InvalidOperation as exc:
            raise ValueError(f"invalid numeric threshold: {part}") from exc
        if value <= 0 or value >= 1:
            raise ValueError("thresholds must be greater than 0 and less than 1")
        values.append(value)

    if any(left <= right for left, right in zip(values, values[1:])):
        raise ValueError(
            "thresholds must be strictly descending, e.g. 0.05,0.01,0.001"
        )

    return tuple(values)


def _parse_exact_p(raw: str) -> Decimal | None:
    match = _EXACT_P_RE.fullmatch(raw)
    if match is None:
        return None
    try:
        value = Decimal(match.group(1))
    except InvalidOperation:
        return None
    if value < 0 or value > 1:
        return None
    return value


def _parse_star_count(raw: str) -> int | None:
    text = _text(raw)
    normalized = _normalized(raw)

    if normalized in _ZERO_STAR_MARKERS:
        return 0
    if normalized in _MISSING_MARKERS:
        return None

    text = text.replace("$", "").replace(" ", "")
    text = text.replace(r"\ast", "*")
    if text and set(text) == {"*"}:
        return len(text)
    return -1


def _threshold_description(thresholds: tuple[Decimal, ...]) -> str:
    return ", ".join(
        f"{'*' * index}: p < {threshold}"
        for index, threshold in enumerate(thresholds, start=1)
    )


def check_significance(
    table: TableData,
    thresholds: tuple[Decimal, ...],
) -> list[Finding]:
    """Compare exact numeric p-values with a clearly labeled star column.

    This rule is opt-in because star conventions vary across journals and fields.
    """
    p_columns = [
        index
        for index, header in enumerate(table.headers)
        if _P_HEADER_RE.fullmatch(_normalized(header))
    ]
    star_columns = [
        index
        for index, header in enumerate(table.headers)
        if _STAR_HEADER_RE.fullmatch(_normalized(header))
    ]

    if len(p_columns) != 1 or len(star_columns) != 1:
        return []

    p_index = p_columns[0]
    star_index = star_columns[0]
    findings: list[Finding] = []
    convention = _threshold_description(thresholds)

    for row_index, row in enumerate(table.rows, start=2):
        p_raw = _text(row[p_index] if p_index < len(row) else None)
        star_raw = _text(row[star_index] if star_index < len(row) else None)

        # Comparator forms such as <0.05 are intentionally skipped because they
        # may not determine a unique star count at all configured levels.
        p_value = _parse_exact_p(p_raw)
        if p_value is None:
            continue

        observed = _parse_star_count(star_raw)
        if observed is None:
            continue
        if observed == -1 or observed > len(thresholds):
            findings.append(
                Finding(
                    path=table.path,
                    severity=Severity.WARNING,
                    code="SIGNIFICANCE_STAR_FORMAT",
                    message=(
                        f"Significance marker '{star_raw}' is not valid for the "
                        f"configured {len(thresholds)}-level convention."
                    ),
                    table=table.name,
                    row=row_index,
                    column=star_index + 1,
                )
            )
            continue

        expected = sum(p_value < threshold for threshold in thresholds)
        if observed != expected:
            findings.append(
                Finding(
                    path=table.path,
                    severity=Severity.WARNING,
                    code="SIGNIFICANCE_STAR_MISMATCH",
                    message=(
                        f"p-value {p_value} implies {'*' * expected or 'no stars'} "
                        f"but the table shows {'*' * observed or 'no stars'} "
                        f"under the configured convention ({convention})."
                    ),
                    table=table.name,
                    row=row_index,
                    column=star_index + 1,
                )
            )

    return findings
