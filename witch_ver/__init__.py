"""witch-ver

git tag based versioning
"""

from witch_ver import version

__version__ = version.version_full

from witch_ver.git import Git
from witch_ver.semver import SemVer
