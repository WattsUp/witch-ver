from __future__ import annotations

import subprocess
import typing as t
from typing import TYPE_CHECKING

from tests import base
from witch_ver import runner

if TYPE_CHECKING:
    import os


class TestRunner(base.TestBase):
    def test_run(self) -> None:
        bad_cmd = "_"

        class MockData:
            cmd_called: t.Union[t.List[str], None] = None
            cwd_called: t.Union[str, bytes, os.PathLike, None] = None
            stdout_out: str = ""
            returncode_out: int = 0

        m = MockData()

        def mock_run(
            cmd: t.List[str],
            cwd: t.Union[str, bytes, os.PathLike, None] = None,
            **_,
        ) -> subprocess.CompletedProcess:
            m.cmd_called = cmd
            m.cwd_called = cwd

            self.assertIsInstance(cmd, list)
            if cmd[0] == bad_cmd:
                raise OSError
            for c in cmd:
                self.assertIsInstance(c, str)

            return subprocess.CompletedProcess(
                cmd,
                m.returncode_out,
                m.stdout_out.encode(),
                b"",
            )

        original_run = runner.subprocess.run
        try:
            runner.subprocess.run = mock_run

            cmd = "echo"
            args = ["hello"]
            m.stdout_out = "hi"
            m.returncode_out = 0

            stdout, returncode = runner.run(cmd, args)
            self.assertEqual(stdout, m.stdout_out)
            self.assertEqual(returncode, m.returncode_out)
            self.assertIsNone(m.cwd_called)
            self.assertEqual(m.cmd_called, [cmd, *args])

            cmd = bad_cmd
            args = ["hello"]
            m.stdout_out = "hi"
            m.returncode_out = 0

            stdout, returncode = runner.run(cmd, args, cwd=self._TEST_ROOT)

            self.assertEqual(stdout, f"Failed to run '{bad_cmd} {' '.join(args)}'")
            self.assertNotEqual(returncode, 0)
            self.assertEqual(m.cwd_called, self._TEST_ROOT)
            self.assertEqual(m.cmd_called, [cmd, *args])

        finally:
            runner.subprocess.run = original_run
