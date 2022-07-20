"""Test module runner
"""

import io
import os
import subprocess
from typing import List, Union
from unittest import mock

from witch_ver import runner

from tests import base


class TestRunner(base.TestBase):
  """Test runner module
  """

  def test_run(self):
    bad_cmd = "_"

    class MockData:
      cmd_called: List[str] = None
      cwd_called: Union[str, bytes, os.PathLike] = None
      stdout_out: str = None
      returncode_out: int = None

    m = MockData()

    def mock_run(cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
      m.cmd_called = cmd
      m.cwd_called = kwargs.get("cwd", None)

      self.assertIsInstance(cmd, list)
      if cmd[0] == bad_cmd:
        raise OSError
      for c in cmd:
        self.assertIsInstance(c, str)

      return subprocess.CompletedProcess(cmd, m.returncode_out,
                                         m.stdout_out.encode(), b"")

    original_run = runner.subprocess.run
    try:
      runner.subprocess.run = mock_run

      cmd = "echo"
      args = ["hello"]
      m.stdout_out = "hi"
      m.returncode_out = 0

      stdout, returncode = runner.run(cmd, args)
      self.assertEqual(m.stdout_out, stdout)
      self.assertEqual(m.returncode_out, returncode)
      self.assertEqual(None, m.cwd_called)
      self.assertListEqual([cmd] + args, m.cmd_called)

      cmd = bad_cmd
      args = ["hello"]
      m.stdout_out = "hi"
      m.returncode_out = 0

      with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
        stdout, returncode = runner.run(cmd, args, cwd=self._TEST_ROOT)
      self.assertEqual(None, stdout)
      self.assertEqual(None, returncode)
      self.assertEqual(self._TEST_ROOT, m.cwd_called)
      self.assertListEqual([cmd] + args, m.cmd_called)
      self.assertEqual(f"Failed to run '{bad_cmd} {' '.join(args)}'\n",
                       fake_stdout.getvalue())

    finally:
      runner.subprocess.run = original_run
