import json
from pathlib import Path

from typer.testing import CliRunner

from tablelint.cli import app


runner = CliRunner()


def test_help_lists_check_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.stdout


def test_check_clean_csv(tmp_path: Path) -> None:
    path = tmp_path / "good.csv"
    path.write_text("group,value\nA,1.0\nB,2.0\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(path)])

    assert result.exit_code == 0
    assert "1 table(s)" in result.stdout


def test_strict_fails_on_warning(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("group,rate\nA,150%\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(path), "--strict"])

    assert result.exit_code == 1
    assert "PERCENT_OUT_OF_RANGE" in result.stdout


def test_json_output_is_machine_readable(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("group,p-value\nA,2.0\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(path), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1
    assert payload["tool"] == "TableLint"
    assert payload["summary"]["warnings"] == 1
    assert payload["findings"][0]["code"] == "P_VALUE_OUT_OF_RANGE"
