from decimal import Decimal
from pathlib import Path

import pytest

from tablelint.models import TableData
from tablelint.significance import check_significance, parse_star_thresholds


def table(headers, rows) -> TableData:
    return TableData(
        path=Path("results.csv"),
        name="results",
        headers=headers,
        rows=rows,
        source_kind="csv",
    )


def test_parse_star_thresholds_requires_descending_values() -> None:
    assert parse_star_thresholds("0.05,0.01,0.001") == (
        Decimal("0.05"),
        Decimal("0.01"),
        Decimal("0.001"),
    )

    with pytest.raises(ValueError):
        parse_star_thresholds("0.01,0.05")


def test_star_mismatch_is_reported_with_explicit_convention() -> None:
    findings = check_significance(
        table(
            ["group", "p-value", "significance"],
            [
                ["A", "0.04", "*"],
                ["B", "0.008", "*"],
                ["C", "0.0005", "***"],
                ["D", "0.2", ""],
            ],
        ),
        parse_star_thresholds("0.05,0.01,0.001"),
    )

    mismatches = [f for f in findings if f.code == "SIGNIFICANCE_STAR_MISMATCH"]
    assert len(mismatches) == 1
    assert mismatches[0].row == 3
    assert "0.05" in mismatches[0].message


def test_comparator_p_values_are_skipped_conservatively() -> None:
    findings = check_significance(
        table(
            ["p", "stars"],
            [["<0.05", "*"], ["<0.001", "***"]],
        ),
        parse_star_thresholds("0.05,0.01,0.001"),
    )

    assert findings == []


def test_invalid_star_marker_is_reported() -> None:
    findings = check_significance(
        table(["p-value", "stars"], [["0.04", "****"]]),
        parse_star_thresholds("0.05,0.01,0.001"),
    )

    assert [f.code for f in findings] == ["SIGNIFICANCE_STAR_FORMAT"]
