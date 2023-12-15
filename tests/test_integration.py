from __future__ import annotations

import io
import os
import re
import shutil
import sys
import textwrap
import zipfile
from pathlib import Path
from unittest import mock

from tests import base
from witch_ver import git, integration


class TestIntegration(base.TestBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # Can't commit a git repo to this repo
        # Test repos are zipped, extract before testing
        for i in range(3):
            path = cls._DATA_ROOT.joinpath(f"package-{i + 1}")
            if not path.exists():
                z = path.with_suffix(".zip")
                with zipfile.ZipFile(z, "r") as z_file:
                    z_file.extractall(path)

    def test_write_matching_newline(self) -> None:
        path = self._TEST_ROOT.joinpath("version.txt")
        contents = "\n".join(self.random_string() for _ in range(10))

        def check_file(*_, crlf: bool) -> None:
            """Check if contents match and line ending is proper.

            Args:
              crlf: True will expect CRLF line endings, False for LF
            """
            with path.open(encoding="utf-8") as file:
                buf = file.read()
                self.assertEqual(buf, contents)

            with path.open("rb") as file:
                is_crlf = b"\r\n" in file.read()
                self.assertEqual(is_crlf, crlf)

        original_open = io.open

        calls = []

        def mock_open(fname: str, *args, **kwargs) -> object:  # noqa: ANN002, ANN003
            calls.append({"file": fname, "args": args, "kwargs": kwargs})
            return original_open(fname, *args, **kwargs)

        try:
            io.open = mock_open

            # File does not exist yet
            calls.clear()
            integration._write_matching_newline(path, contents)  # noqa: SLF001
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["args"][0], "wb")
            check_file(crlf=False)

            # File does exist, no modifications to take place
            calls.clear()
            integration._write_matching_newline(path, contents)  # noqa: SLF001
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["args"][0], "rb")
            check_file(crlf=False)

            with path.open("wb") as file:
                contents_b = contents.encode().replace(b"\n", b"\r\n")
                file.write(contents_b)

            # File does exist as CRLF, no modifications to take place
            calls.clear()
            integration._write_matching_newline(path, contents)  # noqa: SLF001
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["args"][0], "rb")
            check_file(crlf=True)

            # Modify contents
            contents += self.random_string()

            # File does exist as CRLF
            calls.clear()
            integration._write_matching_newline(path, contents)  # noqa: SLF001
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0]["args"][0], "rb")
            self.assertEqual(calls[1]["args"][0], "wb")
            check_file(crlf=True)
        finally:
            io.open = original_open

    def test_use_witch_ver(self) -> None:
        # use_witch_ver is False
        integration.use_witch_ver(None, None, value=False)  # type: ignore[attr-defined]

        # use_witch_ver is a config
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
            ValueError,
            integration.use_witch_ver,
            None,
            None,
            lambda: "version",
        )

        # use_witch_ver = not a boolean or dictionary
        self.assertRaises(TypeError, integration.use_witch_ver, None, None, "version")

    def test_use_witch_ver_package1(self) -> None:
        path_package = self._DATA_ROOT.joinpath("package-1")
        path_test = self._TEST_ROOT.joinpath("package")
        shutil.copytree(path_package, path_test)

        setup = self.import_file(path_test.joinpath("setup.py"))

        # Change folder to package
        original_cwd = Path.cwd()
        original_argv = sys.argv
        try:
            os.chdir(path_test)
            sys.argv = ["setup.py", "--version"]

            path_version = path_test.joinpath("hello", "version.py")

            # Prepare the expected output for version.py
            path_version_hook = Path(integration.__file__).with_name(
                "version_hook.py",
            )
            with path_version_hook.open(encoding="utf-8") as file:
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
                    "git_dir": None,
                }""",
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
                ''',
            )

            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                setup.setup()

            # Validate setup.py got proper version
            self.assertEqual(fake_stdout.getvalue().strip(), "0.0.0+1.gd78b554")

            self.maxDiff = None
            with path_version.open(encoding="utf-8") as file:
                self.assertEqual(file.read(), target_ver)

            with path_init.open(encoding="utf-8") as file:
                self.assertEqual(file.read(), target_init)

        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv

    def test_use_witch_ver_package2(self) -> None:
        path_package = self._DATA_ROOT.joinpath("package-2")
        path_test = self._TEST_ROOT.joinpath("package")
        shutil.copytree(path_package, path_test)

        setup = self.import_file(path_test.joinpath("setup.py"))

        # Change folder to package
        original_cwd = Path.cwd()
        original_argv = sys.argv
        try:
            os.chdir(path_test)
            sys.argv = ["setup.py", "--version"]

            path_version = path_test.joinpath("hello", "version.py")

            # Prepare the expected output for version.py
            path_version_hook = Path(integration.__file__).with_name(
                "version_hook.py",
            )
            with path_version_hook.open(encoding="utf-8") as file:
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
                    "git_dir": None,
                }""",
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
                """,
            )

            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                setup.setup()

            # Validate setup.py got proper version
            self.assertEqual(fake_stdout.getvalue().strip(), "0.0.0+2.g93d84de")

            self.maxDiff = None
            with path_version.open(encoding="utf-8") as file:
                self.assertEqual(file.read(), target_ver)

            with path_init.open(encoding="utf-8") as file:
                self.assertEqual(file.read(), target_init)

            # Mock outside of a git repository

            def mock_fetch(
                *args,  # noqa: ARG001, ANN002
                **kwargs,  # noqa: ARG001, ANN003
            ) -> None:
                raise RuntimeError

            original_fetch = git.fetch
            try:
                git.fetch = mock_fetch

                # Succeeds since version.py exists
                with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                    setup.setup()
                self.assertEqual(fake_stdout.getvalue().strip(), "0.0.0+2.g93d84de")

                # Fails since version.py does not exist
                path_version.unlink()
                with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                    self.assertRaises(RuntimeError, setup.setup)
                self.assertEqual(fake_stdout.getvalue().strip(), "")
            finally:
                git.fetch = original_fetch

        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv

    def test_use_witch_ver_package3(self) -> None:
        path_package = self._DATA_ROOT.joinpath("package-3")
        path_test = self._TEST_ROOT.joinpath("package")
        shutil.copytree(path_package, path_test)

        setup = self.import_file(path_test.joinpath("setup.py"))

        # Change folder to package
        original_cwd = Path.cwd()
        original_argv = sys.argv
        try:
            os.chdir(path_test)
            sys.argv = ["setup.py", "--version"]

            path_version = path_test.joinpath("hello", "version.py")

            # Prepare the expected output for version.py
            # Already exists so load that file
            with path_version.open(encoding="utf-8") as file:
                target_ver = file.read()

            # Prepare the expected output for __init__.py
            # Already installed so no changes
            path_init = path_test.joinpath("hello", "__init__.py")
            with path_init.open(encoding="utf-8") as file:
                target_init = file.read()

            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                setup.setup()

            # Validate setup.py got proper version
            self.assertEqual(
                fake_stdout.getvalue().strip(),
                "0.0.0+4.29c921b55529e5a6ba963bcbcaf2f7e1d9f9efe6",
            )

            self.maxDiff = None
            with path_version.open(encoding="utf-8") as file:
                self.assertEqual(target_ver, file.read())

            with path_init.open(encoding="utf-8") as file:
                self.assertEqual(target_init, file.read())

        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv
