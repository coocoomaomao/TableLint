# GitHub Action

TableLint can run directly in GitHub Actions and emit native workflow annotations.

## Basic use

Until the first tagged release is published, use `@main`:

~~~yaml
name: Table QA

on:
  pull_request:
  push:
    branches: [main]

jobs:
  tables:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: coocoomaomao/TableLint@main
        with:
          path: tables/
          strict: "true"
~~~

## Explicit significance-star convention

Star conventions differ across journals and fields, so TableLint never assumes one. Enable the cross-check explicitly:

~~~yaml
- uses: coocoomaomao/TableLint@main
  with:
    path: tables/
    star-thresholds: "0.05,0.01,0.001"
~~~

The thresholds map to `*`, `**`, and `***` using strict `p < threshold` comparisons.

## Direct CLI use

~~~bash
tablelint check tables/ --github-annotations
tablelint check tables/ --star-thresholds 0.05,0.01,0.001
~~~
