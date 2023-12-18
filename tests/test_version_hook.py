from __future__ import annotations

import io
import pathlib
import re
import textwrap
from pathlib import Path

import witch_ver
from tests import base
from witch_ver.version import version_dict


class TestVersionHook(base.TestBase):
    def test_get_version(self) -> None:
        path_orig = Path(witch_ver.__file__).with_name("version_hook.py").resolve()
        path_test = self._TEST_ROOT.joinpath("version_hook.py")

        with path_orig.open(encoding="utf-8") as file:
            orig_file = file.read()

        v = version_dict
        target_v = textwrap.dedent(
            f"""\
    version_dict = {{
        "tag": {"None"  if v["tag"]  is None else f'"{v["tag"]}"'},
        "tag_prefix": "{v["tag_prefix"]}",
        "sha": "{v["sha"]}",
        "sha_abbrev": "{v["sha_abbrev"]}",
        "branch": {"None"  if v["branch"]  is None else f'"{v["branch"]}"'},
        "date": "{v["date"]}",
        "dirty": {v["dirty"]},
        "distance": {v["distance"]},
        "pretty_str": "{v["pretty_str"]}",
        "git_dir": None,
    }}""",
        )
        target = re.sub(
            r"version_dict = {.*?}",
            target_v,
            orig_file,
            count=1,
            flags=re.S,
        )

        def check_file(*_, crlf: bool) -> None:
            """Check if contents match and line ending is proper.

            Args:
              crlf: True will expect CRLF line endings, False for LF
            """
            with path_test.open(encoding="utf-8") as file:
                buf = file.read()
                self.assertEqual(buf, target)

            with path_test.open("rb") as file:
                is_crlf = b"\r\n" in file.read()
                self.assertEqual(is_crlf, crlf)

        # Copy test file over
        with path_test.open("wb") as dst:
            dst.write(orig_file.encode())

        original_open = io.open

        calls = []

        def mock_open(fname: str, *args, **kwargs) -> object:  # noqa: ANN002, ANN003
            # subprocess calls io.open too, don't log those calls
            if isinstance(fname, int):
                return original_open(fname, *args, **kwargs)
            calls.append({"file": fname, "args": args, "kwargs": kwargs})
            # Retarget file operations to test file
            return original_open(fname, *args, **kwargs)

        try:
            io.open = mock_open

            # For 3.10 pathlib used an accessor model, mock that too
            if self.is_py_3_10:
                pathlib._normal_accessor.open = mock_open  # type: ignore[attr-defined] # noqa: SLF001

            # Upon import, it will write to path_test
            calls.clear()
            version_hook = self.import_file(path_test)
            self.assertEqual(version_hook.version_dict, v)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0]["args"][0], "rb")
            self.assertEqual(calls[1]["args"][0], "wb")
            check_file(crlf=False)

            # Cached, results, no file operations
            calls.clear()
            result = version_hook._get_version()  # noqa: SLF001
            self.assertEqual(result, v)
            self.assertEqual(len(calls), 0)
            check_file(crlf=False)

            # No changes needed
            calls.clear()
            version_hook = self.import_file(path_test)
            self.assertEqual(version_hook.version_dict, v)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["args"][0], "rb")
            check_file(crlf=False)

            # CRLF file
            with path_test.open("wb") as file:
                file.write(orig_file.encode().replace(b"\n", b"\r\n"))
            calls.clear()
            version_hook = self.import_file(path_test)
            self.assertEqual(version_hook.version_dict, v)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0]["args"][0], "rb")
            self.assertEqual(calls[1]["args"][0], "wb")
            check_file(crlf=True)

            original_fetch = witch_ver.fetch

            # Mock not in a git repository
            def mock_fetch_catch(
                *args,  # noqa: ARG001, ANN002
                **kwargs,  # noqa: ARG001, ANN003
            ) -> None:
                raise RuntimeError

            calls.clear()
            try:
                witch_ver.fetch = mock_fetch_catch

                version_hook = self.import_file(path_test)
                result = version_hook.version_dict
                self.assertEqual(result, v)
                self.assertEqual(len(calls), 0)
            finally:
                witch_ver.fetch = original_fetch
        finally:
            io.open = original_open
            if self.is_py_3_10:
                pathlib._normal_accessor.open = original_open  # type: ignore[attr-defined] # noqa: SLF001
