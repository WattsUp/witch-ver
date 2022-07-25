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
    v = witch_ver.version_dict

    # Setup mock IO for the file
    path = pathlib.Path(witch_ver.__file__).with_name("version_hook.py")
    with open(path, "r", encoding="utf-8") as file:
      orig_file = file.read()

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
    target_file = re.sub(r"version_dict = {.*?}",
                         target_v,
                         orig_file,
                         count=1,
                         flags=re.S)

    # Mock an overwrite
    mock_open: mock.MagicMock = mock.mock_open(read_data=orig_file)
    with mock.patch("builtins.open", mock_open):
      from witch_ver import version_hook  # pylint: disable=import-outside-toplevel
      self.assertNotEqual(None, version_hook._semver)  # pylint: disable=protected-access
      self.assertDictEqual(v, version_hook.version_dict)

      handle_r: mock.MagicMock = mock_open().read
      handle_r.assert_called_once()

      handle_w: mock.MagicMock = mock_open().write
      handle_w.assert_called_once_with(target_file)

      # Call again but shouldn't run again since _semver is not None
      result = version_hook._get_version()  # pylint: disable=protected-access
      handle_r.assert_called_once()
      handle_w.assert_called_once()

    # Mock no changes needed
    mock_open: mock.MagicMock = mock.mock_open(read_data=target_file)
    with mock.patch("builtins.open", mock_open):
      version_hook._semver = None  # pylint: disable=protected-access
      result = version_hook._get_version()  # pylint: disable=protected-access
      self.assertDictEqual(v, result)

      handle_r: mock.MagicMock = mock_open().read
      handle_r.assert_called_once()

      handle_w: mock.MagicMock = mock_open().write
      handle_w.assert_not_called()

    # Mock not in a git repository
    mock_open: mock.MagicMock = mock.mock_open(read_data=target_file)
    with mock.patch("builtins.open", mock_open):
      version_hook._semver = None  # pylint: disable=protected-access

      def mock_fetch(*args, **kwargs):
        raise RuntimeError

      with mock.patch("witch_ver.git.fetch", mock_fetch):
        result = version_hook._get_version()  # pylint: disable=protected-access

      handle_r: mock.MagicMock = mock_open().read
      handle_r.assert_not_called()

      handle_w: mock.MagicMock = mock_open().write
      handle_w.assert_not_called()
