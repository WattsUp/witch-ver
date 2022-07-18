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
    for i in range(6):
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

    # git-1 is an empty repo with no commits
    path = self._DATA_ROOT.joinpath("git-1")
    g = git.Git(path=path)
    self.assertRaises(RuntimeError, g.fetch_git_info)

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
    self.assertEqual(1, g.distance)
    self.assertEqual("v0.0.0", g.tag)

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
    g = git.Git(path=path, version_prefix=None)
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

    # git-3 is detached from the main branch
    # Has a change in the index but reverted in the working tree
    path = self._DATA_ROOT.joinpath("git-5")
    g = git.Git(path=path, version_prefix=None)
    self.assertEqual("f70f3f504000d80d45922c213e3cc3dba9bc8e2c", g.sha)
    self.assertEqual("f70f3f5", g.sha_abbrev)
    self.assertEqual("main", g.branch)
    self.assertEqual(
        datetime.datetime.fromisoformat("2022-07-18T12:06:25-07:00"), g.date)
    self.assertFalse(g.is_dirty)
    self.assertEqual(1, g.distance)
    self.assertEqual("0.0.0", g.tag)


