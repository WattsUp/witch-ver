"""Test module git
"""

import datetime
import pathlib
import zipfile

from witch_ver import git

from tests import base


class TestGit(base.TestBase):
  """Test Git
  """

  @classmethod
  def setUpClass(cls):
    super().setUpClass()

    # Can't commit a git repo to this repo
    # Test repos are zipped, extract before testing
    for i in range(7):
      path = cls._DATA_ROOT.joinpath(f"git-{i}")
      if not path.exists():
        z = path.with_suffix(".zip")
        with zipfile.ZipFile(z, "r") as z_file:
          z_file.extractall(path)

  def test_init(self):
    g = git.Git()
    self.assertEqual(pathlib.Path(".").resolve(), g._path.resolve())  # pylint: disable=protected-access

    path = self._DATA_ROOT.joinpath("git", "git-0")
    g = git.Git(path=path)
    self.assertEqual(path.resolve(), g._path.resolve())  # pylint: disable=protected-access

  def test_fetch_git_info(self):
    # This will always be in a git repo of witch-ver,
    # shouldn't touch the parent, so mock the call
    original_run = git.runner.run
    try:
      git.runner.run = lambda *args, **kwargs: (
          "fatal: not a git repository "
          "(or any of the parent directories): .git", 128)
      g = git.Git()
      self.assertRaises(RuntimeError, g.fetch_git_info)

      # Grab all the properties that run fetch_git_info
      # Do it here to avoid running slow git commands
      self.assertRaises(RuntimeError, getattr, g, "sha")
      self.assertRaises(RuntimeError, getattr, g, "sha_abbrev")
      self.assertRaises(RuntimeError, getattr, g, "branch")
      self.assertRaises(RuntimeError, getattr, g, "date")
      self.assertRaises(RuntimeError, getattr, g, "is_dirty")
      self.assertRaises(RuntimeError, getattr, g, "distance")
      self.assertRaises(RuntimeError, getattr, g, "tag")
    finally:
      git.runner.run = original_run

    # git-0 has a branch and is dirty
    path = self._DATA_ROOT.joinpath("git-0")
    g = git.Git(path=path)
    g.fetch_git_info()
    self.assertEqual("dd0ae6e1409910a9189da369864554785f9b0d01", g.sha)
    self.assertEqual("dd0ae6e", g.sha_abbrev)
    self.assertEqual("feat/nothing", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T11:01:26-07:00"), g.date)
    self.assertTrue(g.is_dirty)
    self.assertEqual(0, g.distance)
    self.assertEqual("v1.2.3-rc1", g.tag)

    # git-1 is an empty repo with no commits
    path = self._DATA_ROOT.joinpath("git-1")
    g = git.Git(path=path)
    g.fetch_git_info()
    self.assertEqual("", g.sha)
    self.assertEqual("", g.sha_abbrev)
    self.assertEqual("master", g.branch)
    now = datetime.datetime.now()
    difference = abs((g.date - now).total_seconds())
    self.assertLessEqual(difference, 60)
    self.assertFalse(g.is_dirty)
    self.assertEqual(0, g.distance)
    self.assertEqual(None, g.tag)

    # git-2 has a branch but is detached
    path = self._DATA_ROOT.joinpath("git-2")
    g = git.Git(path=path)
    self.assertEqual("b23ba426ab23f9bf525691e7550fc57afee48dd8", g.sha)
    self.assertEqual("b23ba42", g.sha_abbrev)
    self.assertEqual("feat/something", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T11:55:17-07:00"), g.date)
    self.assertTrue(g.is_dirty)
    self.assertEqual(1, g.distance)
    self.assertEqual("v0.0.0", g.tag)

    # -dirty tag doesn't match REGEX
    g = git.Git(path=path, describe_args=["--tags", "--dirty"])
    self.assertRaises(ValueError, g.fetch_git_info)

    # git-3 is detached from the master branch
    # Has a change in the index but reverted in the working tree
    path = self._DATA_ROOT.joinpath("git-3")
    g = git.Git(path=path, tag_prefix=None)
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
    g = git.Git(path=path)
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
    g = git.Git(path=path, tag_prefix=None)
    self.assertEqual("f70f3f504000d80d45922c213e3cc3dba9bc8e2c", g.sha)
    self.assertEqual("f70f3f5", g.sha_abbrev)
    self.assertEqual("main", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"), g.date)
    self.assertFalse(g.is_dirty)
    self.assertEqual(1, g.distance)
    self.assertEqual("0.0.0", g.tag)

  def test_build_semver(self):
    # git-6 is tagged as a RC and is dirty
    path = self._DATA_ROOT.joinpath("git-6")
    g = git.Git(path=path,
                dirty_in_pre=True,
                distance_in_pre=True,
                sha_in_pre=True,
                sha_abbrev_in_pre=True,
                date_in_pre=True)
    sha = "ea4d6f6162f033dd6a8056498def4d42980a531f"
    sha_abbrev = sha[:7]

    self.assertRaises(ValueError, g.build_semver)

    g._tag_prefix = "ver"  # pylint: disable=protected-access

    s = str(g.semver)
    target = f"0.0.0-rc1.p0.dirty.g{sha}.g{sha_abbrev}.20220719T185017Z"
    self.assertEqual(target, s)

    g._dirty_in_pre = False  # pylint: disable=protected-access
    g._distance_in_pre = False  # pylint: disable=protected-access
    g._sha_in_pre = False  # pylint: disable=protected-access
    g._sha_abbrev_in_pre = False  # pylint: disable=protected-access
    g._date_in_pre = False  # pylint: disable=protected-access

    g.build_semver()
    s = str(g.semver)
    target = f"0.0.0-rc1+p0.dirty.g{sha}.g{sha_abbrev}.20220719T185017Z"
    self.assertEqual(target, s)

    g._dirty_in_pre = None  # pylint: disable=protected-access
    g._distance_in_pre = None  # pylint: disable=protected-access
    g._sha_in_pre = None  # pylint: disable=protected-access
    g._sha_abbrev_in_pre = None  # pylint: disable=protected-access
    g._date_in_pre = None  # pylint: disable=protected-access

    g.build_semver()
    s = str(g.semver)
    target = "0.0.0-rc1"
    self.assertEqual(target, s)

    # git-3 is detached from the master branch
    # Has a change in the index but reverted in the working tree
    path = self._DATA_ROOT.joinpath("git-3")
    g = git.Git(path=path)
    s = str(g.semver)
    target = "0.0.0-untagged.p2.gf70f3f5+20220718T190625Z"
    self.assertEqual(target, s)

  def test_str(self):
    # git-0 has a branch and is dirty
    path = self._DATA_ROOT.joinpath("git-0")
    g = git.Git(path=path)
    s = str(g)
    target = "1.2.3-rc1.p0.dirty.gdd0ae6e+20220718T180126Z"
    self.assertEqual(target, s)
    s = str(g.semver)
    self.assertEqual(target, s)

    target = f"<witch_ver.git.Git '{s}'>"
    self.assertEqual(target, repr(g))

    g._custom_str_func = git.str_func_pep440  # pylint: disable=protected-access
    s = str(g)
    target = "v1.2.3-rc1+0.gdd0ae6e.dirty"
    self.assertEqual(target, s)

    g._custom_str_func = git.str_func_git_describe  # pylint: disable=protected-access
    s = str(g)
    target = "v1.2.3-rc1-dirty"
    self.assertEqual(target, s)

    g._custom_str_func = git.str_func_git_describe_long  # pylint: disable=protected-access
    s = str(g)
    target = "v1.2.3-rc1-0-gdd0ae6e-dirty"
    self.assertEqual(target, s)

    # Fake being not dirty
    g._dirty = False  # pylint: disable=protected-access
    g._custom_str_func = git.str_func_pep440  # pylint: disable=protected-access
    s = str(g)
    target = "v1.2.3-rc1"
    self.assertEqual(target, s)

    g._custom_str_func = git.str_func_git_describe  # pylint: disable=protected-access
    s = str(g)
    target = "v1.2.3-rc1"
    self.assertEqual(target, s)

    # git-1 is an empty repo with no commits
    path = self._DATA_ROOT.joinpath("git-1")
    g = git.Git(path=path, custom_str_func=git.str_func_pep440)
    s = str(g)
    target = "0+untagged"
    self.assertEqual(target, s)

    g._custom_str_func = git.str_func_git_describe  # pylint: disable=protected-access
    s = str(g)
    target = "v0.0.0-untagged-0-g"
    self.assertEqual(target, s)

    g._custom_str_func = git.str_func_git_describe_long  # pylint: disable=protected-access
    g._tag_prefix = ""  # pylint: disable=protected-access
    s = str(g)
    target = "0.0.0-untagged-0-g"
    self.assertEqual(target, s)

    # git-4 has no branches but is detached
    # Has a change in the index
    path = self._DATA_ROOT.joinpath("git-4")
    g = git.Git(path=path)
    s = str(g)
    target = "0.0.0-untagged.p2.dirty.gf70f3f5+20220718T190625Z"
    self.assertEqual(target, s)
    s = str(g.semver)
    self.assertEqual(target, s)

    g._custom_str_func = git.str_func_pep440  # pylint: disable=protected-access
    s = str(g)
    target = "0+untagged.2.gf70f3f5.dirty"
    self.assertEqual(target, s)

    g._custom_str_func = git.str_func_git_describe  # pylint: disable=protected-access
    s = str(g)
    target = "f70f3f5-dirty"
    self.assertEqual(target, s)

    g._custom_str_func = git.str_func_git_describe_long  # pylint: disable=protected-access
    s = str(g)
    target = "f70f3f5-dirty"
    self.assertEqual(target, s)

    # Fake being not dirty
    g._dirty = False  # pylint: disable=protected-access
    g._custom_str_func = git.str_func_pep440  # pylint: disable=protected-access
    s = str(g)
    target = "0+untagged.2.gf70f3f5"
    self.assertEqual(target, s)
