"""Test module git
"""

import datetime
import random
import time
import zipfile

from witch_ver import git

from tests import base


class TestGit(base.TestBase):
  """Test git
  """

  @classmethod
  def setUpClass(cls):
    super().setUpClass()

    # Can't commit a git repo to this repo
    # Test repos are zipped, extract before testing
    for i in range(8):
      path = cls._DATA_ROOT.joinpath(f"git-{i}")
      if not path.exists():
        z = path.with_suffix(".zip")
        with zipfile.ZipFile(z, "r") as z_file:
          z_file.extractall(path)

  def test_init(self):
    g = git.GitVer()
    self.assertEqual(g, "0.0.0-untagged")

    s = "1.2.3-alpha+metadata"
    g = git.GitVer(tag=s)
    self.assertEqual(g, s)

    self.assertRaises(TypeError, git.GitVer, tag=s, not_a_keyword=None)

  def test_fetch(self):
    path = self._DATA_ROOT.joinpath("git-0")
    # This will always be in a git repo of witch-ver,
    # shouldn't touch the parent, so mock the call
    original_run = git.runner.run
    try:
      git.runner.run = lambda *args, **kwargs: (
          "fatal: not a git repository "
          "(or any of the parent directories): .git", 128)
      self.assertRaises(RuntimeError, git.fetch, path)
    finally:
      git.runner.run = original_run

    # git-0 has a branch and is dirty
    path = self._DATA_ROOT.joinpath("git-0")
    g = git.fetch(path)
    self.assertEqual("dd0ae6e1409910a9189da369864554785f9b0d01", g.sha)
    self.assertEqual("dd0ae6e", g.sha_abbrev)
    self.assertEqual("feat/nothing", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T11:01:26-07:00"), g.date)
    self.assertTrue(g.is_dirty)
    self.assertEqual(0, g.distance)
    self.assertEqual("v1.2.3-rc1", g.tag)
    self.assertEqual(path.joinpath(".git"), g.git_dir)

    # git-1 is an empty repo with no commits
    path = self._DATA_ROOT.joinpath("git-1")
    g = git.fetch(path)
    self.assertEqual("", g.sha)
    self.assertEqual("", g.sha_abbrev)
    self.assertEqual("master", g.branch)
    now = datetime.datetime.now()
    difference = abs((g.date - now).total_seconds())
    self.assertLessEqual(difference, 60)
    self.assertFalse(g.is_dirty)
    self.assertEqual(0, g.distance)
    self.assertEqual(None, g.tag)
    self.assertEqual(path.joinpath(".git"), g.git_dir)

    # Child folder will fail
    path = self._DATA_ROOT.joinpath("git-1", "child")
    self.assertRaises(RuntimeError, git.fetch, path)

    # git-2 has a branch but is detached
    path = self._DATA_ROOT.joinpath("git-2")
    g = git.fetch(path)
    self.assertEqual("b23ba426ab23f9bf525691e7550fc57afee48dd8", g.sha)
    self.assertEqual("b23ba42", g.sha_abbrev)
    self.assertEqual("feat/something", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T11:55:17-07:00"), g.date)
    self.assertTrue(g.is_dirty)
    self.assertEqual(1, g.distance)
    self.assertEqual("v0.0.0", g.tag)

    # -dirty tag doesn't match REGEX
    self.assertRaises(ValueError,
                      git.fetch,
                      path,
                      describe_args=["--tags", "--dirty"])

    # git-3 is detached from the master branch
    # Has a change in the index but reverted in the working tree
    path = self._DATA_ROOT.joinpath("git-3")
    g = git.fetch(path, tag_prefix=None)
    self.assertEqual("f70f3f504000d80d45922c213e3cc3dba9bc8e2c", g.sha)
    self.assertEqual("f70f3f5", g.sha_abbrev)
    self.assertEqual("master", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"), g.date)
    self.assertFalse(g.is_dirty)
    self.assertEqual(1, g.distance)
    self.assertEqual("0.0.0", g.tag)

    # git-4 has no branches but is detached
    # Has a change in the index
    path = self._DATA_ROOT.joinpath("git-4")
    g = git.fetch(path)
    self.assertEqual("f70f3f504000d80d45922c213e3cc3dba9bc8e2c", g.sha)
    self.assertEqual("f70f3f5", g.sha_abbrev)
    self.assertEqual(None, g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"), g.date)
    self.assertTrue(g.is_dirty)
    self.assertEqual(2, g.distance)
    self.assertEqual(None, g.tag)

    # git-5 is detached from the main branch
    # Has a change in the index but reverted in the working tree
    path = self._DATA_ROOT.joinpath("git-5")
    start = time.perf_counter()
    g = git.fetch(path, tag_prefix=None)
    elapsed_slow = time.perf_counter() - start
    self.assertEqual("f70f3f504000d80d45922c213e3cc3dba9bc8e2c", g.sha)
    self.assertEqual("f70f3f5", g.sha_abbrev)
    self.assertEqual("main", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"), g.date)
    self.assertFalse(g.is_dirty)
    self.assertEqual(1, g.distance)
    self.assertEqual("0.0.0", g.tag)

    d = g.asdict()
    start = time.perf_counter()
    g = git.fetch(path, tag_prefix=None, cache=d)
    elapsed_cached = time.perf_counter() - start
    self.assertEqual("f70f3f504000d80d45922c213e3cc3dba9bc8e2c", g.sha)
    self.assertEqual("f70f3f5", g.sha_abbrev)
    self.assertEqual("main", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"), g.date)
    self.assertFalse(g.is_dirty)
    self.assertEqual(1, g.distance)
    self.assertEqual("0.0.0", g.tag)

    self.log_speed(elapsed_slow, elapsed_cached)
    self.assertGreater(elapsed_slow, elapsed_cached)

    # This won't use the partial cache
    d.pop("branch")
    g = git.fetch(path, tag_prefix=None, cache=d)
    self.assertEqual("f70f3f504000d80d45922c213e3cc3dba9bc8e2c", g.sha)
    self.assertEqual("f70f3f5", g.sha_abbrev)
    self.assertEqual("main", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"), g.date)
    self.assertFalse(g.is_dirty)
    self.assertEqual(1, g.distance)
    self.assertEqual("0.0.0", g.tag)

    # git-7 is a standard repo
    # But the cache was updated before v0.1.0 tag was added
    # Expect to rerun to get new tag name
    path = self._DATA_ROOT.joinpath("git-7")
    g = git.fetch(path=path)
    d = g.asdict()
    d["tag"] = "v0.0.0"
    d["distance"] = 1

    g = git.fetch(path, cache=d)
    self.assertEqual("2200dfa76743325303418980c363826ccfd7acbd", g.sha)
    self.assertEqual("2200dfa", g.sha_abbrev)
    self.assertEqual("master", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2023-08-23T12:53:05-07:00"), g.date)
    self.assertFalse(g.is_dirty)
    self.assertEqual(0, g.distance)
    self.assertEqual("v0.1.0", g.tag)

  def test_dict(self):
    major = random.randint(0, 100)
    minor = random.randint(0, 100)
    patch = random.randint(0, 100)
    sha = f"{random.getrandbits(64):X}"
    target = {
        "tag": f"v{major}.{minor}.{patch}-rc1",
        "tag_prefix": "v",
        "sha": sha,
        "sha_abbrev": sha[:7],
        "branch": "master",
        "date": datetime.datetime.now(),
        "dirty": False,
        "distance": random.randint(0, 100),
        "pretty_str": f"v{major}.{minor}.{patch}-rc1",
        "git_dir": "something"
    }
    g = git.GitVer(**target)
    d = g.asdict(include_git_dir=True)
    self.assertDictEqual(target, d)
    self.assertEqual(g, git.GitVer(**d))

    d = g.asdict(include_git_dir=False)
    self.assertEqual(None, d["git_dir"])

    d["date"] = d["date"].isoformat()
    self.assertEqual(g, git.GitVer(**d))

    d = g.asdict(isoformat_date=True)
    self.assertEqual(g, git.GitVer(**d))

  def test_build_semver(self):
    # git-6 is tagged as a RC and is dirty
    path = self._DATA_ROOT.joinpath("git-6")
    g = git.fetch(path=path,
                  tag_prefix="ver",
                  dirty_in_pre=True,
                  distance_in_pre=True,
                  sha_in_pre=True,
                  sha_abbrev_in_pre=True,
                  date_in_pre=True)
    d = g.asdict()
    sha = "ea4d6f6162f033dd6a8056498def4d42980a531f"
    sha_abbrev = sha[:7]

    s = str(g)
    target = f"0.0.0-rc1.p0.dirty.g{sha}.g{sha_abbrev}.20220719T185017Z"
    self.assertEqual(target, s)

    g = git.GitVer(dirty_in_pre=False,
                   distance_in_pre=False,
                   sha_in_pre=False,
                   sha_abbrev_in_pre=False,
                   date_in_pre=False,
                   **d)
    s = str(g)
    target = f"0.0.0-rc1+p0.dirty.g{sha}.g{sha_abbrev}.20220719T185017Z"
    self.assertEqual(target, s)

    g = git.GitVer(dirty_in_pre=None,
                   distance_in_pre=None,
                   sha_in_pre=None,
                   sha_abbrev_in_pre=None,
                   date_in_pre=None,
                   **d)
    s = str(g)
    target = "0.0.0-rc1"
    self.assertEqual(target, s)

  def test_str(self):
    # git-0 has a branch and is dirty
    path = self._DATA_ROOT.joinpath("git-0")
    g = git.fetch(path=path)
    s = str(g)
    target = "1.2.3-rc1.p0.dirty.gdd0ae6e+20220718T180126Z"
    self.assertEqual(target, s)
    self.assertEqual(target, g.semver)

    d = g.asdict()

    target = f"<witch_ver.git.GitVer '{s}'>"
    self.assertEqual(target, repr(g))

    d["pretty_str"] = git.str_func_pep440
    s = str(git.GitVer(**d))
    target = "1.2.3-rc1+0.gdd0ae6e.dirty"
    self.assertEqual(target, s)

    d["pretty_str"] = git.str_func_git_describe
    s = str(git.GitVer(**d))
    target = "v1.2.3-rc1-dirty"
    self.assertEqual(target, s)

    d["pretty_str"] = git.str_func_git_describe_long
    s = str(git.GitVer(**d))
    target = "v1.2.3-rc1-0-gdd0ae6e-dirty"
    self.assertEqual(target, s)

    # Fake being not dirty
    d["dirty"] = False
    d["pretty_str"] = git.str_func_pep440
    s = str(git.GitVer(**d))
    target = "1.2.3-rc1"
    self.assertEqual(target, s)

    d["pretty_str"] = git.str_func_git_describe
    s = str(git.GitVer(**d))
    target = "v1.2.3-rc1"
    self.assertEqual(target, s)

    # Remove tag_prefix from tag
    d["tag"] = d["tag"][1:]
    d["pretty_str"] = git.str_func_pep440
    s = str(git.GitVer(**d))
    target = "1.2.3-rc1"
    self.assertEqual(target, s)

    # git-1 is an empty repo with no commits
    path = self._DATA_ROOT.joinpath("git-1")
    g = git.fetch(path=path, custom_str_func=git.str_func_pep440)
    s = str(g)
    target = "0+untagged"
    self.assertEqual(target, s)

    d = g.asdict()

    d["pretty_str"] = git.str_func_git_describe
    s = str(git.GitVer(**d))
    target = "v0.0.0-untagged-0-g"
    self.assertEqual(target, s)

    d["tag_prefix"] = ""
    d["pretty_str"] = git.str_func_git_describe_long
    s = str(git.GitVer(**d))
    target = "0.0.0-untagged-0-g"
    self.assertEqual(target, s)

    # git-4 has no branches but is detached
    # Has a change in the index
    path = self._DATA_ROOT.joinpath("git-4")
    g = git.fetch(path=path)
    s = str(g)
    target = "0.0.0-untagged.p2.dirty.gf70f3f5+20220718T190625Z"
    self.assertEqual(target, s)
    s = str(g.semver)
    self.assertEqual(target, s)

    d = g.asdict()

    d["pretty_str"] = git.str_func_pep440
    s = str(git.GitVer(**d))
    target = "0+untagged.2.gf70f3f5.dirty"
    self.assertEqual(target, s)

    d["pretty_str"] = git.str_func_git_describe
    s = str(git.GitVer(**d))
    target = "f70f3f5-dirty"
    self.assertEqual(target, s)

    d["pretty_str"] = git.str_func_git_describe_long
    s = str(git.GitVer(**d))
    target = "f70f3f5-dirty"
    self.assertEqual(target, s)

    # Fake being not dirty
    d["dirty"] = False
    d["pretty_str"] = git.str_func_pep440
    s = str(git.GitVer(**d))
    target = "0+untagged.2.gf70f3f5"
    self.assertEqual(target, s)
