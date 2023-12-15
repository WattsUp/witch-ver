# witch-ver
[![Unit Test][unittest-image]][unittest-url] [![Static Analysis][static-analysis-image]][static-analysis-url] [![Coverage][coverage-image]][coverage-url] [![Latest Version][pypi-image]][pypi-url]

Have you ever asked yourself which version you're at? witch-ver can help.

witch-ver automatically calculates the version of a git repo and adds the information when building.

If you just want to integrate witch-ver into your project, head to [usage](#usage)

----
## Environment
List of dependencies for package to run.
### Required
* git
* python modules, installed via `pip install witch-ver`
  * colorama
  * setuptools

### Optional
* Test extensions, installed via `pip install witch-ver[test]`
  * AutoDict
  * coverage
  * time-machine
  * tomli

----
## Installation / Build / Deployment
```bash
# To install latest stable version on PyPi, execute:
python -m pip install witch-ver

# To install from source, execute:
git clone https://github.com/WattsUp/witch-ver
cd witch-ver
python -m pip install .

# For development, install as a link to repository such that code changes are used. And include testing packages
git clone https://github.com/WattsUp/witch-ver
cd witch-ver
python -m pip install -e ".[dev]"
```

----
## Usage
To use witch-ver in your project, add two lines to the project configuration. Also should have some git tags.
```Python
# setup.py
setuptools.setup(
    ...
    use_witch_ver=True,
    ...
)
```
```toml
# pyproject.toml
[build-system]
requires = [
    ...
    "witch-ver",
    ...
]
```
----
## Running Tests
Make sure to install package with [testing extension](#optional)
Unit tests
```bash
> python -m test
```
Coverage report
```bash
> python -m coverage run && python -m coverage report
```
----
## Development
Code development of this project adheres to [Google Python Guide](https://google.github.io/styleguide/pyguide.html)

Linters
```bash
> ruff .
> codespell .
```
Formatters
```bash
> isort .
> black .
```
### Tools
- `formatters.sh` will run every formatter
- `linters.sh` will run every linter
---
## Versioning
Versioning of this projects adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and is implemented using git tags.  

[pypi-image]: https://img.shields.io/pypi/v/witch-ver.svg
[pypi-url]: https://pypi.python.org/pypi/witch-ver/
[unittest-image]: https://github.com/WattsUp/witch-ver/actions/workflows/test.yml/badge.svg
[unittest-url]: https://github.com/WattsUp/witch-ver/actions/workflows/test.yml
[static-analysis-image]: https://github.com/WattsUp/witch-ver/actions/workflows/static-analysis.yml/badge.svg
[static-analysis-url]: https://github.com/WattsUp/witch-ver/actions/workflows/static-analysis.yml
[coverage-image]: https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/WattsUp/36d9705addcd44fb0fccec1d23dc1338/raw/witch-ver__heads_master.json
[coverage-url]: https://github.com/WattsUp/witch-ver/actions/workflows/coverage.yml
