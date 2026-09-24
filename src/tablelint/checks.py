from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from .models import Finding, Severity, TableData
from .significance import check_significance


_PLACEHOLDERS = {"todo", "tbd", "???", "??", "fixme"}
_MISSING_MARKERS = {"", "na", "n/a", "nan", "null", "none", "-", "—", "–"}
_PERCENT_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*%\s*$")
_P_HEADER_RE = re.compile(r"^p(?:\s*[-_]?\s*(?:value|val))?$", re.IGNORECASE)
_P_VALUE_RE = re.compile(
    r"^\s*(?:p\s*)?(?:<=|>=|<|>|=|≤|≥)?\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$",
    re.IGNORECASE,
)
_NUMBER_TOKEN = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_NUMBER_RE = re.compile(rf"^{_NUMBER_TOKEN}$")

_PM_HEADER_RE = re.compile(
    r"(?:\bmean\b|\baverage\b)?\s*(?:±|\\pm)\s*"
    r"(?:sd|s\.?d\.?|sem|se)\b",
    re.IGNORECASE,
)
_PAREN_STAT_HEADER_RE = re.compile(
    r"(?:\bmean\b|\baverage\b)\s*\(\s*(?:sd|s\.?d\.?|sem|se)\s*\)",
    re.IGNORECASE,
)
_PM_VALUE_RE = re.compile(
    rf"^\s*\$?\s*({_NUMBER_TOKEN})\s*(?:±|\\pm)\s*"
    rf"({_NUMBER_TOKEN})\s*\$?\s*$"
)
_PAREN_STAT_VALUE_RE = re.compile(
    rf"^\s*\$?\s*({_NUMBER_TOKEN})\s*\(\s*({_NUMBER_TOKEN})\s*\)"
    r"\s*\$?\s*$"
)

_CI_HEADER_RE = re.compile(r"(?:\bci\b|confidence\s+interval)", re.IGNORECASE)
_CI_BRACKET_RE = re.compile(
    rf"^\s*\$?\s*[\[(]?\s*({_NUMBER_TOKEN})\s*[,;]\s*"
    rf"({_NUMBER_TOKEN})\s*[\])]?\s*\$?\s*$"
)
_CI_RANGE_RE = re.compile(
    rf"^\s*\$?\s*({_NUMBER_TOKEN})\s*"
    rf"(?:–|—|\s+-\s+|\s+to\s+)\s*({_NUMBER_TOKEN})"
    r"\s*\$?\s*$",
    re.IGNORECASE,
)
_CI_LOWER_RE = re.compile(r"(?:\blower\b|\blcl\b|lower\s+bound)", re.IGNORECASE)
_CI_UPPER_RE = re.compile(r"(?:\bupper\b|\bucl\b|upper\s+bound)", re.IGNORECASE)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalized(value: Any) -> str:
    return " ".join(_text(value).casefold().split())


def _column_count(table: TableData) -> int:
    return max(
        [len(table.headers), *(len(row) for row in table.rows)],
        default=0,
    )


def _cell(table: TableData, row: list[Any], index: int) -> Any:
    return row[index] if index < len(row) else None


def _decimal_places(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    text = _text(value)
    if not _NUMBER_RE.fullmatch(text) or "." not in text:
        return None
    mantissa = re.split(r"[eE]", text, maxsplit=1)[0]
    if "." not in mantissa:
        return None
    return len(mantissa.rsplit(".", 1)[1])


def _to_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _summary_style(header: Any) -> str | None:
    text = _text(header)
    if _PM_HEADER_RE.search(text):
        return "plusminus"
    if _PAREN_STAT_HEADER_RE.search(text):
        return "parentheses"
    return None


def _parse_summary_value(raw: str, style: str) -> tuple[Decimal, Decimal] | None:
    pattern = _PM_VALUE_RE if style == "plusminus" else _PAREN_STAT_VALUE_RE
    match = pattern.fullmatch(raw)
    if match is None:
        return None
    center = _to_decimal(match.group(1))
    spread = _to_decimal(match.group(2))
    if center is None or spread is None:
        return None
    return center, spread


def _parse_ci(raw: str) -> tuple[Decimal, Decimal] | None:
    for pattern in (_CI_BRACKET_RE, _CI_RANGE_RE):
        match = pattern.fullmatch(raw)
        if match is None:
            continue
        lower = _to_decimal(match.group(1))
        upper = _to_decimal(match.group(2))
        if lower is not None and upper is not None:
            return lower, upper
    return None


def _ci_role(header: Any) -> str | None:
    text = _text(header)
    if not _CI_HEADER_RE.search(text):
        return None
    if _CI_LOWER_RE.search(text):
        return "lower"
    if _CI_UPPER_RE.search(text):
        return "upper"
    return "interval"


def check_table(
    table: TableData,
    *,
    star_thresholds: tuple[Decimal, ...] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    width = _column_count(table)

    if width == 0:
        return [
            Finding(
                table.path,
                Severity.WARNING,
                "EMPTY_TABLE",
                "Table contains no columns.",
                table=table.name,
            )
        ]

    headers = [
        table.headers[index] if index < len(table.headers) else None
        for index in range(width)
    ]

    if table.source_kind in {"csv", "xlsx"}:
        for index, header in enumerate(headers, start=1):
            if not _text(header):
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "EMPTY_HEADER",
                        f"Column {index} has an empty header.",
                        table=table.name,
                        column=index,
                    )
                )

        header_locations: dict[str, list[int]] = defaultdict(list)
        for index, header in enumerate(headers, start=1):
            normalized = _normalized(header)
            if normalized:
                header_locations[normalized].append(index)

        for normalized, columns in sorted(header_locations.items()):
            if len(columns) > 1:
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "DUPLICATE_HEADER",
                        f"Header '{normalized}' appears in columns {columns}.",
                        table=table.name,
                    )
                )

        for index in range(width):
            values = [_cell(table, row, index) for row in table.rows]
            if values and all(not _text(value) for value in values):
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "EMPTY_COLUMN",
                        f"Column {index + 1} contains no data values.",
                        table=table.name,
                        column=index + 1,
                    )
                )

    seen_rows: dict[tuple[str, ...], int] = {}
    duplicate_pairs: list[tuple[int, int]] = []

    for row_index, row in enumerate(table.rows, start=2):
        normalized_row = tuple(
            _normalized(_cell(table, row, index))
            for index in range(width)
        )
        if any(normalized_row):
            if normalized_row in seen_rows:
                duplicate_pairs.append((seen_rows[normalized_row], row_index))
            else:
                seen_rows[normalized_row] = row_index

        for column_index in range(width):
            value = _cell(table, row, column_index)
            normalized = _normalized(value)

            if normalized in _PLACEHOLDERS:
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "PLACEHOLDER_VALUE",
                        f"Placeholder value '{_text(value)}' remains in the table.",
                        table=table.name,
                        row=row_index,
                        column=column_index + 1,
                    )
                )

            percent = _PERCENT_RE.fullmatch(_text(value))
            if percent:
                number = Decimal(percent.group(1))
                if number < 0 or number > 100:
                    findings.append(
                        Finding(
                            table.path,
                            Severity.WARNING,
                            "PERCENT_OUT_OF_RANGE",
                            f"Percentage value {_text(value)} is outside 0–100%.",
                            table=table.name,
                            row=row_index,
                            column=column_index + 1,
                        )
                    )

    if duplicate_pairs:
        pairs = ", ".join(f"{first}/{second}" for first, second in duplicate_pairs[:5])
        suffix = "" if len(duplicate_pairs) <= 5 else " …"
        findings.append(
            Finding(
                table.path,
                Severity.INFO,
                "DUPLICATE_ROW",
                f"Exact duplicate data rows detected (row pairs {pairs}{suffix}).",
                table=table.name,
            )
        )

    for index, header in enumerate(headers):
        if not _P_HEADER_RE.fullmatch(_normalized(header)):
            continue
        for row_index, row in enumerate(table.rows, start=2):
            raw = _text(_cell(table, row, index))
            if not raw:
                continue
            match = _P_VALUE_RE.fullmatch(raw)
            if match is None:
                continue
            number = _to_decimal(match.group(1))
            if number is not None and (number < 0 or number > 1):
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "P_VALUE_OUT_OF_RANGE",
                        f"p-value '{raw}' is outside the valid 0–1 range.",
                        table=table.name,
                        row=row_index,
                        column=index + 1,
                    )
                )

    # Summary-statistic format checks only activate when the header explicitly
    # declares a combined mean ± SD/SEM or Mean (SD/SEM) representation.
    for index, header in enumerate(headers):
        style = _summary_style(header)
        if style is None:
            continue
        expected = "mean ± SD/SEM" if style == "plusminus" else "Mean (SD/SEM)"
        for row_index, row in enumerate(table.rows, start=2):
            raw = _text(_cell(table, row, index))
            if _normalized(raw) in _MISSING_MARKERS:
                continue
            parsed = _parse_summary_value(raw, style)
            if parsed is None:
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "SUMMARY_STAT_FORMAT",
                        f"Value '{raw}' does not match the header-declared {expected} format.",
                        table=table.name,
                        row=row_index,
                        column=index + 1,
                    )
                )
                continue
            _, spread = parsed
            if spread < 0:
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "SUMMARY_SPREAD_NEGATIVE",
                        f"Spread value in '{raw}' is negative; SD/SEM cannot be negative.",
                        table=table.name,
                        row=row_index,
                        column=index + 1,
                    )
                )

    # Single-column confidence intervals are validated only for headers that
    # explicitly mention CI / confidence interval.
    ci_roles = [_ci_role(header) for header in headers]
    for index, role in enumerate(ci_roles):
        if role != "interval":
            continue
        for row_index, row in enumerate(table.rows, start=2):
            raw = _text(_cell(table, row, index))
            if _normalized(raw) in _MISSING_MARKERS:
                continue
            parsed = _parse_ci(raw)
            if parsed is None:
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "CI_FORMAT_INVALID",
                        f"Confidence interval '{raw}' has an unrecognized two-bound format.",
                        table=table.name,
                        row=row_index,
                        column=index + 1,
                    )
                )
                continue
            lower, upper = parsed
            if lower > upper:
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "CI_BOUNDS_REVERSED",
                        f"Confidence interval lower bound {lower} exceeds upper bound {upper}.",
                        table=table.name,
                        row=row_index,
                        column=index + 1,
                    )
                )

    lower_columns = [i for i, role in enumerate(ci_roles) if role == "lower"]
    upper_columns = [i for i, role in enumerate(ci_roles) if role == "upper"]
    if len(lower_columns) == 1 and len(upper_columns) == 1:
        lower_index = lower_columns[0]
        upper_index = upper_columns[0]
        for row_index, row in enumerate(table.rows, start=2):
            lower_raw = _text(_cell(table, row, lower_index))
            upper_raw = _text(_cell(table, row, upper_index))
            if (
                _normalized(lower_raw) in _MISSING_MARKERS
                or _normalized(upper_raw) in _MISSING_MARKERS
            ):
                continue
            lower = _to_decimal(lower_raw) if _NUMBER_RE.fullmatch(lower_raw) else None
            upper = _to_decimal(upper_raw) if _NUMBER_RE.fullmatch(upper_raw) else None
            if lower is not None and upper is not None and lower > upper:
                findings.append(
                    Finding(
                        table.path,
                        Severity.WARNING,
                        "CI_BOUNDS_REVERSED",
                        (
                            f"Confidence interval lower bound {lower} exceeds "
                            f"upper bound {upper}."
                        ),
                        table=table.name,
                        row=row_index,
                    )
                )

    if table.source_kind in {"csv", "xlsx"}:
        for index in range(width):
            places = [
                places
                for row in table.rows
                if (places := _decimal_places(_cell(table, row, index))) is not None
            ]
            if len(places) < 4 or len(set(places)) < 2:
                continue
            counts = Counter(places)
            mode_places, mode_count = counts.most_common(1)[0]
            if mode_count / len(places) >= 0.6:
                variants = sorted(set(places))
                findings.append(
                    Finding(
                        table.path,
                        Severity.INFO,
                        "DECIMAL_PRECISION_MIXED",
                        (
                            f"Column {index + 1} mixes decimal precision {variants}; "
                            f"most values use {mode_places} decimal place(s)."
                        ),
                        table=table.name,
                        column=index + 1,
                    )
                )

    if star_thresholds:
        findings.extend(check_significance(table, star_thresholds))

    return findings
