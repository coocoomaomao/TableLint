# TableLint 🐈‍⬛📊

> **ESLint for academic tables.**

**TableLint** is an open-source linter for academic tables. It helps researchers catch deterministic data-quality and formatting problems before submission.

Part of **喵造实验室 / MeowBuild Lab** and the Academic Lint family:

- **FigureLint** — figure QA
- **RefLint** — reference QA
- **TableLint** — table QA
- **ManuscriptLint** — manuscript preflight

## What v0.1 checks

### CSV / XLSX

- empty column headers
- duplicate column headers
- entirely empty columns
- leftover placeholders such as `TODO`, `TBD`, `???`, and `FIXME`
- exact duplicate data rows (informational)
- explicit percentage values outside 0–100%
- numeric p-values outside 0–1 in clearly named p-value columns
- mixed decimal precision when one precision clearly dominates (informational)

### LaTeX

- `table` environments without captions
- missing table labels (informational)
- missing `tabular` inside a table
- inconsistent simple row widths
- standalone `tabular` environments

TableLint deliberately avoids claiming that a duplicated row or mixed decimal precision is scientifically wrong. Those cases are surfaced as information because they may be intentional.

## Install from source

Requires Python 3.10+.

~~~bash
git clone https://github.com/coocoomaomao/TableLint.git
cd TableLint
python -m venv .venv
pip install -e .
~~~

For development:

~~~bash
pip install -e ".[dev]"
pytest
~~~

## Usage

Check one CSV:

~~~bash
tablelint check results.csv
~~~

Check one Excel workbook:

~~~bash
tablelint check results.xlsx
~~~

Check a LaTeX table file:

~~~bash
tablelint check tables.tex
~~~

Scan a directory recursively:

~~~bash
tablelint check tables/
~~~

Fail CI when warnings exist:

~~~bash
tablelint check tables/ --strict
~~~

Machine-readable output:

~~~bash
tablelint check tables/ --format json
~~~

## Exit codes

- `0`: no structural errors; warnings are allowed unless `--strict` is used
- `1`: warnings found in strict mode
- `2`: unreadable / structural file errors

## Philosophy

TableLint separates:

1. **deterministic problems** — malformed/unreadable files and clearly invalid ranges,
2. **likely formatting issues** — empty headers, placeholders, LaTeX structure,
3. **context-dependent signals** — duplicates and precision consistency.

The third category stays informational by default.

## Planned next

- mean ± SD / SEM formatting
- confidence interval checks
- significance-star vs p-value consistency
- optional unit consistency
- GitHub Actions annotations
- ManuscriptLint integration

## License

MIT
