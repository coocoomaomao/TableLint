import json
from pathlib import Path

from typer.testing import CliRunner

from tablelint.cli import app


runner = CliRunner()


def test_star_thresholds_enable_consistency_check(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    path.write_text(
        "group,p-value,stars\nA,0.008,*\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "check",
            str(path),
            "--star-thresholds",
            "0.05,0.01,0.001",
        ],
    )

    assert result.exit_code == 0
    assert "SIGNIFICANCE_STAR_MISMATCH" in result.stdout


def test_invalid_star_thresholds_fail_fast(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    path.write_text("p-value,stars\n0.01,**\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["check", str(path), "--star-thresholds", "0.01,0.05"],
    )

    assert result.exit_code != 0
    assert "strictly descending" in result.output


def test_json_and_github_annotations_are_mutually_exclusive(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    path.write_text("group,value\nA,1\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["check", str(path), "--format", "json", "--github-annotations"],
    )

    assert result.exit_code != 0
    assert "invalid JSON" in result.output
