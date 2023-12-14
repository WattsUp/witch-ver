"""Command runner."""
from __future__ import annotations

import subprocess
import typing as t
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os


def run(
    cmd: str,
    args: t.List[str],
    cwd: t.Union[str, bytes, os.PathLike, None] = None,
) -> t.Tuple[str, int]:
    """Run a command and capture its output and return code.

    Args:
      cmd: Command to run
      args: Arguments to add to command
      cwd: Current working directory to run the command from

    Returns:
      stdout, return code
    """
    cmd_l = [cmd, *args]
    try:
        result = subprocess.run(
            cmd_l,  # noqa: S603
            capture_output=True,
            cwd=cwd,
            check=False,
        )
    except OSError:
        cmd_str = " ".join(cmd_l)
        return f"Failed to run '{cmd_str}'", -1
    return result.stdout.strip().decode(), result.returncode
