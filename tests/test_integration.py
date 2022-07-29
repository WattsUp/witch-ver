"""Test module integration
"""

import importlib.util
import io
import pathlib
import os
import re
import sys
import textwrap
from types import ModuleType
from unittest import mock
import zipfile

from witch_ver import integration

from tests import base


class TestIntegration(base.TestBase):
  """Test integration
  """

  @classmethod
  def setUpClass(cls):
    super().setUpClass()

    # Can't commit a git repo to this repo
    # Test repos are zipped, extract before testing
    for i in range(3):
      path = cls._DATA_ROOT.joinpath(f"package-{i + 1}")
      if not path.exists():
        z = path.with_suffix(".zip")
        with zipfile.ZipFile(z, "r") as z_file:
          z_file.extractall(path)

  def _import(self, path: pathlib.Path) -> ModuleType:
    name = path.name.strip(".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

  def test_use_witch_ver_1(self):
    integration.use_witch_ver(None, None, False)

    value = {"custom_str_func": None}
    self.assertRaises(TypeError, integration.use_witch_ver, None, None, value)

    self.assertRaises(TypeError, integration.use_witch_ver, None, None,
                      lambda: {"custom_str_func": None})

    self._test_use_witch_ver_package1()
    self._test_use_witch_ver_package2()
    self._test_use_witch_ver_package3()

  def _test_use_witch_ver_package1(self):
    orig_open = open
    mock_files = {}

    def mock_open(fname: str, *args, **kwargs):
      if str(fname) in mock_files:
        return mock_files[str(fname)]
      return orig_open(fname, *args, **kwargs)

    # Change folder to package-1
    # use_witch_ver = True
    package = self._DATA_ROOT.joinpath("package-1")
    setup = self._import(package.joinpath("setup.py"))
    orig_cwd = os.getcwd()
    orig_argv = sys.argv
    try:
      os.chdir(package)
      sys.argv = ["setup.py", "--version"]

      path_ver = str(package.joinpath("hello", "version.py"))

      # Prepare the expected output for version.py
      path_version_hook = pathlib.Path(
          integration.__file__).with_name("version_hook.py")
      with open(path_version_hook, "r", encoding="utf-8") as file:
        target_ver = file.read()
      target_version_dict = textwrap.dedent("""\
      version_dict = {
          "tag": "v0.0.0",
          "tag_prefix": "v",
          "sha": "d78b554b4fc9ad5bdf844a4702c6a06d7ae5fdcb",
          "sha_abbrev": "d78b554",
          "branch": "master",
          "date": "2022-07-29T13:08:23-07:00",
          "dirty": False,
          "distance": 1,
          "pretty_str": "0.0.0+1.gd78b554",
          "git_dir": None
      }""")
      target_ver = re.sub(r"version_dict = {.*?}",
                          target_version_dict,
                          target_ver,
                          count=1,
                          flags=re.S)

      # Prepare the expected output for __init__.py
      path_init = str(package.joinpath("hello", "__init__.py"))
      with open(path_init, "r", encoding="utf-8") as file:
        orig_init = file.read()
      target_init = textwrap.dedent('''\
      """Hello-world
      """

      from hello.version import __version__

      from hello.world import MSG
      ''')

      # Set up mock_files
      mock_files = {
          path_ver: mock.mock_open().return_value,
          path_init: mock.mock_open(read_data=orig_init).return_value
      }
      with mock.patch("builtins.open", mock_open):
        with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
          setup.setup()

        # Validate setup.py got proper version
        self.assertEqual("0.0.0+1.gd78b554", fake_stdout.getvalue().strip())

        # Validate version.py got written
        mock_file: mock.MagicMock = mock_files[path_ver]
        handle_r: mock.MagicMock = mock_file.read
        handle_r.assert_not_called()

        handle_w: mock.MagicMock = mock_file.write
        handle_w.assert_called_once_with(target_ver)

        # Validate __init__.py got written
        mock_file: mock.MagicMock = mock_files[path_init]
        handle_r: mock.MagicMock = mock_file.read
        handle_r.assert_called_once()

        handle_w: mock.MagicMock = mock_file.write
        handle_w.assert_called_once_with(target_init)

    finally:
      os.chdir(orig_cwd)
      sys.argv = orig_argv

  def _test_use_witch_ver_package2(self):
    orig_open = open
    mock_files = {}

    def mock_open(fname: str, *args, **kwargs):
      if str(fname) in mock_files:
        return mock_files[str(fname)]
      return orig_open(fname, *args, **kwargs)

    def mock_fetch(*args, **kwargs):
      raise RuntimeError

    # Change folder to package-2
    # use_witch_ver = {"custom_str_func": "str_func_pep440"}
    # And doesn't have a properly formatted docstring
    package = self._DATA_ROOT.joinpath("package-2")
    setup = self._import(package.joinpath("setup.py"))
    orig_cwd = os.getcwd()
    orig_argv = sys.argv
    try:
      os.chdir(package)
      sys.argv = ["setup.py", "--version"]

      path_ver = str(package.joinpath("hello", "version.py"))

      # Prepare the expected output for version.py
      path_version_hook = pathlib.Path(
          integration.__file__).with_name("version_hook.py")
      with open(path_version_hook, "r", encoding="utf-8") as file:
        target_ver = file.read()
      target_version_dict = textwrap.dedent("""\
      version_dict = {
          "tag": "v0.0.0",
          "tag_prefix": "v",
          "sha": "93d84de0a95250fbacac83671f6f1ad7fb236742",
          "sha_abbrev": "93d84de",
          "branch": "master",
          "date": "2022-07-29T13:46:13-07:00",
          "dirty": False,
          "distance": 2,
          "pretty_str": "0.0.0+2.g93d84de",
          "git_dir": None
      }""")
      target_ver = re.sub(r"version_dict = {.*?}",
                          target_version_dict,
                          target_ver,
                          count=1,
                          flags=re.S)

      # Prepare the expected output for __init__.py
      path_init = str(package.joinpath("hello", "__init__.py"))
      with open(path_init, "r", encoding="utf-8") as file:
        orig_init = file.read()
      target_init = textwrap.dedent('''\
      # Hello-world module is missing PEP0257 docstring

      from hello.world import MSG

      from hello.version import __version__
      ''')

      # Set up mock_files
      mock_files = {
          path_ver: mock.mock_open().return_value,
          path_init: mock.mock_open(read_data=orig_init).return_value
      }
      with mock.patch("builtins.open", mock_open):
        with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
          setup.setup()

        # Validate setup.py got proper version
        self.assertEqual("0.0.0+2.g93d84de", fake_stdout.getvalue().strip())

        # Validate version.py got written
        mock_file: mock.MagicMock = mock_files[path_ver]
        handle_r: mock.MagicMock = mock_file.read
        handle_r.assert_not_called()

        handle_w: mock.MagicMock = mock_file.write
        handle_w.assert_called_once_with(target_ver)

        # Validate __init__.py got written
        mock_file: mock.MagicMock = mock_files[path_init]
        handle_r: mock.MagicMock = mock_file.read
        handle_r.assert_called_once()

        handle_w: mock.MagicMock = mock_file.write
        handle_w.assert_called_once_with(target_init)

      with mock.patch("builtins.open", mock_open):
        with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
          with mock.patch("witch_ver.git.fetch", mock_fetch):
            self.assertRaises(RuntimeError, setup.setup)
        self.assertEqual("", fake_stdout.getvalue())

    finally:
      os.chdir(orig_cwd)
      sys.argv = orig_argv

  def _test_use_witch_ver_package3(self):
    orig_open = open
    mock_files = {}

    def mock_open(fname: str, *args, **kwargs):
      if str(fname) in mock_files:
        return mock_files[str(fname)]
      return orig_open(fname, *args, **kwargs)

    def mock_fetch(*args, **kwargs):
      raise RuntimeError

    # Change folder to package-3
    # use_witch_ver = {"custom_str_func": str_func}
    # Already had integration ran
    package = self._DATA_ROOT.joinpath("package-3")
    setup = self._import(package.joinpath("setup.py"))
    orig_cwd = os.getcwd()
    orig_argv = sys.argv
    try:
      os.chdir(package)
      sys.argv = ["setup.py", "--version"]

      path_ver = str(package.joinpath("hello", "version.py"))

      # Prepare the expected output for version.py
      # Already exists so load that file
      with open(path_ver, "r", encoding="utf-8") as file:
        target_ver = file.read()

      # Prepare the expected output for __init__.py
      # Already installed so no changes
      path_init = str(package.joinpath("hello", "__init__.py"))
      with open(path_init, "r", encoding="utf-8") as file:
        orig_init = file.read()

      # Set up mock_files
      mock_files = {
          path_ver: mock.mock_open(read_data=target_ver).return_value,
          path_init: mock.mock_open(read_data=orig_init).return_value
      }
      with mock.patch("builtins.open", mock_open):
        with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
          setup.setup()

        # Validate setup.py got proper version
        self.assertEqual("0.0.0+3.6f14ed6dadf0327ea2ee869bcc275118e71f300a",
                         fake_stdout.getvalue().strip())

        # Validate version.py got written
        mock_file: mock.MagicMock = mock_files[path_ver]
        handle_r: mock.MagicMock = mock_file.read
        handle_r.assert_not_called()

        handle_w: mock.MagicMock = mock_file.write
        handle_w.assert_called_once_with(target_ver)

        # Validate __init__.py got written
        mock_file: mock.MagicMock = mock_files[path_init]
        handle_r: mock.MagicMock = mock_file.read
        handle_r.assert_called_once()

        handle_w: mock.MagicMock = mock_file.write
        handle_w.assert_not_called()

      # Set up mock_files
      mock_files = {
          path_ver: mock.mock_open(read_data=target_ver).return_value,
          path_init: mock.mock_open(read_data=orig_init).return_value
      }
      with mock.patch("builtins.open", mock_open):
        with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
          with mock.patch("witch_ver.git.fetch", mock_fetch):
            setup.setup()

        # Validate setup.py got proper version
        self.assertEqual("0.0.0+3.6f14ed6dadf0327ea2ee869bcc275118e71f300a",
                         fake_stdout.getvalue().strip())

        # Validate version.py got written
        mock_file: mock.MagicMock = mock_files[path_ver]
        handle_r: mock.MagicMock = mock_file.read
        handle_r.assert_called_once()

        handle_w: mock.MagicMock = mock_file.write
        handle_w.assert_called_once_with(target_ver)

        # Validate __init__.py got written
        mock_file: mock.MagicMock = mock_files[path_init]
        handle_r: mock.MagicMock = mock_file.read
        handle_r.assert_called_once()

        handle_w: mock.MagicMock = mock_file.write
        handle_w.assert_not_called()

    finally:
      os.chdir(orig_cwd)
      sys.argv = orig_argv
