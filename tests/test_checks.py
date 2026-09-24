from pathlib import Path

from tablelint.checks import check_table
from tablelint.models import Severity, TableData


def table(headers, rows) -> TableData:
    return TableData(
        path=Path("results.csv"),
        name="results",
        headers=headers,
        rows=rows,
        source_kind="csv",
    )


def codes(findings) -> list[str]:
    return [finding.code for finding in findings]


def test_header_column_and_placeholder_checks() -> None:
    findings = check_table(
        table(
            ["group", "", "group", "notes"],
            [
                ["A", "", "A", "TODO"],
                ["B", "", "B", "ok"],
            ],
        )
    )

    assert "EMPTY_HEADER" in codes(findings)
    assert "DUPLICATE_HEADER" in codes(findings)
    assert "EMPTY_COLUMN" in codes(findings)
    assert "PLACEHOLDER_VALUE" in codes(findings)


def test_percent_out_of_range() -> None:
    findings = check_table(
        table(["rate"], [["95%"], ["135%"], ["-2%"]])
    )

    outliers = [f for f in findings if f.code == "PERCENT_OUT_OF_RANGE"]
    assert len(outliers) == 2
    assert all(f.severity is Severity.WARNING for f in outliers)


def test_p_value_range_only_applies_to_p_columns() -> None:
    findings = check_table(
        table(
            ["p-value", "measurement"],
            [["0.04", "4.2"], ["1.4", "1.4"], ["<0.001", "9.0"]],
        )
    )

    p_findings = [f for f in findings if f.code == "P_VALUE_OUT_OF_RANGE"]
    assert len(p_findings) == 1
    assert p_findings[0].row == 3
    assert p_findings[0].column == 1


def test_duplicate_row_is_informational() -> None:
    findings = check_table(
        table(["group", "value"], [["A", "1.0"], ["A", "1.0"]])
    )

    finding = next(f for f in findings if f.code == "DUPLICATE_ROW")
    assert finding.severity is Severity.INFO


def test_decimal_precision_mixed_is_informational() -> None:
    findings = check_table(
        table(
            ["mean"],
            [["1.20"], ["2.30"], ["3.40"], ["4.50"], ["5.678"]],
        )
    )

    finding = next(f for f in findings if f.code == "DECIMAL_PRECISION_MIXED")
    assert finding.severity is Severity.INFO
