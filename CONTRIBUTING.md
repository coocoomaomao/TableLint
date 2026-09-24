# Contributing

Thanks for helping improve TableLint.

## Development

~~~bash
python -m venv .venv
pip install -e ".[dev]"
pytest
~~~

When adding a rule:

- prefer deterministic checks over guesses,
- keep domain-dependent checks informational or opt-in,
- add focused tests,
- document false-positive risks,
- do not turn a formatting convention into a scientific-validity claim.
