from __future__ import annotations

import io
import pathlib
from unittest import mock

from tests import base
from witch_ver import version
from witch_ver.version import version_dict


class TestVersion(base.TestBase):
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

            # For 3.10 pathlib used an accessor model, mock that too
            if self.is_py_3_10:
                pathlib._normal_accessor.open = mock_open  # type: ignore[attr-defined] # noqa: SLF001

            # File does not exist yet
            calls.clear()
            version._write_matching_newline(path, contents)  # noqa: SLF001
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["args"][0], "wb")
            check_file(crlf=False)

            # File does exist, no modifications to take place
            calls.clear()
            version._write_matching_newline(path, contents)  # noqa: SLF001
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["args"][0], "rb")
            check_file(crlf=False)

            with path.open("wb") as file:
                contents_b = contents.encode().replace(b"\n", b"\r\n")
                file.write(contents_b)

            # File does exist as CRLF, no modifications to take place
            calls.clear()
            version._write_matching_newline(path, contents)  # noqa: SLF001
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["args"][0], "rb")
            check_file(crlf=True)

            # Modify contents
            contents += self.random_string()

            # File does exist as CRLF
            calls.clear()
            version._write_matching_newline(path, contents)  # noqa: SLF001
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0]["args"][0], "rb")
            self.assertEqual(calls[1]["args"][0], "wb")
            check_file(crlf=True)
        finally:
            io.open = original_open
            if self.is_py_3_10:
                pathlib._normal_accessor.open = original_open  # type: ignore[attr-defined] # noqa: SLF001

    def test_get_version(self) -> None:
        path_version = self._TEST_ROOT.joinpath("version.py")

        target_v = version_dict

        original_file = version.__file__
        try:
            version.__file__ = str(path_version)

            # Clear Cache
            version._semver = {}  # noqa: SLF001

            result = version._get_version()  # noqa: SLF001
            self.assertNotEqual(None, version._semver)  # noqa: SLF001
            self.assertDictEqual(target_v, version.version_dict)
            self.assertDictEqual(target_v, result)

            # _semver is cached so shouldn't raise ValueError
            def mock_fetch_no_catch(
                *args,  # noqa: ARG001, ANN002
                **kwargs,  # noqa: ARG001, ANN003
            ) -> None:
                raise ValueError

            with mock.patch("witch_ver.git.fetch", mock_fetch_no_catch):
                result = version._get_version()  # noqa: SLF001
            self.assertDictEqual(target_v, result)

            # Clear Cache
            version._semver = {}  # noqa: SLF001

            # Mock not in a git repository
            def mock_fetch_catch(
                *args,  # noqa: ARG001, ANN002
                **kwargs,  # noqa: ARG001, ANN003
            ) -> None:
                raise RuntimeError

            with mock.patch("witch_ver.git.fetch", mock_fetch_catch):
                result = version._get_version()  # noqa: SLF001
            self.assertDictEqual(target_v, result)

        finally:
            version.__file__ = original_file
