"""witch-ver

git tag based versioning
"""

from witch_ver.version import *

from witch_ver.git import (GitVer, fetch, str_func_pep440,
                           str_func_git_describe, str_func_git_describe_long)
from witch_ver.semver import SemVer
