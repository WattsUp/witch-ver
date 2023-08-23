"""Test module version_hook
"""

import pathlib
import re
import textwrap
from unittest import mock

import witch_ver

from tests import base


class TestVersionHook(base.TestBase):
  """Test version_hook
  """

  def test_get_version(self):
    path_orig = pathlib.Path(
        witch_ver.__file__).with_name("version_hook.py").resolve()
    path_test = self._TEST_ROOT.joinpath("version_hook.py")

    with open(path_orig, "r", encoding="utf-8") as file:
      orig_file = file.read()

    v = witch_ver.version_dict
    target_v = textwrap.dedent(f"""\
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
        "git_dir": None
    }}""")
    target = re.sub(r"version_dict = {.*?}",
                    target_v,
                    orig_file,
                    count=1,
                    flags=re.S)

    def check_file(crlf: bool) -> None:
      """Check if contents match and line ending is proper

      Args:
        crlf: True will expect CRLF line endings, False for LF
      """
      with open(path_test, "r", encoding="utf-8") as file:
        buf = file.read()
        self.assertEqual(target, buf)

      with open(path_test, "rb") as file:
        is_crlf = b"\r\n" in file.read()
        self.assertEqual(crlf, is_crlf)

    # Copy test file over
    with open(path_test, "wb") as dst:
      dst.write(orig_file.encode())

    original_open = open

    calls = []

    def mock_open(fname: str, *args, **kwargs) -> object:
      calls.append({"file": fname, "args": args, "kwargs": kwargs})
      # Retarget file operations to test file
      return original_open(path_test, *args, **kwargs)

    # Upon import, it will write to path_test
    calls.clear()
    with mock.patch("builtins.open", mock_open):
      from witch_ver import version_hook  # pylint: disable=import-outside-toplevel
    check_file(False)
    self.assertEqual(2, len(calls))
    self.assertEqual("rb", calls[0]["args"][0])
    self.assertEqual("wb", calls[1]["args"][0])

    # Cached, results, no file operations
    calls.clear()
    with mock.patch("builtins.open", mock_open):
      result = version_hook._get_version()  # pylint: disable=protected-access
      self.assertEqual(v, result)
    check_file(False)
    self.assertEqual(0, len(calls))

    # No changes needed
    calls.clear()
    version_hook._semver = None  # pylint: disable=protected-access
    with mock.patch("builtins.open", mock_open):
      result = version_hook._get_version()  # pylint: disable=protected-access
      self.assertEqual(v, result)
    check_file(False)
    self.assertEqual(1, len(calls))
    self.assertEqual("rb", calls[0]["args"][0])

    # CRLF file
    version_hook._semver = None  # pylint: disable=protected-access
    with open(path_test, "wb") as file:
      file.write(orig_file.encode().replace(b"\n", b"\r\n"))
    calls.clear()
    with mock.patch("builtins.open", mock_open):
      result = version_hook._get_version()  # pylint: disable=protected-access
      self.assertEqual(v, result)
    check_file(True)
    self.assertEqual(2, len(calls))
    self.assertEqual("rb", calls[0]["args"][0])
    self.assertEqual("wb", calls[1]["args"][0])

    # Clear Cache
    version_hook._semver = None  # pylint: disable=protected-access

    # Mock not in a git repository
    def mock_fetch_catch(*args, **kwargs):
      raise RuntimeError

    calls.clear()
    with mock.patch("builtins.open", mock_open):
      with mock.patch("witch_ver.fetch", mock_fetch_catch):
        result = version_hook._get_version()  # pylint: disable=protected-access
        self.assertEqual(v, result)
    self.assertEqual(0, len(calls))
