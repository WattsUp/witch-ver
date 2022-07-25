"""Test module version
"""

from __future__ import annotations
import pathlib
from unittest import mock

import witch_ver
from witch_ver import version

from tests import base


class TestVersion(base.TestBase):
  """Test version
  """

  def test_get_version(self):
    v = witch_ver.version_dict

    # Setup mock IO for the file
    path = pathlib.Path(witch_ver.__file__).with_name("_version.py")
    with open(path, "r", encoding="utf-8") as file:
      target_file = file.read()

    # Mock an overwrite
    mock_open: mock.MagicMock = mock.mock_open(read_data="")
    with mock.patch("builtins.open", mock_open):
      version._semver = None  # pylint: disable=protected-access
      result = version._get_version()  # pylint: disable=protected-access
      self.assertNotEqual(None, version._semver)  # pylint: disable=protected-access
      self.assertDictEqual(v, version.version_dict)

      handle_r: mock.MagicMock = mock_open().read
      handle_r.assert_called_once()

      handle_w: mock.MagicMock = mock_open().write
      handle_w.assert_called_once_with(target_file)

      # Call again but shouldn't run again since _semver is not None
      result = version._get_version()  # pylint: disable=protected-access
      handle_r.assert_called_once()
      handle_w.assert_called_once()

    # Mock no changes needed
    mock_open: mock.MagicMock = mock.mock_open(read_data=target_file)
    with mock.patch("builtins.open", mock_open):
      version._semver = None  # pylint: disable=protected-access
      result = version._get_version()  # pylint: disable=protected-access
      self.assertDictEqual(v, result)

      handle_r: mock.MagicMock = mock_open().read
      handle_r.assert_called_once()

      handle_w: mock.MagicMock = mock_open().write
      handle_w.assert_not_called()

    # Mock not in a git repository
    mock_open: mock.MagicMock = mock.mock_open(read_data=target_file)
    with mock.patch("builtins.open", mock_open):
      version._semver = None  # pylint: disable=protected-access

      def mock_fetch(*args, **kwargs):
        raise RuntimeError

      with mock.patch("witch_ver.git.fetch", mock_fetch):
        result = version._get_version()  # pylint: disable=protected-access

      handle_r: mock.MagicMock = mock_open().read
      handle_r.assert_not_called()

      handle_w: mock.MagicMock = mock_open().write
      handle_w.assert_not_called()

    # Mock non-existent file
    mock_open: mock.MagicMock = mock.mock_open(read_data=target_file)
    with mock.patch("builtins.open", mock_open):
      version._semver = None  # pylint: disable=protected-access

      class MockWindowsPath(pathlib.WindowsPath):

        def exists(self) -> bool:
          return False

      class MockPosixPath(pathlib.PosixPath):

        def exists(self) -> bool:
          return False

      with mock.patch("pathlib.WindowsPath", MockWindowsPath):
        with mock.patch("pathlib.PosixPath", MockPosixPath):
          result = version._get_version()  # pylint: disable=protected-access

      handle_r: mock.MagicMock = mock_open().read
      handle_r.assert_not_called()

      handle_w: mock.MagicMock = mock_open().write
      handle_w.assert_called_once_with(target_file)
