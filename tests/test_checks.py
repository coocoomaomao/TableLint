from pathlib import Path

from tablelint.checks import check_table
from tablelint.models import Severity, TableData


def table(headers, rows, source_kind: str = "csv") -> TableData:
    return TableData(
        path=Path("results.csv"),
        name="results",
        headers=headers,
        rows=rows,
        source_kind=source_kind,
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


def test_mean_plus_minus_sd_format_is_checked_when_header_declares_it() -> None:
    findings = check_table(
        table(
            ["Group", "Mean ± SD"],
            [
                ["A", "12.3 ± 1.4"],
                ["B", "10.2"],
                ["C", "9.8 ± -0.4"],
            ],
        )
    )

    assert codes(findings).count("SUMMARY_STAT_FORMAT") == 1
    assert codes(findings).count("SUMMARY_SPREAD_NEGATIVE") == 1


def test_mean_parenthesized_sd_format_is_supported() -> None:
    findings = check_table(
        table(
            ["Mean (SD)"],
            [["12.3 (1.4)"], ["10.2 (0.8)"]],
        )
    )

    assert "SUMMARY_STAT_FORMAT" not in codes(findings)


def test_latex_pm_summary_format_is_supported() -> None:
    findings = check_table(
        table(
            ["Mean \\pm SEM"],
            [["$12.3 \\pm 1.4$"]],
            source_kind="latex",
        )
    )

    assert "SUMMARY_STAT_FORMAT" not in codes(findings)


def test_confidence_interval_reversed_bounds_are_detected() -> None:
    findings = check_table(
        table(
            ["95% CI"],
            [["[1.2, 3.4]"], ["5.0–2.0"], ["-1.0 to 2.0"]],
        )
    )

    reversed_findings = [f for f in findings if f.code == "CI_BOUNDS_REVERSED"]
    assert len(reversed_findings) == 1
    assert reversed_findings[0].row == 3


def test_malformed_confidence_interval_is_warning() -> None:
    findings = check_table(
        table(["Confidence interval"], [["1.2"], ["[1.0, 2.0]"]])
    )

    invalid = [f for f in findings if f.code == "CI_FORMAT_INVALID"]
    assert len(invalid) == 1
    assert invalid[0].row == 2


def test_paired_ci_lower_upper_columns_are_compared() -> None:
    findings = check_table(
        table(
            ["Estimate", "95% CI lower", "95% CI upper"],
            [
                ["A", "1.2", "3.4"],
                ["B", "5.0", "2.0"],
            ],
        )
    )

    reversed_findings = [f for f in findings if f.code == "CI_BOUNDS_REVERSED"]
    assert len(reversed_findings) == 1
    assert reversed_findings[0].row == 3


def test_missing_markers_do_not_trigger_summary_or_ci_format_warnings() -> None:
    findings = check_table(
        table(
            ["Mean ± SD", "95% CI"],
            [["NA", "—"], ["12.0 ± 1.0", "[10.0, 14.0]"]],
        )
    )

    assert "SUMMARY_STAT_FORMAT" not in codes(findings)
    assert "CI_FORMAT_INVALID" not in codes(findings)
