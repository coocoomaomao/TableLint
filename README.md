# TableLint 🐈‍⬛📊

<p>
  <a href="https://pypi.org/project/tablelint/"><img src="https://img.shields.io/pypi/v/tablelint" alt="PyPI"></a>
  <a href="https://github.com/coocoomaomao/TableLint/releases/tag/v0.1.0"><img src="https://img.shields.io/github/v/release/coocoomaomao/TableLint" alt="GitHub release"></a>
  <a href="https://github.com/coocoomaomao/TableLint/actions/workflows/ci.yml"><img src="https://github.com/coocoomaomao/TableLint/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/pypi/pyversions/tablelint" alt="Python versions">
  <img src="https://img.shields.io/github/license/coocoomaomao/TableLint" alt="MIT License">
</p>

> **ESLint for academic tables.**

**TableLint** is an open-source linter for academic tables. It helps researchers catch deterministic data-quality and formatting problems before submission.

Part of **喵造实验室 / MeowBuild Lab** and the Academic Lint family:

- **FigureLint** — figure QA
- **RefLint** — reference QA
- **TableLint** — table QA
- **ManuscriptLint** — manuscript preflight

## Current checks

### CSV / XLSX

- empty column headers
- duplicate column headers
- entirely empty columns
- leftover placeholders such as `TODO`, `TBD`, `???`, and `FIXME`
- exact duplicate data rows (informational)
- explicit percentage values outside 0–100%
- numeric p-values outside 0–1 in clearly named p-value columns
- mixed decimal precision when one precision clearly dominates (informational)
- **header-declared Mean ± SD / SEM formatting**
- **header-declared Mean (SD / SEM) formatting**
- negative SD / SEM spread values
- **confidence-interval syntax and bound ordering**
- paired CI lower / upper column ordering
- opt-in significance-star ↔ exact p-value consistency checks

Summary-statistic checks only activate when the column header explicitly declares a combined representation such as `Mean ± SD` or `Mean (SEM)`. Confidence-interval checks only activate for headers that explicitly contain `CI` or `confidence interval`.

### LaTeX

- `table` environments without captions
- missing table labels (informational)
- missing `tabular` inside a table
- inconsistent simple row widths
- standalone `tabular` environments
- summary-statistic / CI cell checks when headers explicitly declare them

TableLint deliberately avoids claiming that a duplicated row or mixed decimal precision is scientifically wrong. Those cases are surfaced as information because they may be intentional.

## Install

Requires Python 3.10+.

### PyPI

~~~bash
pip install tablelint
~~~

Verify the installation:

~~~bash
tablelint --help
~~~

### From source

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

~~~bash
tablelint check results.csv
tablelint check results.xlsx
tablelint check tables.tex
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

Enable a project-specific significance-star convention explicitly:

~~~bash
tablelint check results.csv --star-thresholds 0.05,0.01,0.001
~~~

The thresholds map to `*`, `**`, and `***` using strict `p < threshold` comparisons. Comparator p-values such as `<0.05` are skipped by this rule when they do not determine a unique star count.

Emit native GitHub Actions annotations:

~~~bash
tablelint check tables/ --github-annotations
~~~

### GitHub Actions

Pin the Action to the published release:

~~~yaml
- uses: coocoomaomao/TableLint@v0.1.0
  with:
    path: tables/
    strict: "true"
~~~

See [GitHub Action usage](docs/GITHUB_ACTION.md).

## Exit codes

- `0`: no structural errors; warnings are allowed unless `--strict` is used
- `1`: warnings found in strict mode
- `2`: unreadable / structural file errors

## Philosophy

TableLint separates:

1. **deterministic problems** — malformed/unreadable files, impossible ranges, reversed CI bounds, negative SD/SEM,
2. **likely formatting issues** — empty headers, placeholders, declared summary-statistic/CI syntax mismatches, LaTeX structure,
3. **context-dependent signals** — duplicates and precision consistency.

The third category stays informational by default. TableLint does not judge whether a reported mean, SD, SEM, CI width, or p-value is scientifically plausible.

## Release

The first public release, **TableLint v0.1.0**, is now available.

- [PyPI package](https://pypi.org/project/tablelint/)
- [GitHub release](https://github.com/coocoomaomao/TableLint/releases/tag/v0.1.0)
- [v0.1.0 release notes](docs/releases/v0.1.0.md)
- [Publishing guide](docs/PUBLISHING.md)

## Planned next

- optional unit consistency
- configurable missing-value policy
- ManuscriptLint integration

## License

MIT
