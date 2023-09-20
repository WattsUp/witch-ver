"""Semantic Versioning as described by https://semver.org/
"""

from __future__ import annotations

import re
import typing as t

# From https://semver.org/
_NUM_ID = r"0|[1-9]\d*"
_PRE_ID = rf"(?:{_NUM_ID}|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
_BUILD_ID = r"[0-9a-zA-Z-]+"
REGEX = re.compile(
    rf"^(?P<major>{_NUM_ID})\."
    rf"(?P<minor>{_NUM_ID})\."
    rf"(?P<patch>{_NUM_ID})"
    rf"(?:-(?P<prerelease>{_PRE_ID}(?:\.{_PRE_ID})*))?"
    rf"(?:\+(?P<build>{_BUILD_ID}(?:\.{_BUILD_ID})*))?$"
)
REGEX_NUM_ID = re.compile(rf"^{_NUM_ID}$")
REGEX_PRE_ID = re.compile(rf"^{_PRE_ID}$")
REGEX_BUILD_ID = re.compile(rf"^{_BUILD_ID}$")


class SemVer:
    """Semantic Versioning as described by https://semver.org/"""

    def __init__(
        self,
        string: str = None,
        major: int = None,
        minor: int = None,
        patch: int = None,
        prerelease: t.Union[str, t.List[str]] = None,
        build: t.Union[str, t.List[str]] = None,
    ) -> None:
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
        self._major = None
        self._minor = None
        self._patch = None
        self._prerelease: t.List[str] = []
        self._build: t.List[str] = []

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
        if prerelease is not None:
            if isinstance(prerelease, str):
                self.append_prerelease(prerelease)
            else:
                # Probably a list of tags but maybe a list of tag.tag
                for e in prerelease:
                    self.append_prerelease(e)

        if build is not None:
            if isinstance(build, str):
                self.append_build(build)
            else:
                # Probably a list of tags but maybe a list of tag.tag
                for e in build:
                    self.append_build(e)

    def __str__(self) -> str:
        buf = self.core
        if len(self._prerelease) > 0:
            buf += "-"
            buf += self.prerelease
        if len(self._build) > 0:
            buf += "+"
            buf += self.build
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

    def bump_major(self) -> None:
        """Bump major revision number

        Adds one to major.
        Resets minor, patch, prerelease, and build
        """
        self._major += 1
        self._minor = 0
        self._patch = 0
        self.clear_prerelease()
        self.clear_build()

    def bump_minor(self) -> None:
        """Bump minor revision number

        Adds one to minor.
        Resets patch, prerelease, and build
        """
        self._minor += 1
        self._patch = 0
        self.clear_prerelease()
        self.clear_build()

    def bump_patch(self) -> None:
        """Bump patch revision number

        Adds one to patch.
        Resets prerelease, and build
        """
        self._patch += 1
        self.clear_prerelease()
        self.clear_build()

    def clear_prerelease(self) -> None:
        """Clear prerelease tags"""
        self._prerelease = []

    def append_prerelease(self, s: str) -> None:
        """Append prerelease tag

        Args:
          s: String tag to append or multiple tag.tag.tag
        """
        for i in s.split("."):
            if not REGEX_PRE_ID.match(i):
                raise ValueError(f"Prerelease tag does not match SemVer pattern '{i}'")
            self._prerelease.append(i)

    def clear_build(self) -> None:
        """Clear build tags"""
        self._build = []

    def append_build(self, s: str) -> None:
        """Append prerelease tag

        Args:
          s: String tag to append or multiple tag.tag.tag
        """
        for i in s.split("."):
            if not REGEX_BUILD_ID.match(i):
                raise ValueError(f"Build tag does not match SemVer pattern '{i}'")
            self._build.append(i)

    @property
    def major(self) -> int:
        """Major revision number"""
        return self._major

    @property
    def minor(self) -> int:
        """Minor revision number"""
        return self._minor

    @property
    def patch(self) -> int:
        """Patch revision number"""
        return self._patch

    @property
    def prerelease_list(self) -> t.List[str]:
        """Prerelease tags as a list"""
        return self._prerelease

    @property
    def prerelease(self) -> str:
        """Prerelease tags as a single string"""
        return ".".join(self._prerelease)

    @property
    def build_list(self) -> t.List[str]:
        """Build tags as a list"""
        return self._build

    @property
    def build(self) -> str:
        """Build tags as a single string"""
        return ".".join(self._build)

    @property
    def core(self) -> str:
        """Version core string"""
        return f"{self._major}.{self._minor}.{self._patch}"
