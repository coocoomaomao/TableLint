from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from .models import Finding, Severity, TableData


_PLACEHOLDERS = {"todo", "tbd", "???", "??", "fixme"}
_PERCENT_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*%\s*$")
_P_HEADER_RE = re.compile(r"^p(?:\s*[-_]?\s*(?:value|val))?$", re.IGNORECASE)
_P_VALUE_RE = re.compile(
    r"^\s*(?:p\s*)?(?:<=|>=|<|>|=|≤|≥)?\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


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
    return len(text.rsplit(".", 1)[1])


def check_table(table: TableData) -> list[Finding]:
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
            try:
                number = Decimal(match.group(1))
            except InvalidOperation:
                continue
            if number < 0 or number > 1:
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

    return findings
