from pathlib import Path

from tablelint.github_annotations import format_annotation
from tablelint.models import Finding, Severity


def test_annotation_includes_table_cell_context() -> None:
    finding = Finding(
        path=Path("tables/results.csv"),
        severity=Severity.WARNING,
        code="P_VALUE_OUT_OF_RANGE",
        message="p-value is outside range.",
        table="results",
        row=3,
        column=2,
    )

    rendered = format_annotation(finding)

    assert rendered.startswith(
        "::warning file=tables/results.csv,title=P_VALUE_OUT_OF_RANGE::"
    )
    assert "[table=results, row=3, column=2]" in rendered


def test_annotation_escapes_workflow_command_characters() -> None:
    finding = Finding(
        path=Path("tables/a,b.tex"),
        severity=Severity.ERROR,
        code="BAD:TABLE",
        message="bad%value\nnext",
        line=8,
    )

    rendered = format_annotation(finding)

    assert "file=tables/a%2Cb.tex" in rendered
    assert "title=BAD%3ATABLE" in rendered
    assert "line=8" in rendered
    assert "bad%25value%0Anext" in rendered
