"""witch-ver: git tag based versioning."""
from __future__ import annotations

from witch_ver.git import (
    fetch,
    GitVer,
    str_func_git_describe,
    str_func_git_describe_long,
    str_func_pep440,
)
from witch_ver.semver import SemVer
from witch_ver.version import __version__

__all__ = [
    "__version__",
    "GitVer",
    "SemVer",
    "fetch",
    "str_func_git_describe",
    "str_func_git_describe_long",
    "str_func_pep440",
]
