from __future__ import annotations

import datetime
import time
import zipfile

import time_machine

from tests import base
from witch_ver import git


class TestGit(base.TestBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # Can't commit a git repo to this repo
        # Test repos are zipped, extract before testing
        for i in range(8):
            path = cls._DATA_ROOT.joinpath(f"git-{i}")
            if not path.exists():
                z = path.with_suffix(".zip")
                with zipfile.ZipFile(z, "r") as z_file:
                    z_file.extractall(path)

    def test_init(self) -> None:
        g = git.GitVer()
        self.assertEqual(g, "0.0.0-untagged")

        s = "1.2.3-alpha+metadata"
        g = git.GitVer(tag=s)
        self.assertEqual(g, s)

        self.assertRaises(TypeError, git.GitVer, tag=s, not_a_keyword=None)

    def test_fetch(self) -> None:
        path = self._DATA_ROOT.joinpath("git-0")
        # This will always be in a git repo of witch-ver,
        # shouldn't touch the parent, so mock the call
        original_run = git.runner.run
        try:
            git.runner.run = lambda *args, **kwargs: (  # noqa: ARG005
                "fatal: not a git repository (or any of the parent directories): .git",
                128,
            )
            self.assertRaises(RuntimeError, git.fetch, path)
        finally:
            git.runner.run = original_run

        # git-0 has a branch and is dirty
        path = self._DATA_ROOT.joinpath("git-0")
        g = git.fetch(path)
        self.assertEqual(g.sha, "dd0ae6e1409910a9189da369864554785f9b0d01")
        self.assertEqual(g.sha_abbrev, "dd0ae6e")
        self.assertEqual(g.branch, "feat/nothing")
        self.assertEqual(
            g.date,
            datetime.datetime.fromisoformat("2022-07-18T11:01:26-07:00"),
        )
        self.assertTrue(g.is_dirty)
        self.assertEqual(g.distance, 0)
        self.assertEqual(g.tag, "v1.2.3-rc1")
        self.assertEqual(g.git_dir, path.joinpath(".git"))

        # git-1 is an empty repo with no commits
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        path = self._DATA_ROOT.joinpath("git-1")
        with time_machine.travel(utc_now, tick=False):
            g = git.fetch(path)
        self.assertEqual(g.sha, "")
        self.assertEqual(g.sha_abbrev, "")
        self.assertEqual(g.branch, "master")
        self.assertEqual(utc_now, g.date)
        self.assertFalse(g.is_dirty)
        self.assertEqual(g.distance, 0)
        self.assertIsNone(g.tag)
        self.assertEqual(g.git_dir, path.joinpath(".git"))

        # Child folder will fail
        path = self._DATA_ROOT.joinpath("git-1", "child")
        self.assertRaises(RuntimeError, git.fetch, path)

        # git-2 has a branch but is detached
        path = self._DATA_ROOT.joinpath("git-2")
        g = git.fetch(path)
        self.assertEqual(g.sha, "b23ba426ab23f9bf525691e7550fc57afee48dd8")
        self.assertEqual(g.sha_abbrev, "b23ba42")
        self.assertEqual(g.branch, "feat/something")
        self.assertEqual(
            g.date,
            datetime.datetime.fromisoformat("2022-07-18T11:55:17-07:00"),
        )
        self.assertTrue(g.is_dirty)
        self.assertEqual(g.distance, 1)
        self.assertEqual(g.tag, "v0.0.0")

        # -dirty tag doesn't match REGEX
        self.assertRaises(
            ValueError,
            git.fetch,
            path,
            describe_args=["--tags", "--dirty"],
        )

        # git-3 is detached from the master branch
        # Has a change in the index but reverted in the working tree
        path = self._DATA_ROOT.joinpath("git-3")
        g = git.fetch(path, tag_prefix=None)
        self.assertEqual(g.sha, "f70f3f504000d80d45922c213e3cc3dba9bc8e2c")
        self.assertEqual(g.sha_abbrev, "f70f3f5")
        self.assertEqual(g.branch, "master")
        self.assertEqual(
            g.date,
            datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"),
        )
        self.assertFalse(g.is_dirty)
        self.assertEqual(g.distance, 1)
        self.assertEqual(g.tag, "0.0.0")

        # git-4 has no branches but is detached
        # Has a change in the index
        path = self._DATA_ROOT.joinpath("git-4")
        g = git.fetch(path)
        self.assertEqual(g.sha, "f70f3f504000d80d45922c213e3cc3dba9bc8e2c")
        self.assertEqual(g.sha_abbrev, "f70f3f5")
        self.assertIsNone(g.branch)
        self.assertEqual(
            g.date,
            datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"),
        )
        self.assertTrue(g.is_dirty)
        self.assertEqual(g.distance, 2)
        self.assertIsNone(g.tag)

        # git-5 is detached from the main branch
        # Has a change in the index but reverted in the working tree
        path = self._DATA_ROOT.joinpath("git-5")
        start = time.perf_counter()
        g = git.fetch(path, tag_prefix=None)
        elapsed_slow = time.perf_counter() - start
        self.assertEqual(g.sha, "f70f3f504000d80d45922c213e3cc3dba9bc8e2c")
        self.assertEqual(g.sha_abbrev, "f70f3f5")
        self.assertEqual(g.branch, "main")
        self.assertEqual(
            g.date,
            datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"),
        )
        self.assertFalse(g.is_dirty)
        self.assertEqual(g.distance, 1)
        self.assertEqual(g.tag, "0.0.0")

        d = g.asdict()
        start = time.perf_counter()
        g = git.fetch(path, tag_prefix=None, cache=d)
        elapsed_cached = time.perf_counter() - start
        self.assertEqual(g.sha, "f70f3f504000d80d45922c213e3cc3dba9bc8e2c")
        self.assertEqual(g.sha_abbrev, "f70f3f5")
        self.assertEqual(g.branch, "main")
        self.assertEqual(
            g.date,
            datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"),
        )
        self.assertFalse(g.is_dirty)
        self.assertEqual(g.distance, 1)
        self.assertEqual(g.tag, "0.0.0")

        self.log_speed(elapsed_slow, elapsed_cached)
        self.assertGreater(elapsed_slow, elapsed_cached)

        # This won't use the partial cache
        d.pop("branch")
        g = git.fetch(path, tag_prefix=None, cache=d)
        self.assertEqual(g.sha, "f70f3f504000d80d45922c213e3cc3dba9bc8e2c")
        self.assertEqual(g.sha_abbrev, "f70f3f5")
        self.assertEqual(g.branch, "main")
        self.assertEqual(
            g.date,
            datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"),
        )
        self.assertFalse(g.is_dirty)
        self.assertEqual(g.distance, 1)
        self.assertEqual(g.tag, "0.0.0")

        # git-7 is a standard repo
        # But the cache was updated before v0.1.0 tag was added
        # Expect to rerun to get new tag name
        path = self._DATA_ROOT.joinpath("git-7")
        g = git.fetch(path=path)
        d = g.asdict()
        d["tag"] = "v0.0.0"
        d["distance"] = 1

        g = git.fetch(path, cache=d)
        self.assertEqual(g.sha, "2200dfa76743325303418980c363826ccfd7acbd")
        self.assertEqual(g.sha_abbrev, "2200dfa")
        self.assertEqual(g.branch, "master")
        self.assertEqual(
            g.date,
            datetime.datetime.fromisoformat("2023-08-23T12:53:05-07:00"),
        )
        self.assertFalse(g.is_dirty)
        self.assertEqual(g.distance, 0)
        self.assertEqual(g.tag, "v0.1.0")

    def test_dict(self) -> None:
        major = self.random_int(0, 100)
        minor = self.random_int(0, 100)
        patch = self.random_int(0, 100)
        sha = self.random_sha()
        target = {
            "tag": f"v{major}.{minor}.{patch}-rc1",
            "tag_prefix": "v",
            "sha": sha,
            "sha_abbrev": sha[:7],
            "branch": "master",
            "date": datetime.datetime.now(datetime.timezone.utc),
            "dirty": False,
            "distance": self.random_int(0, 100),
            "pretty_str": f"v{major}.{minor}.{patch}-rc1",
            "git_dir": "something",
        }
        g = git.GitVer(**target)
        d = g.asdict(include_git_dir=True)
        self.assertDictEqual(d, target)
        self.assertEqual(g, git.GitVer(**d))

        d = g.asdict(include_git_dir=False)
        self.assertIsNone(d["git_dir"])

        d["date"] = d["date"].isoformat()
        self.assertEqual(g, git.GitVer(**d))

        d = g.asdict(isoformat_date=True)
        self.assertEqual(g, git.GitVer(**d))

    def test_build_semver(self) -> None:
        # git-6 is tagged as a RC and is dirty
        path = self._DATA_ROOT.joinpath("git-6")
        g = git.fetch(
            path=path,
            tag_prefix="ver",
            dirty_in_pre=True,
            distance_in_pre=True,
            sha_in_pre=True,
            sha_abbrev_in_pre=True,
            date_in_pre=True,
        )
        d = g.asdict()
        sha = "ea4d6f6162f033dd6a8056498def4d42980a531f"
        sha_abbrev = sha[:7]

        s = str(g)
        target = f"0.0.0-rc1.p0.dirty.g{sha}.g{sha_abbrev}.20220719T185017Z"
        self.assertEqual(s, target)

        g = git.GitVer(
            dirty_in_pre=False,
            distance_in_pre=False,
            sha_in_pre=False,
            sha_abbrev_in_pre=False,
            date_in_pre=False,
            **d,
        )
        s = str(g)
        target = f"0.0.0-rc1+p0.dirty.g{sha}.g{sha_abbrev}.20220719T185017Z"
        self.assertEqual(s, target)

        g = git.GitVer(
            dirty_in_pre=None,
            distance_in_pre=None,
            sha_in_pre=None,
            sha_abbrev_in_pre=None,
            date_in_pre=None,
            **d,
        )
        s = str(g)
        target = "0.0.0-rc1"
        self.assertEqual(s, target)

    def test_str(self) -> None:
        # git-0 has a branch and is dirty
        path = self._DATA_ROOT.joinpath("git-0")
        g = git.fetch(path=path)
        s = str(g)
        target = "1.2.3-rc1.p0.dirty.gdd0ae6e+20220718T180126Z"
        self.assertEqual(s, target)
        self.assertEqual(g.semver, target)

        d = g.asdict()

        target = f"<witch_ver.git.GitVer '{s}'>"
        self.assertEqual(repr(g), target)

        d["pretty_str"] = git.str_func_pep440
        s = str(git.GitVer(**d))
        target = "1.2.3-rc1+0.gdd0ae6e.dirty"
        self.assertEqual(s, target)

        d["pretty_str"] = git.str_func_git_describe
        s = str(git.GitVer(**d))
        target = "v1.2.3-rc1-dirty"
        self.assertEqual(s, target)

        d["pretty_str"] = git.str_func_git_describe_long
        s = str(git.GitVer(**d))
        target = "v1.2.3-rc1-0-gdd0ae6e-dirty"
        self.assertEqual(s, target)

        # Fake being not dirty
        d["dirty"] = False
        d["pretty_str"] = git.str_func_pep440
        s = str(git.GitVer(**d))
        target = "1.2.3-rc1"
        self.assertEqual(s, target)

        d["pretty_str"] = git.str_func_git_describe
        s = str(git.GitVer(**d))
        target = "v1.2.3-rc1"
        self.assertEqual(s, target)

        # Remove tag_prefix from tag
        d["tag"] = d["tag"][1:]
        d["pretty_str"] = git.str_func_pep440
        s = str(git.GitVer(**d))
        target = "1.2.3-rc1"
        self.assertEqual(s, target)

        # git-1 is an empty repo with no commits
        path = self._DATA_ROOT.joinpath("git-1")
        g = git.fetch(path=path, custom_str_func=git.str_func_pep440)
        s = str(g)
        target = "0+untagged"
        self.assertEqual(s, target)

        d = g.asdict()

        d["pretty_str"] = git.str_func_git_describe
        s = str(git.GitVer(**d))
        target = "v0.0.0-untagged-0-g"
        self.assertEqual(s, target)

        d["tag_prefix"] = ""
        d["pretty_str"] = git.str_func_git_describe_long
        s = str(git.GitVer(**d))
        target = "0.0.0-untagged-0-g"
        self.assertEqual(s, target)

        # git-4 has no branches but is detached
        # Has a change in the index
        path = self._DATA_ROOT.joinpath("git-4")
        g = git.fetch(path=path)
        s = str(g)
        target = "0.0.0-untagged.p2.dirty.gf70f3f5+20220718T190625Z"
        self.assertEqual(s, target)
        s = str(g.semver)
        self.assertEqual(s, target)

        d = g.asdict()

        d["pretty_str"] = git.str_func_pep440
        s = str(git.GitVer(**d))
        target = "0+untagged.2.gf70f3f5.dirty"
        self.assertEqual(s, target)

        d["pretty_str"] = git.str_func_git_describe
        s = str(git.GitVer(**d))
        target = "f70f3f5-dirty"
        self.assertEqual(s, target)

        d["pretty_str"] = git.str_func_git_describe_long
        s = str(git.GitVer(**d))
        target = "f70f3f5-dirty"
        self.assertEqual(s, target)

        # Fake being not dirty
        d["dirty"] = False
        d["pretty_str"] = git.str_func_pep440
        s = str(git.GitVer(**d))
        target = "0+untagged.2.gf70f3f5"
        self.assertEqual(s, target)
