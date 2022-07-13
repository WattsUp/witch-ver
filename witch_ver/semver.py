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
REGEX_NUM_ID = re.compile(fr"^{_NUM_ID}$")
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

  def __str__(self) -> str:
    buf = f"{self._major}.{self._minor}.{self._patch}"
    if len(self._prerelease) > 0:
      buf += "-"
      buf += ".".join(self._prerelease)
    if len(self._build) > 0:
      buf += "+"
      buf += ".".join(self._build)
    return buf

  def __repr__(self) -> str:
    return f"<witch_ver.semver.SemVer '{self}'>"

  def __eq__(self, obj: object) -> bool:
    """Compare SemVer for equality

    Tests strictly that all parts match.

    Args:
      obj: Of type SemVer or a string

    Returns:
      True if all parts are equal, False otherwise
    """
    if isinstance(obj, str):
      obj = SemVer(obj)
    elif not isinstance(obj, SemVer):
      raise TypeError(f"Cannot compare SemVer to {type(obj)}")

    if self._major != obj._major:
      return False
    if self._minor != obj._minor:
      return False
    if self._patch != obj._patch:
      return False
    if self._prerelease != obj._prerelease:
      return False
    if self._build != obj._build:
      return False
    return True

  def __gt__(self, obj: object) -> bool:
    """Compare SemVer for greater-than

    See https://semver.org/#spec-item-11 for precedence

    Args:
      obj: Of type SemVer or a string

    Returns:
      True if all parts are equal, False otherwise
    """
    if isinstance(obj, str):
      obj = SemVer(obj)
    elif not isinstance(obj, SemVer):
      raise TypeError(f"Cannot compare SemVer to {type(obj)}")

    if self._major > obj._major:
      return True
    if self._minor > obj._minor:
      return True
    if self._patch > obj._patch:
      return True
    for this, other in zip(self._prerelease, obj._prerelease):
      if REGEX_NUM_ID.match(this):
        this = int(this)
        if REGEX_NUM_ID.match(other):
          other = int(other)
          if this > other:
            return True
        # this is number
        # other is alphanumeric
      else:
        if REGEX_NUM_ID.match(other):
          # this is alphanumeric
          # other is number
          return True
        # Both are alphanumeric, compare lexically
        if this > other:
          return True
    return len(self._prerelease) < len(obj._prerelease)

  def __ge__(self, obj: object) -> bool:
    return (self > obj) or (self == obj)

  def __lt__(self, obj: object) -> bool:
    return not self >= obj

  def __le__(self, obj: object) -> bool:
    return not self > obj
