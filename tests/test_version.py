"""Test module version
"""

from __future__ import annotations
from unittest import mock

import witch_ver
from witch_ver import version

from tests import base


class TestVersion(base.TestBase):
  """Test version
  """

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
      version._write_matching_newline(path, contents)  # pylint: disable=protected-access
    check_file(False)
    self.assertEqual(1, len(calls))
    self.assertEqual("wb", calls[0]["args"][0])

    # File does exist, no modifications to take place
    calls.clear()
    with mock.patch("builtins.open", mock_open):
      version._write_matching_newline(path, contents)  # pylint: disable=protected-access
    check_file(False)
    self.assertEqual(1, len(calls))
    self.assertEqual("rb", calls[0]["args"][0])

    with open(path, "wb") as file:
      contents_b = contents.encode().replace(b"\n", b"\r\n")
      file.write(contents_b)

    # File does exist as CRLF, no modifications to take place
    calls.clear()
    with mock.patch("builtins.open", mock_open):
      version._write_matching_newline(path, contents)  # pylint: disable=protected-access
    check_file(True)
    self.assertEqual(1, len(calls))
    self.assertEqual("rb", calls[0]["args"][0])

    # Modify contents
    contents += self.random_string()

    # File does exist as CRLF
    calls.clear()
    with mock.patch("builtins.open", mock_open):
      version._write_matching_newline(path, contents)  # pylint: disable=protected-access
    check_file(True)
    self.assertEqual(2, len(calls))
    self.assertEqual("rb", calls[0]["args"][0])
    self.assertEqual("wb", calls[1]["args"][0])

  def test_get_version(self):
    path_version = self._TEST_ROOT.joinpath("version.py")

    target_v = witch_ver.version_dict

    original_file = version.__file__
    try:
      version.__file__ = str(path_version)

      # Clear Cache
      version._semver = None  # pylint: disable=protected-access

      result = version._get_version()  # pylint: disable=protected-access
      self.assertNotEqual(None, version._semver)  # pylint: disable=protected-access
      self.assertDictEqual(target_v, version.version_dict)
      self.assertDictEqual(target_v, result)

      # _semver is cached so shouldn't raise ValueError
      def mock_fetch_no_catch(*args, **kwargs):
        raise ValueError

      with mock.patch("witch_ver.git.fetch", mock_fetch_no_catch):
        result = version._get_version()  # pylint: disable=protected-access
      self.assertDictEqual(target_v, result)

      # Clear Cache
      version._semver = None  # pylint: disable=protected-access

      # Mock not in a git repository
      def mock_fetch_catch(*args, **kwargs):
        raise RuntimeError

      with mock.patch("witch_ver.git.fetch", mock_fetch_catch):
        result = version._get_version()  # pylint: disable=protected-access
      self.assertDictEqual(target_v, result)

    finally:
      version.__file__ = original_file
