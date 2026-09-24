# TableLint 🐈‍⬛📊

> **ESLint for academic tables.**

**TableLint** is an open-source linter for academic tables. It helps researchers catch deterministic data-quality and formatting problems before submission.

Part of **喵造实验室 / MeowBuild Lab** and the Academic Lint family:

- **FigureLint** — figure QA
- **RefLint** — reference QA
- **TableLint** — table QA
- **ManuscriptLint** — manuscript preflight

## v0.1 scope

TableLint starts with checks that can be made conservatively and repeatably:

- CSV / XLSX / LaTeX table input
- empty and duplicate column headers
- entirely empty columns
- placeholder values such as TODO / TBD / ???
- exact duplicate rows
- percentage values outside 0–100%
- p-values outside the valid 0–1 range
- suspicious decimal-place inconsistency in numeric columns
- LaTeX tabular row-width mismatches
- LaTeX tables missing captions or labels
- recursive directory scanning
- strict mode and CI-friendly exit codes
- machine-readable JSON output

## Philosophy

TableLint should flag verifiable table problems without pretending to understand the scientific meaning of a dataset. Checks that require domain context should stay informational or out of the default ruleset.

## Planned CLI

~~~bash
tablelint check results.xlsx
tablelint check tables/
tablelint check results.csv --strict
tablelint check tables/ --format json
~~~

## License

MIT
