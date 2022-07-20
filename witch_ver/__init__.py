"""witch-ver

git tag based versioning
"""

from witch_ver import version

__version__ = version.version_full

from witch_ver.git import (GitVer, fetch, str_func_pep440,
                           str_func_git_describe, str_func_git_describe_long)
from witch_ver.semver import SemVer
