# witch-ver
[![Unit Test][unittest-image]][unittest-url] [![Pylint][pylint-image]][pylint-url] [![Coverage][coverage-image]][coverage-url] [![Latest Version][pypi-image]][pypi-url]

Have you ever asked yourself which version you're at? witch-ver can help.

witch-ver automatically calculates the version of a git repo and adds the information when building.

----
## Environment
List of dependencies for package to run.
### Required
* git
* python modules, installed via `pip install witch-ver`
  * colorama

### Optional
* Test extensions, installed via `pip install witch-ver[test]`
  * AutoDict
  * coverage
  * pylint

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
python -m pip install -e .[test]
```

----
## Usage
Explain how to use your project.
```Python
# TODO
```
----
## Running Tests
Make sure to install package with [testing extension](#optional)
```bash
# To run the automated tests, execute:
python -m tests discover -s tests -t . --locals

# To save the results to file, execute:
python -m tests discover -s tests -t . --locals &> testing.log

## The following is a synopsis of unittest main arguments ##
# To run a singular test file, execute:
python -m tests $path_to_test_file
python -m tests tests.test_main

# To run a singular test class, execute:
python -m tests $path_to_test_file.$class
python -m tests tests.test_main.TestMain

# To run a singular test method, execute:
python -m tests $path_to_test_file.$class.$method
python -m tests tests.test_main.TestMain.test_parser

# Multiple can be strung together
python -m tests tests.test_main tests.test_writer
```
```bash
# To run coverage and print the report with missing lines, execute:
python -m coverage run && python -m coverage report -m

# To run profiler, execute:
python -m cProfile -s tottime -m tests discover -s tests -t . > profile.log

# To run linting, execute:
python -m pylint witch_ver tests tools setup.py
```
----
## Development
Code development of this project adheres to [Google Python Guide](https://google.github.io/styleguide/pyguide.html)

### Styling
Use `yapf` to format files, based on Google's guide with the exception of indents being 2 spaces.
```bash
# To format all files, execute:
yapf -ir .
```

---
## Versioning
Versioning of this projects adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and is implemented using git tags.  

[pypi-image]: https://img.shields.io/pypi/v/witch-ver.svg
[pypi-url]: https://pypi.python.org/pypi/witch-ver/
[unittest-image]: https://github.com/WattsUp/witch-ver/actions/workflows/test.yml/badge.svg
[unittest-url]: https://github.com/WattsUp/witch-ver/actions/workflows/test.yml
[pylint-image]: https://github.com/WattsUp/witch-ver/actions/workflows/lint.yml/badge.svg
[pylint-url]: https://github.com/WattsUp/witch-ver/actions/workflows/lint.yml
[coverage-image]: https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/WattsUp/36d9705addcd44fb0fccec1d23dc1338/raw/witch-ver__heads_master.json
[coverage-url]: https://github.com/WattsUp/witch-ver/actions/workflows/coverage.yml
