"""Semantic Versioning as described by https://semver.org/
"""

from __future__ import annotations

import re
from typing import List, Union

# From https://semver.org/
_NUM_ID = r"0|[1-9]\d*"
_PRE_ID = fr"(?:{_NUM_ID}|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
_BUILD_ID = r"[0-9a-zA-Z-]+"
REGEX = re.compile(fr"^(?P<major>{_NUM_ID})\."
                   fr"(?P<minor>{_NUM_ID})\."
                   fr"(?P<patch>{_NUM_ID})"
                   fr"(?:-(?P<prerelease>{_PRE_ID}(?:\.{_PRE_ID})*))?"
                   fr"(?:\+(?P<build>{_BUILD_ID}(?:\.{_BUILD_ID})*))?$")
REGEX_PRE_ID = re.compile(fr"^{_PRE_ID}$")
REGEX_BUILD_ID = re.compile(fr"^{_BUILD_ID}$")


class SemVer:
  """Semantic Versioning as described by https://semver.org/
  """

  def __init__(self,
               string: str = None,
               major: int = None,
               minor: int = None,
               patch: int = None,
               prerelease: Union[str, List[str]] = None,
               build: Union[str, List[str]] = None) -> None:
    """Create a SemVer object

    Must provide a string to parse or at least major, minor, & patch.

    Args:
      string: String to parse
      major: Major revision number (required if s is None)
      minor: Minor revision number (required if s is None)
      patch: Patch revision number (required if s is None)
      prerelease: Prerelease tag or a list of them (optional)
      build: Build metadata tag or a list of them (optional)

    Raises:
      TypeError if s is None and major, minor, or patch is missing
      ValueError if any any values are improper format
    """
    if string is not None:
      m = REGEX.match(string)
      if m is None:
        raise ValueError(f"String did not match SemVer pattern '{string}'")
      m = m.groupdict()
      major = m["major"]
      minor = m["minor"]
      patch = m["patch"]
      prerelease = m["prerelease"]
      build = m["build"]

    if major is None or minor is None or patch is None:
      raise TypeError("SemVer() takes a string or major, minor, & patch")

    self._major = int(major)
    self._minor = int(minor)
    self._patch = int(patch)
    self._prerelease: List[str] = []
    self._build: List[str] = []
    if prerelease is not None:
      if isinstance(prerelease, str):
        prerelease = [prerelease]
      # Probably a list of tags but maybe a list of tag.tag
      for e in prerelease:
        for i in e.split("."):
          if REGEX_PRE_ID.match(i) is None:
            raise ValueError(
                f"Prerelease tag does not match SemVer pattern '{i}'")
          self._prerelease.append(i)

    if build is not None:
      if isinstance(build, str):
        build = [build]
      # Probably a list of tags but maybe a list of tag.tag
      for e in build:
        for i in e.split("."):
          if REGEX_PRE_ID.match(i) is None:
            raise ValueError(f"Build tag does not match SemVer pattern '{i}'")
          self._build.append(i)
