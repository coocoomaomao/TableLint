from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .checks import check_table
from .discovery import collect_table_files
from .models import Severity
from .readers import read_file
from .reporting import json_report, summarize


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Lint academic tables before submission.",
)
console = Console()


@app.callback()
def main() -> None:
    """TableLint command group."""


@app.command()
def check(
    target: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="CSV, XLSX, LaTeX file, or directory to inspect.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit with code 1 when warnings are present.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text or json.",
    ),
) -> None:
    """Check one table file or recursively scan a directory."""
    output_format = output_format.lower()
    if output_format not in {"text", "json"}:
        raise typer.BadParameter("--format must be 'text' or 'json'.")

    files = collect_table_files(target)
    if not files:
        console.print("[yellow]No supported table files found.[/yellow]")
        raise typer.Exit(code=0)

    findings = []
    table_count = 0

    for path in files:
        result = read_file(path)
        findings.extend(result.findings)
        table_count += len(result.tables)
        for table_data in result.tables:
            findings.extend(check_table(table_data))

    counts = summarize(findings)

    if output_format == "json":
        typer.echo(
            json.dumps(
                json_report(
                    target,
                    findings,
                    file_count=len(files),
                    table_count=table_count,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        report = Table(title="TableLint")
        report.add_column("File", overflow="fold")
        report.add_column("Table", no_wrap=True)
        report.add_column("Cell", no_wrap=True)
        report.add_column("Severity")
        report.add_column("Code", no_wrap=True)
        report.add_column("Message", overflow="fold")

        if not findings:
            report.add_row(str(target), "—", "—", "pass", "OK", "No findings.")

        for finding in findings:
            cell_parts = []
            if finding.row is not None:
                cell_parts.append(f"R{finding.row}")
            if finding.column is not None:
                cell_parts.append(f"C{finding.column}")
            if finding.line is not None:
                cell_parts.append(f"L{finding.line}")
            report.add_row(
                str(finding.path),
                finding.table or "—",
                " ".join(cell_parts) or "—",
                finding.severity.value,
                finding.code,
                finding.message,
            )

        console.print(report)
        console.print(
            f"Checked {len(files)} file(s), {table_count} table(s): "
            f"{counts['errors']} error(s), {counts['warnings']} warning(s), "
            f"{counts['info']} info."
        )

    if counts["errors"]:
        raise typer.Exit(code=2)
    if strict and counts["warnings"]:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
