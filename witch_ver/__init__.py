"""witch-ver

git tag based versioning
"""

from witch_ver.git import (
    fetch,
    GitVer,
    str_func_git_describe,
    str_func_git_describe_long,
    str_func_pep440,
)
from witch_ver.semver import SemVer
from witch_ver.version import *
