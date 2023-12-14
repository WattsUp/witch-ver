"""Interface to a git repository."""

from __future__ import annotations

import datetime
import functools
import re
import typing as t
from pathlib import Path
from typing import TYPE_CHECKING

from witch_ver import runner
from witch_ver.semver import SemVer

if TYPE_CHECKING:
    import os

REGEX = re.compile(r"^(?P<tag>.+)-(?P<distance>\d+)-g(?P<sha>[0-9a-f]+)$")


class GitVer(SemVer):
    """Semantic version with extra git information."""

    def __init__(
        self,
        tag_prefix: str = "v",
        *_,
        dirty_in_pre: t.Union[bool, None] = True,
        distance_in_pre: t.Union[bool, None] = True,
        sha_in_pre: t.Union[bool, None] = None,
        sha_abbrev_in_pre: t.Union[bool, None] = True,
        date_in_pre: t.Union[bool, None] = False,
        sha: t.Union[str, None] = None,
        sha_abbrev: t.Union[str, None] = None,
        branch: t.Union[str, None] = None,
        date: t.Union[datetime.datetime, str, None] = None,
        dirty: t.Union[bool, None] = None,
        distance: t.Union[int, None] = None,
        tag: t.Union[str, None] = None,
        git_dir: t.Union[Path, None] = None,
        pretty_str: t.Union[str, t.Callable[[GitVer], str], None] = None,
    ) -> None:
        """Create a git interface.

        Args:
            tag_prefix: Prefix for git tags describing version (to filter)
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

            sha: git SHA of latest commit
            sha_abbrev: git SHA latest commit, abbreviated
            branch: Current branch
            date: Date of last commit
            dirty: True if has changes from HEAD
            distance: Distance to latest tag
            tag: Latest tag
            git_dir: Path to .git folder
            pretty_str: Formatted semantic version string
        """
        date = datetime.datetime.fromisoformat(date) if isinstance(date, str) else date
        self._sha = sha
        self._sha_abbrev = sha_abbrev
        self._branch = branch
        self._date = date
        self._dirty = dirty
        self._distance = distance
        self._tag = tag
        self._tag_prefix = tag_prefix
        self._git_dir = git_dir

        if date is not None and date.tzinfo is None:
            msg = "Date timezone must not be None"
            raise ValueError(msg)

        if tag is None:
            super().__init__(major=0, minor=0, patch=0, prerelease="untagged")
        else:
            if tag_prefix is not None and tag.startswith(tag_prefix):
                tag = tag[len(tag_prefix) :]
            super().__init__(tag)

        if distance is not None:
            if distance_in_pre:
                self.append_prerelease(f"p{distance}")
            elif distance_in_pre is False:
                self.append_build(f"p{distance}")

        if dirty:
            if dirty_in_pre:
                self.append_prerelease("dirty")
            elif dirty_in_pre is False:
                self.append_build("dirty")

        if sha is not None:
            if sha_in_pre:
                self.append_prerelease(f"g{sha}")
            elif sha_in_pre is False:
                self.append_build(f"g{sha}")

        if sha_abbrev is not None:
            if sha_abbrev_in_pre:
                self.append_prerelease(f"g{sha_abbrev}")
            elif sha_abbrev_in_pre is False:
                self.append_build(f"g{sha_abbrev}")

        if date is not None:
            s = date.strftime("%Y%m%dT%H%M%SZ")
            if date_in_pre:
                self.append_prerelease(s)
            elif date_in_pre is False:
                self.append_build(s)

        if callable(pretty_str):
            self._pretty_str = pretty_str(self)
        else:
            self._pretty_str = pretty_str

    def __str__(self) -> str:
        """Formatted semantic version string."""
        if self._pretty_str is None:
            return self.semver
        return self._pretty_str

    def __repr__(self) -> str:
        """Representation debug string."""
        return f"<witch_ver.git.GitVer '{self.semver}'>"

    def asdict(
        self,
        *_,
        isoformat_date: bool = False,
        include_git_dir: bool = False,
    ) -> dict:
        """Convert GitVer to dictionary.

        Args:
            isoformat_date: True will convert date to isoformat, False will leave it
                as datetime
            include_git_dir: True will include the git_dir, False will include None

        Returns:
            Dictionary of tag, tag_prefix, sha, sha_abbrev, branch, date, dirty,
                distance, pretty_str (output of str(GitVer)), and git_dir
        """
        date = self._date.isoformat() if isoformat_date and self._date else self._date
        return {
            "tag": self._tag,
            "tag_prefix": self._tag_prefix,
            "sha": self._sha,
            "sha_abbrev": self._sha_abbrev,
            "branch": self._branch,
            "date": date,
            "dirty": self._dirty,
            "distance": self._distance,
            "pretty_str": self._pretty_str,
            "git_dir": self._git_dir if include_git_dir else None,
        }

    @property
    def git_dir(self) -> t.Union[Path, None]:
        """Location to the folder containing git repository (.git folder)."""
        return self._git_dir

    @property
    def semver(self) -> str:
        """Semantic version of repository."""
        return super().__str__()

    @property
    def sha(self) -> t.Union[str, None]:
        """Git SHA of latest commit."""
        return self._sha

    @property
    def sha_abbrev(self) -> t.Union[str, None]:
        """Git SHA of latest commit, abbreviated length (git decides how long)."""
        return self._sha_abbrev

    @property
    def branch(self) -> t.Union[str, None]:
        """Current branch."""
        return self._branch

    @property
    def date(self) -> t.Union[datetime.datetime, None]:
        """Date of latest commit."""
        return self._date

    @property
    def is_dirty(self) -> t.Union[bool, None]:
        """True means repository has changes from HEAD.

        If changes in the index are reverted in the working tree then it is not
        dirty since it is equivalent to HEAD

        If there is a untracked and unignored file, that is dirty
        """
        return self._dirty

    @property
    def distance(self) -> t.Union[int, None]:
        """Distance between latest commit and closest tag."""
        return self._distance

    @property
    def tag(self) -> t.Union[str, None]:
        """Closest tag to latest commit, possible None if no tags exist."""
        return self._tag

    @property
    def tag_prefix(self) -> str:
        """Prefix for git tags describing version.

        i.e. "v" for v0.0.0 or "ver" for ver0.0.0
        """
        return self._tag_prefix


def fetch(
    path: t.Union[str, os.PathLike],
    tag_prefix: str = "v",
    describe_args: t.Union[t.List[str], None] = None,
    custom_str_func: t.Union[t.Callable[[GitVer], str], None] = None,
    cache: t.Union[t.Dict[str, t.Any], None] = None,
    **kwargs: t.Union[str, int, bool, datetime.datetime, None, Path],
) -> GitVer:
    """Run git commands to fetch current repository status.

    Args:
      path: Path to repository folder (to run commands from), None will use cwd()
      tag_prefix: Prefix for git tags describing version (to filter)
      describe_args: Arguments used for git describe, None will use default:
        --tags --always --long --match {tag_prefix}*
      custom_str_func: Custom format function for str(Git) which takes a single
        argument self. None will use str(SemVer) and tags included as follows.
      cache: Cached dict version of a GitVer, if SHAs are identical, only update
        dirtiness, else fetch all
      kwargs: Other arguments passed to GitVer.__init__

    Raises:
      RuntimeError if a git command fails
      ValueError if git describe doesn't match REGEX
    """
    path = Path(path).resolve()

    if describe_args is None:
        describe_args = ["--tags", "--always", "--long"]
        if tag_prefix is not None:
            describe_args.extend(("--match", tag_prefix + "*"))

    run = functools.partial(runner.run, "git", cwd=path)

    def run_check(cmd: t.List[str], *args: str, **kwargs: str) -> t.Tuple[str, int]:
        stdout, returncode = run(cmd, *args, **kwargs)
        if stdout is None or returncode != 0:  # pragma: no cover
            # All commands should fail gracefully, can't test
            msg = f"Command failed {' '.join(cmd)}"
            raise RuntimeError(msg)
        return stdout, returncode

    def default_branch() -> str:
        out, returncode = run(["config", "init.defaultBranch"])
        # This key was added in 2.28. The default prior was master
        return out if returncode == 0 else "master"

    git_dir, returncode = run(["rev-parse", "--git-dir"])
    if returncode != 0:
        msg = f"Path is not inside a git repository '{path}'"
        raise RuntimeError(msg)
    git_dir = Path(git_dir)
    if not git_dir.is_absolute():
        git_dir = path.joinpath(git_dir)
    git_dir = git_dir.resolve()
    if git_dir.parent != path:
        msg = f"Unexpected git repository '{git_dir}'"
        raise RuntimeError(msg)

    sha, returncode = run(["rev-parse", "HEAD"])
    if returncode != 0:
        # Likely HEAD doesn't point to anything aka no commits
        kwargs["sha"] = ""
        kwargs["sha_abbrev"] = ""
        kwargs["branch"] = default_branch()
        kwargs["date"] = datetime.datetime.now(datetime.timezone.utc)
        kwargs["distance"] = 0
        kwargs["tag"] = None
        kwargs["git_dir"] = git_dir

        status, returncode = run_check(["status", "--porcelain"])
        kwargs["dirty"] = len(status) > 0
        return GitVer(
            tag_prefix=tag_prefix,
            pretty_str=custom_str_func,
            **kwargs,  # type: ignore[attr-defined]
        )

    dirty = False
    _, returncode = run(["diff", "--quiet", "HEAD"])
    if returncode == 0:
        # No difference between HEAD and working tree
        # Check for any untracked and unignored files
        status, returncode = run_check(["status", "--porcelain"])
        changes = status.splitlines()
        for c in changes:
            if c[0] == "?":
                dirty = True
                break
    else:
        dirty = True

    describe, returncode = run_check(["describe", *describe_args])
    if "-" in describe:
        m = REGEX.match(describe)
        if m is None:
            msg = f"git describe did not match regex '{describe}'"
            raise ValueError(msg)
        m = m.groupdict()

        distance = int(m["distance"])
        tag = m["tag"]
        sha_abbrev = m["sha"]
    else:
        d, returncode = run_check(["rev-list", "HEAD", "--count"])

        distance = int(d)
        tag = None
        sha_abbrev = describe

    if cache is not None:
        required = ["sha", "sha_abbrev", "branch", "date", "distance", "tag"]
        if (
            all(r in cache for r in required)
            and sha == cache["sha"]
            and tag == cache["tag"]
        ):
            for r in required:
                kwargs[r] = cache[r]
            kwargs["git_dir"] = git_dir
            kwargs["dirty"] = dirty
            return GitVer(
                tag_prefix=tag_prefix,
                pretty_str=custom_str_func,
                **kwargs,  # type: ignore[attr-defined]
            )

    branch, returncode = run_check(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch == "HEAD":
        branches, returncode = run_check(
            ["branch", "--format=%(refname:lstrip=2)", "--contains"],
        )

        branches = branches.splitlines()
        if "(" in branches[0]:
            # On git v1.5.0-rc1 detached head information was added to git branch
            branches.pop(0)  # pragma: no cover since this is 15 years old

        branch = None
        default_branches = [default_branch(), "master", "main"]
        for b in default_branches:
            if b in branches:
                branch = b
                break
        if branch is None:
            branch = None if len(branches) == 0 else branches[0]

    raw, returncode = run_check(["show", "-s", "--format=%ci", "HEAD"])
    date = datetime.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %z")

    kwargs["sha"] = sha
    kwargs["sha_abbrev"] = sha_abbrev
    kwargs["branch"] = branch
    kwargs["date"] = date
    kwargs["distance"] = distance
    kwargs["tag"] = tag
    kwargs["git_dir"] = git_dir

    status, returncode = run_check(["status", "--porcelain"])
    kwargs["dirty"] = dirty

    return GitVer(
        tag_prefix=tag_prefix,
        pretty_str=custom_str_func,
        **kwargs,  # type: ignore[attr-defined]
    )


def str_func_pep440(g: GitVer) -> str:
    """Format a GitVer compliant with PEP440.

    Does strip tag_prefix

    TAG if precisely at that point
    0+untagged.DISTANCE.gSHA[.dirty] if untagged
    TAG.DISTANCE.gSHA[.dirty] if tag has a '+'
    TAG+DISTANCE.gSHA[.dirty] otherwise

    If HEAD doesn't point to anything (no commits)
    0+untagged[.dirty]

    Args:
      g: Git version information

    Returns:
      Formatted string
    """
    buf = g.tag
    if buf is None:
        buf = "0+untagged"
    elif buf.startswith(g.tag_prefix):
        buf = buf[len(g.tag_prefix) :]

    if g.distance == 0 and not g.is_dirty:
        return buf

    buf += "." if "+" in buf else "+"
    buf += f"{g.distance}.g{g.sha_abbrev}"
    if g.is_dirty:
        buf += ".dirty"
    return buf


def str_func_git_describe(g: GitVer) -> str:
    """Format GitVer to match `git describe --tags --dirty --always`.

    TAG[-dirty] if precisely at that point
    SHA[-dirty] if untagged
    TAG-DISTANCE-gSHA[-dirty] otherwise

    If HEAD doesn't point to anything (no commits)
    {tag_prefix}0.0.0-untagged-0-g[-dirty]

    Args:
      g: Git version information

    Returns:
      Formatted string
    """
    if g.tag is not None and g.distance == 0:
        if g.is_dirty:
            return g.tag + "-dirty"
        return g.tag
    return str_func_git_describe_long(g)


def str_func_git_describe_long(g: GitVer) -> str:
    """Format GitVer to match `git describe --tags --dirty --always --long`.

    SHA[-dirty] if untagged
    TAG-DISTANCE-gSHA[-dirty] otherwise

    If HEAD doesn't point to anything (no commits)
    {tag_prefix}0.0.0-untagged-0-g[-dirty]

    Args:
      g: Git version information

    Returns:
      Formatted string
    """
    if g.tag is None:
        buf = (
            f"{g.tag_prefix}0.0.0-untagged-0-g"
            if g.distance == 0
            else str(g.sha_abbrev)
        )
    else:
        buf = f"{g.tag}-{g.distance}-g{g.sha_abbrev}"
    if g.is_dirty:
        buf += "-dirty"
    return buf
