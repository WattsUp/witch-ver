"""Interface to a git repository
"""

import datetime
import functools
import os
import pathlib
import re
from typing import List, Union

from witch_ver import runner
from witch_ver.semver import SemVer

REGEX = re.compile(r"^(?P<tag>.+)-(?P<distance>\d+)-g(?P<sha>[0-9a-f]+)$")


class Git:
  """Interface to a git repository
  """

  def __init__(self,
               path: Union[str, bytes, os.PathLike] = None,
               version_prefix: str = "v",
               describe_args: List[str] = None,
               custom_str_fmt: str = None,
               dirty_in_pre: bool = True,
               distance_in_pre: bool = True,
               sha_in_pre: bool = None,
               sha_abbrev_in_pre: bool = True,
               date_in_pre: bool = False) -> None:
    """Create a git interface

    Args:
      path: Path to .git folder (given to git -C <path>), None will use cwd()
      version_prefix: Prefix for git tags describing version (to filter)
      describe_args: Arguments used for git describe, None will use default:
        --tags --dirty --always --long --match {version_prefix}*
      custom_str_fmt: Custom format for str(Git), see Git.str() for format
        specifications. None will use str(SemVer) and tags included as follows.
      dirty_in_pre: True will add "dirty" to prerelease tags, False to build
        tags, None for omission
      distance_in_pre: True will add "p{n}" to prerelease tags, False to build
        tags, None for omission
      sha_in_pre: True will add commit "g{SHA}" to prerelease tags, False to
        build tags, None for omission
      sha_abbrev_in_pre: True will add "g{abbreviated SHA}" to prerelease tags,
        False to build tags, None for omission
      date_in_pre: True will add "{date:%Y%m%dT%H%M%SZ}" to prerelease tags,
        False to build tags, None for omission
    """
    if path is None:
      path = pathlib.Path(".").absolute()
    self._path = path
    self._semver: SemVer = None

    self._version_prefix = version_prefix

    if describe_args is None:
      describe_args = ["--tags", "--dirty", "--always", "--long"]
      if version_prefix is not None:
        describe_args.extend(("--match", version_prefix + "*"))
    self._describe_args = describe_args

    self._sha: str = None
    self._sha_abbrev: str = None
    self._branch: str = None
    self._date: datetime.datetime = None
    self._dirty: bool = None
    self._distance: int = None
    self._tag: str = None

    self._custom_str_format = custom_str_fmt

    self._dirty_in_pre = dirty_in_pre
    self._distance_in_pre = distance_in_pre
    self._sha_in_pre = sha_in_pre
    self._sha_abbrev_in_pre = sha_abbrev_in_pre
    self._date_in_pre = date_in_pre

  def fetch_git_info(self) -> None:
    """Run git commands to fetch current repository status

    Raises:
      RuntimeError if a git command fails
      ValueError if git describe doesn't match REGEX
    """
    run = functools.partial(runner.run, "git", cwd=self._path)

    _, returncode = run(["rev-parse", "--git-dir"])
    if returncode != 0:
      raise RuntimeError(f"Path is not inside a git repository '{self._path}'")

    describe, returncode = run(["describe"] + self._describe_args)
    if describe is None or returncode != 0:
      raise RuntimeError("git describe failed")

    self._sha, returncode = run(["rev-parse", "HEAD"])
    if self._sha is None or returncode != 0:
      raise RuntimeError("git rev-pase failed")

    self._branch, returncode = run(["rev-parse", "--abbrev-ref", "HEAD"])
    if self._branch is None or returncode != 0:
      raise RuntimeError("git rev-parse --abbrev-ref HEAD failed")

    if self._branch == "HEAD":
      branches, returncode = run(
          ["branch", "--format=%(refname:lstrip=2)", "--contains"])
      if branches is None or returncode != 0:
        raise RuntimeError("git branch failed")

      branches = branches.splitlines()
      if "(" in branches[0]:
        branches.pop(0)

      if "master" in branches:
        self._branch = "master"
      elif "main" in branches:
        self._branch = "main"
      elif len(branches) == 0:
        self._branch = None
      else:
        self._branch = branches[0]

    raw, returncode = run(["show", "-s", "--format=%ci", "HEAD"])
    if raw is None or returncode != 0:
      raise RuntimeError("git show failed")
    self._date = datetime.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %z")

    self._dirty = False
    if describe.endswith("-dirty"):
      self._dirty = True
      describe = describe.removesuffix("-dirty")

    if "-" in describe:
      m = REGEX.match(describe)
      if m is None:
        raise ValueError(f"git describe did not match regex '{describe}'")
      m = m.groupdict()

      self._distance = int(m["distance"])
      self._tag = m["tag"]
      self._sha_abbrev = m["sha"]
    else:
      d, returncode = run(["rev-list", "HEAD", "--count"])
      if d is None or returncode != 0:
        raise RuntimeError("git rev-list failed")

      self._distance = int(d)
      self._tag = None
      self._sha_abbrev = describe

  def build_semver(self) -> SemVer:
    """Build semantic version for git information

    Returns:
      SemVer object built by rules given in init

    Raises:
      ValueError if tag is missing version_prefix
    """
    if self._sha is None:
      self.fetch_git_info()

    if self._tag is None:
      self._semver = SemVer(major=0, minor=0, patch=0, prerelease="no-tag")
    else:
      if not self._tag.startswith(self._version_prefix):
        raise ValueError("tag does not start with version_prefix "
                         f"'{self._tag}'")

      self._semver = SemVer(self._tag.removeprefix(self._version_prefix))

    if self._dirty_in_pre:
      self._semver.append_prerelease("dirty")
    elif self._dirty_in_pre is False:
      self._semver.append_build("dirty")

    if self._distance_in_pre:
      self._semver.append_prerelease(f"p{self._distance}")
    elif self._distance_in_pre is False:
      self._semver.append_build(f"p{self._distance}")

    if self._sha_in_pre:
      self._semver.append_prerelease("g" + self._sha)
    elif self._sha_in_pre is False:
      self._semver.append_build("g" + self._sha)

    if self._sha_abbrev_in_pre:
      self._semver.append_prerelease("g" + self._sha_abbrev)
    elif self._sha_abbrev_in_pre is False:
      self._semver.append_build("g" + self._sha_abbrev)

    s = self._date.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if self._date_in_pre:
      self._semver.append_prerelease(s)
    elif self._date_in_pre is False:
      self._semver.append_build(s)

    return self._semver

  @property
  def semver(self) -> SemVer:
    """Semantic version of repository
    """
    if self._semver is None:
      return self.build_semver()
    return self._semver

  @property
  def sha(self) -> str:
    """git SHA of latest commit
    """
    if self._sha is None:
      self.fetch_git_info()
    return self._sha

  @property
  def sha_abbrev(self) -> str:
    """git SHA of latest commit, abbreviated length (git decides how long)
    """
    if self._sha is None:
      self.fetch_git_info()
    return self._sha_abbrev

  @property
  def branch(self) -> str:
    """Current branch
    """
    if self._sha is None:
      self.fetch_git_info()
    return self._branch

  @property
  def date(self) -> datetime.datetime:
    """Date of latest commit
    """
    if self._sha is None:
      self.fetch_git_info()
    return self._date

  @property
  def is_dirty(self) -> bool:
    """True means repository has uncommitted changes
    """
    if self._sha is None:
      self.fetch_git_info()
    return self._dirty

  @property
  def distance(self) -> int:
    """Distance between latest commit and closest tag
    """
    if self._sha is None:
      self.fetch_git_info()
    return self._distance

  @property
  def tag(self) -> str:
    """Closest tag to latest commit, possible None if no tags exist
    """
    if self._sha is None:
      self.fetch_git_info()
    return self._tag
