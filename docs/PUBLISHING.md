# Publishing TableLint

TableLint publishes to PyPI through GitHub Actions using PyPI Trusted Publishing (OIDC). No long-lived PyPI API token is stored in GitHub.

## One-time PyPI setup

Create a pending trusted publisher for:

- PyPI project name: `tablelint`
- GitHub owner: `coocoomaomao`
- Repository: `TableLint`
- Workflow: `release.yml`
- Environment: `pypi`

## Release process

1. Make sure CI is green on `main`.
2. Create and publish a GitHub Release, for example `v0.1.0`.
3. The Release workflow builds wheel + source distribution and runs `twine check`.
4. The publish job uses GitHub OIDC to publish to PyPI.
5. Verify:

~~~bash
pip install tablelint
tablelint --help
~~~

## Security

Do not paste PyPI passwords, API tokens, TOTP QR codes/seeds, or recovery codes into issues, pull requests, screenshots, or chat messages.
