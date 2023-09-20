"""Test module integration
"""

import importlib.util
import io
import os
import pathlib
import re
import shutil
import sys
import textwrap
import zipfile
from types import ModuleType
from unittest import mock

from tests import base
from witch_ver import integration


class TestIntegration(base.TestBase):
    """Test integration"""

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

    def test_write_matching_newline(self):
        path = self._TEST_ROOT.joinpath("version.txt")
        contents = "\n".join(self.random_string() for _ in range(10))

        def check_file(crlf: bool) -> None:
            """Check if contents match and line ending is proper

            Args:
              crlf: True will expect CRLF line endings, False for LF
            """
            with open(path, "r", encoding="utf-8") as file:
                buf = file.read()
                self.assertEqual(contents, buf)

            with open(path, "rb") as file:
                is_crlf = b"\r\n" in file.read()
                self.assertEqual(crlf, is_crlf)

        original_open = open

        calls = []

        def mock_open(fname: str, *args, **kwargs) -> object:
            calls.append({"file": fname, "args": args, "kwargs": kwargs})
            return original_open(fname, *args, **kwargs)

        # File does not exist yet
        calls.clear()
        with mock.patch("builtins.open", mock_open):
            integration._write_matching_newline(  # pylint: disable=protected-access
                path, contents
            )
        check_file(False)
        self.assertEqual(1, len(calls))
        self.assertEqual("wb", calls[0]["args"][0])

        # File does exist, no modifications to take place
        calls.clear()
        with mock.patch("builtins.open", mock_open):
            integration._write_matching_newline(  # pylint: disable=protected-access
                path, contents
            )
        check_file(False)
        self.assertEqual(1, len(calls))
        self.assertEqual("rb", calls[0]["args"][0])

        with open(path, "wb") as file:
            contents_b = contents.encode().replace(b"\n", b"\r\n")
            file.write(contents_b)

        # File does exist as CRLF, no modifications to take place
        calls.clear()
        with mock.patch("builtins.open", mock_open):
            integration._write_matching_newline(  # pylint: disable=protected-access
                path, contents
            )
        check_file(True)
        self.assertEqual(1, len(calls))
        self.assertEqual("rb", calls[0]["args"][0])

        # Modify contents
        contents += self.random_string()

        # File does exist as CRLF
        calls.clear()
        with mock.patch("builtins.open", mock_open):
            integration._write_matching_newline(  # pylint: disable=protected-access
                path, contents
            )
        check_file(True)
        self.assertEqual(2, len(calls))
        self.assertEqual("rb", calls[0]["args"][0])
        self.assertEqual("wb", calls[1]["args"][0])

    def test_use_witch_ver(self):
        # use_witch_ver = False
        integration.use_witch_ver(None, None, False)

        # use_witch_ver = config
        # custom_str_func is not callable
        value = {"custom_str_func": None}
        self.assertRaises(TypeError, integration.use_witch_ver, None, None, value)

        # use_witch_ver = function -> config
        # custom_str_func is not callable
        self.assertRaises(
            TypeError,
            integration.use_witch_ver,
            None,
            None,
            lambda: {"custom_str_func": None},
        )

        # use_witch_ver = function -> not a config
        self.assertRaises(
            ValueError, integration.use_witch_ver, None, None, lambda: "version"
        )

        # use_witch_ver = not a boolean or dictionary
        self.assertRaises(ValueError, integration.use_witch_ver, None, None, "version")

    def test_use_witch_ver_package1(self):
        path_package = self._DATA_ROOT.joinpath("package-1")
        path_test = self._TEST_ROOT.joinpath("package")
        shutil.copytree(path_package, path_test)

        setup = self._import(path_test.joinpath("setup.py"))

        # Change folder to package
        original_cwd = os.getcwd()
        original_argv = sys.argv
        try:
            os.chdir(path_test)
            sys.argv = ["setup.py", "--version"]

            path_version = path_test.joinpath("hello", "version.py")

            # Prepare the expected output for version.py
            path_version_hook = pathlib.Path(integration.__file__).with_name(
                "version_hook.py"
            )
            with open(path_version_hook, "r", encoding="utf-8") as file:
                target_ver = file.read()
            target_version_dict = textwrap.dedent(
                """\
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
      }"""
            )
            target_ver = re.sub(
                r"version_dict = {.*?}",
                target_version_dict,
                target_ver,
                count=1,
                flags=re.S,
            )

            # Prepare the expected output for __init__.py
            path_init = path_test.joinpath("hello", "__init__.py")
            target_init = textwrap.dedent(
                '''\
      """Hello-world
      """

      from hello.version import __version__

      from hello.world import MSG
      '''
            )

            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                setup.setup()

            # Validate setup.py got proper version
            self.assertEqual("0.0.0+1.gd78b554", fake_stdout.getvalue().strip())

            with open(path_version, "r", encoding="utf-8") as file:
                self.assertEqual(target_ver, file.read())

            with open(path_init, "r", encoding="utf-8") as file:
                self.assertEqual(target_init, file.read())

        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv

    def test_use_witch_ver_package2(self):
        path_package = self._DATA_ROOT.joinpath("package-2")
        path_test = self._TEST_ROOT.joinpath("package")
        shutil.copytree(path_package, path_test)

        setup = self._import(path_test.joinpath("setup.py"))

        # Change folder to package
        original_cwd = os.getcwd()
        original_argv = sys.argv
        try:
            os.chdir(path_test)
            sys.argv = ["setup.py", "--version"]

            path_version = path_test.joinpath("hello", "version.py")

            # Prepare the expected output for version.py
            path_version_hook = pathlib.Path(integration.__file__).with_name(
                "version_hook.py"
            )
            with open(path_version_hook, "r", encoding="utf-8") as file:
                target_ver = file.read()
            target_version_dict = textwrap.dedent(
                """\
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
      }"""
            )
            target_ver = re.sub(
                r"version_dict = {.*?}",
                target_version_dict,
                target_ver,
                count=1,
                flags=re.S,
            )

            # Prepare the expected output for __init__.py
            path_init = path_test.joinpath("hello", "__init__.py")
            target_init = textwrap.dedent(
                """\
      # Hello-world module is missing PEP0257 docstring

      from hello.world import MSG

      from hello.version import __version__
      """
            )

            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                setup.setup()

            # Validate setup.py got proper version
            self.assertEqual("0.0.0+2.g93d84de", fake_stdout.getvalue().strip())

            with open(path_version, "r", encoding="utf-8") as file:
                self.assertEqual(target_ver, file.read())

            with open(path_init, "r", encoding="utf-8") as file:
                self.assertEqual(target_init, file.read())

            # Mock outside of a git repository

            def mock_fetch(*args, **kwargs):
                raise RuntimeError

            # Succeeds since version.py exists
            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                with mock.patch("witch_ver.git.fetch", mock_fetch):
                    setup.setup()
            self.assertEqual("0.0.0+2.g93d84de", fake_stdout.getvalue().strip())

            # Fails since version.py does not exist
            path_version.unlink()
            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                with mock.patch("witch_ver.git.fetch", mock_fetch):
                    self.assertRaises(RuntimeError, setup.setup)
            self.assertEqual("", fake_stdout.getvalue().strip())

        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv

    def test_use_witch_ver_package3(self):
        path_package = self._DATA_ROOT.joinpath("package-3")
        path_test = self._TEST_ROOT.joinpath("package")
        shutil.copytree(path_package, path_test)

        setup = self._import(path_test.joinpath("setup.py"))

        # Change folder to package
        original_cwd = os.getcwd()
        original_argv = sys.argv
        try:
            os.chdir(path_test)
            sys.argv = ["setup.py", "--version"]

            path_version = path_test.joinpath("hello", "version.py")

            # Prepare the expected output for version.py
            # Already exists so load that file
            with open(path_version, "r", encoding="utf-8") as file:
                target_ver = file.read()

            # Prepare the expected output for __init__.py
            # Already installed so no changes
            path_init = path_test.joinpath("hello", "__init__.py")
            with open(path_init, "r", encoding="utf-8") as file:
                target_init = file.read()

            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                setup.setup()

            # Validate setup.py got proper version
            self.assertEqual(
                "0.0.0+4.29c921b55529e5a6ba963bcbcaf2f7e1d9f9efe6",
                fake_stdout.getvalue().strip(),
            )

            with open(path_version, "r", encoding="utf-8") as file:
                self.assertEqual(target_ver, file.read())

            with open(path_init, "r", encoding="utf-8") as file:
                self.assertEqual(target_init, file.read())

        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv
