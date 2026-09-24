# Roadmap

## v0.1 — deterministic table QA

- CSV input
- XLSX input
- LaTeX table/tabular input
- empty / duplicate headers
- empty columns
- placeholder values
- exact duplicate rows
- explicit percentage range checks
- p-value range checks for clearly named p-value columns
- informational decimal-precision consistency checks
- LaTeX caption / label checks
- LaTeX row-width checks
- recursive directory scanning
- strict mode
- JSON output
- Python 3.10–3.12 CI

## v0.2 — research-table intelligence

- [x] mean ± SD / SEM format checks
- [x] Mean (SD / SEM) format checks
- [x] negative SD / SEM detection
- [x] confidence interval syntax and ordering
- [x] paired CI lower / upper ordering
- [ ] significance-star consistency when both stars and numeric p-values are present
- [ ] optional unit-consistency rules
- [ ] configurable missing-value policy
- [ ] GitHub Actions annotations
- [ ] reusable GitHub Action

## v0.3 — Academic Lint integration

- ManuscriptLint orchestration
- source-backed journal/publisher table presets where rules are automatable
- cross-check table references against manuscript source
- optional TableLint report aggregation with FigureLint and RefLint

## Long term

TableLint should remain conservative: deterministic data and formatting QA first, domain-specific statistical interpretation only when explicitly configured.
